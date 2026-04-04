from src import data_collection, data_extraction, data_normalisation, json_to_rdf

def main():
    data_collection()
    data_extraction()
    data_normalisation()
    output = json_to_rdf()
    return output

if __name__ == "__main__":
    main()