import argparse
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

DEFAULT_OUTPUT_PATH = Path("output/performance_benchmark.json")
DEFAULT_COMMAND = [sys.executable, "-m", "src.main", "--from-cache"]


class BenchmarkError(RuntimeError):
    pass


def _utc_timestamp():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _load_json_if_exists(path):
    file_path = Path(path)
    if not file_path.exists():
        return None
    return json.loads(file_path.read_text(encoding="utf-8"))


def _extract_output_summary():
    query_results = _load_json_if_exists("output/query_results.json") or []
    validation = _load_json_if_exists("output/validation_results.json") or {}
    kg_summary = _load_json_if_exists("output/kg_summary.json") or {}

    query_count = len(query_results)
    answered_queries = sum(1 for item in query_results if item.get("row_count", 0) > 0)

    graph_summary = kg_summary.get("graph", {})
    extraction_summary = kg_summary.get("extraction", {})

    return {
        "query_coverage": {
            "answered_queries": answered_queries,
            "total_queries": query_count,
        },
        "validation": {
            "rule_count": validation.get("rule_count"),
            "failed_rule_count": validation.get("failed_rule_count"),
            "total_violations": validation.get("total_violations"),
        },
        "graph": {
            "triple_count": graph_summary.get("triple_count"),
            "policy_event_count": graph_summary.get("policy_event_count"),
            "events_with_government_body_count": graph_summary.get(
                "events_with_government_body_count"
            ),
        },
        "extraction": {
            "record_count": extraction_summary.get("record_count"),
            "event_count": extraction_summary.get("event_count"),
            "extraction_method_counts": extraction_summary.get("extraction_method_counts"),
        },
    }


def _windows_peak_memory_bytes(pid):
    import ctypes
    from ctypes import Structure, byref, c_size_t, sizeof, wintypes

    PROCESS_QUERY_INFORMATION = 0x0400
    PROCESS_VM_READ = 0x0010

    class PROCESS_MEMORY_COUNTERS(Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("PageFaultCount", wintypes.DWORD),
            ("PeakWorkingSetSize", c_size_t),
            ("WorkingSetSize", c_size_t),
            ("QuotaPeakPagedPoolUsage", c_size_t),
            ("QuotaPagedPoolUsage", c_size_t),
            ("QuotaPeakNonPagedPoolUsage", c_size_t),
            ("QuotaNonPagedPoolUsage", c_size_t),
            ("PagefileUsage", c_size_t),
            ("PeakPagefileUsage", c_size_t),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)

    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    psapi.GetProcessMemoryInfo.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(PROCESS_MEMORY_COUNTERS),
        wintypes.DWORD,
    ]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL

    handle = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    if not handle:
        return None

    try:
        counters = PROCESS_MEMORY_COUNTERS()
        counters.cb = sizeof(PROCESS_MEMORY_COUNTERS)
        if not psapi.GetProcessMemoryInfo(handle, byref(counters), counters.cb):
            return None
        return int(counters.PeakWorkingSetSize)
    finally:
        kernel32.CloseHandle(handle)


def _linux_rss_bytes(pid):
    try:
        status = Path(f"/proc/{pid}/status").read_text()
    except OSError:
        return None
    for line in status.splitlines():
        if line.startswith("VmRSS:"):
            kb = int(line.split()[1])
            return kb * 1024
    return None


def _peak_memory_bytes(pid):
    if os.name == "nt":
        return _windows_peak_memory_bytes(pid)
    return _linux_rss_bytes(pid)


def run_benchmark(command):
    started_at = _utc_timestamp()
    started_monotonic = time.perf_counter()

    process = subprocess.Popen(command)

    peak_memory_bytes = None
    while process.poll() is None:
        observed = _peak_memory_bytes(process.pid)
        if observed is not None:
            peak_memory_bytes = max(peak_memory_bytes or 0, observed)
        time.sleep(0.5)

    elapsed_seconds = round(time.perf_counter() - started_monotonic, 2)
    ended_at = _utc_timestamp()

    final_peak = _peak_memory_bytes(process.pid)
    if final_peak is not None:
        peak_memory_bytes = max(peak_memory_bytes or 0, final_peak)

    if process.returncode is None:
        raise BenchmarkError("Benchmark process ended without an exit code.")

    report = {
        "measured_at": ended_at,
        "command": command,
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "python": sys.version.split()[0],
        },
        "run": {
            "started_at": started_at,
            "ended_at": ended_at,
            "elapsed_seconds": elapsed_seconds,
            "exit_code": process.returncode,
            "peak_working_set_bytes": peak_memory_bytes,
            "peak_working_set_mb": round((peak_memory_bytes or 0) / (1024 * 1024), 2)
            if peak_memory_bytes is not None
            else None,
        },
        "outputs": _extract_output_summary(),
    }
    if report["outputs"]["extraction"]["record_count"] and elapsed_seconds > 0:
        report["run"]["records_per_second"] = round(
            report["outputs"]["extraction"]["record_count"] / elapsed_seconds, 2
        )
    else:
        report["run"]["records_per_second"] = None
    return report


def save_report(report, output_path):
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def build_arg_parser():
    parser = argparse.ArgumentParser(
        description="Benchmark the KG pipeline and save runtime / memory summary."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Where to save the benchmark JSON report.",
    )
    parser.add_argument(
        "--command",
        nargs="+",
        default=DEFAULT_COMMAND,
        help="Command to execute for the benchmark.",
    )
    return parser


def main():
    args = build_arg_parser().parse_args()
    report = run_benchmark(args.command)
    output_path = save_report(report, args.output)
    print(
        f"[BENCHMARK] Saved report to {output_path} "
        f"(elapsed {report['run']['elapsed_seconds']}s, "
        f"peak working set {report['run']['peak_working_set_mb']} MB)"
    )


if __name__ == "__main__":
    main()
