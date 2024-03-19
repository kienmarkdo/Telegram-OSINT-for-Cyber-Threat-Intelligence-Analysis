from credentials import es_username, es_password, es_ca_cert_path
from elasticsearch import Elasticsearch, helpers
import json
import logging

# https://www.elastic.co/guide/en/elasticsearch/client/python-api/current/connecting.html
es = Elasticsearch(
    "https://localhost:9200",
    basic_auth=(es_username, es_password),
    ca_certs=es_ca_cert_path,
)  # Update with your credentials

# print(es.info())  # https://www.elastic.co/guide/en/elasticsearch/client/python-api/current/connecting.html


def index_json_file_to_es(file_path: str, index_name: str) -> bool:
    """
    Index a JSON file to Elasticsearch.

    Allows the creation of a Data View on Elasticsearch for data visualization and analysis.
    Navigate to Elasticsearch on your browser -> Left Panel -> Analytics -> Discover to
    create the Data View. From there, Elasticsearch and Kibana can be used to visualize,
    analyze, filter, or produce reports out of the data.

    Args:
        file_path: path to the JSON response file returned by Telegram API
        index_name: descriptive name for the index (i.e.: messages_index)

    Returns:
        True if the JSON file was successfully indexed into Elasticsearch
    """
    if None in [es_username, es_password, es_ca_cert_path]:
        logging.warning(
            f"Cannot index JSON file to Elasticsearch due to missing configurations"
        )
        logging.warning(
            f"Elasticsearch username, password, and CA certificate path have not been configured in credentials.py"
        )
        logging.warning(f"Do nothing")
        return False

    with open(file_path, "r") as file:
        documents = json.load(file)
        actions = [
            {
                "_index": index_name,
                "_source": document,
            }
            for document in documents
        ]
        # https://stackoverflow.com/questions/59555640/how-to-bulk-insert-in-elasticsearch-ignoring-all-errors-that-may-occur-in-the-pr
        # https://elasticsearch-py.readthedocs.io/en/latest/helpers.html
        helpers.bulk(es, actions, raise_on_error=False)
        # raise_on_error argument ignores the BulkIndexError exception
        # raise BulkIndexError(f"{len(errors)} document(s) failed to index.", errors) elasticsearch.helpers.BulkIndexError: 1 document(s) failed to index.

    return True


# def transform_to_ndjson(json_file_path: str, entity: Channel | Chat | User):
#     """
#     Transforms a JSON formatted Telegram API response into a newline-delimited JSON
#     so that the data can be imported into Elasticsearch for data analysis.

#     Takes the path to a list JSON file as input and outputs a ndjson file
#     into an output folder.

#     Example input:
#     ```
#     [
#         {
#             "key1": values
#         },
#         {
#             "key1": values
#         }
#     ]
#     ```
#     Example output:
#     ```
#     {"key1": values}
#     {"key2": values}
#     ```


#     Args:
#         json_file_path: path to your JSON file

#     Returns:
#         True if the transformation and file output completed successfully
#     """
#     if json_file_path is None:
#         return False

#     ndjson_file_path = f"{OUTPUT_NDJSON}/{get_entity_type_name(entity)}_{entity.id}/{COLLECTION_NAME}_{entity.id}.json"

#     # Read the JSON data from the file
#     with open(json_file_path, "r") as file:
#         json_objects = json.load(file)

#     # Convert each JSON object into a newline-delimited string
#     ndjson_content = "\n".join(json.dumps(obj) for obj in json_objects)

#     # Check if directory exists, create it if necessary
#     os.makedirs(os.path.dirname(ndjson_file_path), exist_ok=True)

#     # Write the NDJSON content to the output file
#     with open(ndjson_file_path, "w") as ndjson_file:
#         ndjson_file.write(ndjson_content)

#     logging.info(f"Converted NDJSON saved to {ndjson_file_path}")


if __name__ == "__main__":

    index_json_file(
        f"output/2024-03-18T04-21-06Z/public_group_2016527483/messages_2016527483.json",
        "messages_index",
    )

    index_json_file(
        f"output/2024-03-10T01-02-56Z/public_group_1012147388/messages_1012147388.json",
        "messages_index",
    )
