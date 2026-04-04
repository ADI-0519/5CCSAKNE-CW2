# =====local imports=====
from src.data_collection import load_data_from_url
from src.data_extraction import extract_relevant_information
from src.data_normalisation import normalise_data
from src.json_to_rdf import convert_json_to_rdf
from src.config import CONFIG


today = CONFIG["today"]


def save_rdf_to_file(rdf_graph, filename):
    print(f"Saving RDF graph to {filename}...")
    # TODO: save the RDF graph to a file in the desired format (e.g., Turtle, RDF/XML)
    pass


def main():
    raw_data = load_data_from_url(CONFIG["url_headlines"])
    print(raw_data)
    extracted_data = extract_relevant_information(raw_data)
    normalised_data = normalise_data(extracted_data)
    rdf_graph = convert_json_to_rdf(normalised_data)
    save_rdf_to_file(rdf_graph, "output.rdf")


if __name__ == "__main__":
    main()