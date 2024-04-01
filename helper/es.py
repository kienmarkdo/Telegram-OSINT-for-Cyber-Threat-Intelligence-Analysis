import hashlib
import json
import logging

from elasticsearch import Elasticsearch, helpers
from telethon.types import *

from configs import es_ca_cert_path, es_password, es_username
from helper.logger import OUTPUT_DIR, OUTPUT_NDJSON

# https://www.elastic.co/guide/en/elasticsearch/client/python-api/current/connecting.html
es = Elasticsearch(
    "https://localhost:9200",
    basic_auth=(es_username, es_password),
    ca_certs=es_ca_cert_path,
)  # Update with your credentials

# print(es.info())  # https://www.elastic.co/guide/en/elasticsearch/client/python-api/current/connecting.html


def get_index_mapping(index_name: str) -> dict:
    """
    Generates a dictionary index mapping for the specified index.

    Example usage:
    ```python
    index_name='new_index'
    body = {
                "mappings": {...}  # define mappings here
            }
    es.indices.create(index_name, body)
    # Based on https://discuss.elastic.co/t/specify-mappings-while-creating-index-using-python-client/292433
    ```

    Supported indicies
        - messages_index
        - iocs_index
        - users_index
        - entities_index

    Args:
        index_name: descriptive name for the index (i.e.: messages_index)

    Returns:
        The dictionary index mapping for the specified index.
    """
    index_mapping: dict = {}
    if index_name == "messages_index":
        index_mapping = {
            "mappings": {
                "properties": {
                    "_": {
                        "type": "text",
                    },
                }
            }
        }
    elif index_name == "iocs_index":
        index_mapping = {"mappings": {"properties": {}}}
    elif index_name == "users_index":
        index_mapping = {
            "mappings": {
                "properties": {
                    "_": {
                        "type": "text",
                    },
                }
            }
        }
    elif index_name == "entities_index":
        index_mapping = {
            "mappings": {
                "properties": {
                    "_": {
                        "type": "text",
                    },
                }
            }
        }
    else:
        raise Exception(f"Unsupported index name `{index_name}`")

    return index_mapping


def get_record_id(index_name: str, collected_obj: dict) -> str | None:
    """
    Generates a record ID for the current object.

    A record ID is a string ID of the record to be inserted in the document's `_id` metadata field
    https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping-id-field.html

    Args:
        index_name: descriptive name for the index (i.e.: messages_index)
        collected_obj: one collected object (e.g.: one Message, one Participant...)

    Returns:
        A record ID for the current object.
    """
    # Create a record ID attribute for the current object (message, user...) to store in Elasticsearch
    record_id: str = ""
    if index_name == "messages_index":
        message_id: int = collected_obj.get("id")
        entity_id: int = (
            collected_obj.get("peer_id", {}).get("channel_id")
            or collected_obj.get("peer_id", {}).get("chat_id")
            or collected_obj.get("peer_id", {}).get("user_id")
        )  # Channel (channel or public group), Chat (private group), User (direct message)
        record_id = f"{message_id}_{entity_id}"
    elif index_name == "iocs_index":
        # -- Generate a deterministic hash for this IOC object's ID

        # Convert the object to a JSON string and encode it to bytes
        data_string = json.dumps(collected_obj, sort_keys=True).encode()

        # Use SHA-256 hash function to generate a hash of the data
        hash_object = hashlib.sha256(data_string)

        # Return the hexadecimal representation of the digest
        record_id = hash_object.hexdigest()
    elif index_name == "users_index":
        record_id = f"{collected_obj['id']}"
    elif index_name == "entities_index":
        record_id = f"{collected_obj['id']}"
    else:
        raise Exception(f"Unsupported index name `{index_name}`")

    return record_id


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
            f"Elasticsearch username, password, and CA certificate path have not been configured in configs.py"
        )
        logging.warning(f"Do nothing")
        return False

    # Create index with the provided index mapping, if this is a new index
    # index mapping / explicit mapping as defined by Elasticsearch https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping.html
    if not es.indices.exists(index=index_name):
        index_mapping: dict = get_index_mapping(index_name)
        es.indices.create(index=index_name, body=index_mapping)

    with open(file_path, "r") as file:
        documents: list[dict] = json.load(file)
        actions = [
            {
                "_index": index_name,
                "_id": get_record_id(
                    index_name, document
                ),  # Prevents duplicate records from being inserted into the document
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


def transform_to_ndjson(json_file_path: str):
    """
    Transforms a JSON formatted Telegram API response into a newline-delimited JSON
    so that the data can be imported into Elasticsearch for data analysis.

    Takes the path to a list JSON file as input and outputs a ndjson file
    into an output folder.

    Example input:
    ```
    [
        {
            "key1": values
        },
        {
            "key1": values
        }
    ]
    ```
    Example output:
    ```
    {"key1": values}
    {"key2": values}
    ```


    Args:
        json_file_path: path to your JSON file

    Returns:
        True if the transformation and file output completed successfully
    """
    if json_file_path is None:
        return False

    ndjson_file_path = json_file_path.replace(OUTPUT_DIR, OUTPUT_NDJSON)

    # Read the JSON data from the file
    with open(json_file_path, "r") as file:
        json_objects = json.load(file)

    # Convert each JSON object into a newline-delimited string
    ndjson_content = "\n".join(json.dumps(obj) for obj in json_objects)

    # Check if directory exists, create it if necessary
    os.makedirs(os.path.dirname(ndjson_file_path), exist_ok=True)

    # Write the NDJSON content to the output file
    with open(ndjson_file_path, "w") as ndjson_file:
        ndjson_file.write(ndjson_content)

    logging.info(f"Converted NDJSON saved to {ndjson_file_path}")


if __name__ == "__main__":

    index_json_file_to_es(
        f"output/2024-03-18T04-21-06Z/public_group_2016527483/messages_2016527483.json",
        "messages_index",
    )

    index_json_file_to_es(
        f"output/2024-03-10T01-02-56Z/public_group_1012147388/messages_1012147388.json",
        "messages_index",
    )
