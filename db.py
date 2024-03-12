"""
Interface with the local SQLite3 database.

This database is required for operational usage and allows collections to
work properly, such as tracking offset ID when extracting messages with
the Telegram API. This database does not store the actual collected data.
"""

import sqlite3

sqlite_db_name: str = "app.db"


def start_database():
    """
    Creates the database and tables for the application if they do not already exist.
    """
    try:
        # Create or connect to the SQLite3 database
        conn = sqlite3.connect(sqlite_db_name)

        # Create a cursor object to execute SQL commands
        cursor = conn.cursor()

        # Create required tables
        # To track messages collection details/metadata, such as offset ID or elapsed time
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS Messages_collection (
                id INTEGER PRIMARY KEY,
                entity_id INTEGER,
                start_offset_id INTEGER, 
                last_offset_id INTEGER,
                collection_start_timestamp INTEGER,
                collection_end_timestamp INTEGER
            );
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS IOCs (
                id INTEGER PRIMARY KEY,
                message_id INTEGER,
                channel_id INTEGER,
                user_id INTEGER, 
                ioc_type TEXT,
                ioc_value TEXT,
                message TEXT,
                message_translated TEXT
            );
            """
        )
        # Fetch names of all tables to verify that all tables were created successfully
        table_names: list[str] = ["Messages_collection", "IOCs"]
        for table_name in table_names:
            res = cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';"
            )

            curr_row = res.fetchone()  # Get current row then move cursor to next row
            # print(curr_row)
            if curr_row is None:
                print(
                    f"Failed to create the following table in the database: {table_name}"
                )
                raise

        # Commit the transaction and close the connection
        conn.commit()
        conn.close()

    except sqlite3.DatabaseError as err:
        raise f"Database error: {err}"
    finally:
        conn.close()


def messages_collection_get_offset_id(entity_id: int):
    """
    Gets the latest offset id in the database with the latest offset id
    of the last message in the latest messages collection.

    Args:
        entity_id:
            id of the entity (i.e.: public group, private group, channel, user)
    """
    try:
        # Create or connect to the SQLite3 database
        conn = sqlite3.connect(sqlite_db_name)

        # Create a cursor object to execute SQL commands
        cursor = conn.cursor()

        # Get last row of a specified entity id (most recent messages collection of a particular entity)
        res = cursor.execute(
            f"""
            SELECT * FROM Messages_collection WHERE entity_id={entity_id} ORDER BY ID DESC LIMIT 1;
        """
        )
        returned_result: list[tuple] = res.fetchall()  # returns all resulting rows

        offset_id: int = 0
        entity_id: int = entity_id
        if offset_id is not None and len(returned_result) > 0:
            offset_id = returned_result[0][3]
        # print(f"Latest offset id of {entity_id} from database: {offset_id}")

        # Commit the transaction and close the connection
        conn.commit()
        conn.close()

        return offset_id

    except sqlite3.DatabaseError as err:
        raise f"Database error: {err}"
    finally:
        conn.close()


def messages_collection_insert_offset_id(
    entity_id: int,
    start_offset_id: int,
    last_offset_id: int,
    collection_start_timestamp: int,
    collection_end_timestamp: int,
):
    """
    Inserts the latest offset id in the database with the latest offset id
    of the last message in the latest messages collection.

    The next message collection would start at this latest offset id.

    Args:
        entity_id:
            id of the entity (i.e.: public group, private group, channel, user)
        start_offset_id:
            offset id of the first message collected in this collection
        last_offset_id:
            offset id of the latest message collected in this collection
        collection_start_timestamp:
            epoch timestamp of when the latest completed successful collection started (i.e.: 1707699810)
        collection_end_timestamp:
            epoch timestamp of when the latest completed successful collection ended
    """
    try:
        # Create or connect to the SQLite3 database
        conn = sqlite3.connect(sqlite_db_name)

        # Create a cursor object to execute SQL commands
        cursor = conn.cursor()

        # Define SQL query
        sql_query = """
        INSERT INTO Messages_collection (
            entity_id, start_offset_id, last_offset_id, collection_start_timestamp, collection_end_timestamp
        )
        VALUES (?, ?, ?, ?, ?)
        """

        # Insert into the table
        cursor.execute(
            sql_query,
            (
                entity_id,
                start_offset_id,
                last_offset_id,
                collection_start_timestamp,
                collection_end_timestamp,
            ),
        )

        # Commit the transaction and close the connection
        conn.commit()
    except sqlite3.DatabaseError as err:
        raise f"Database error: {err}"
    finally:
        conn.close()


def iocs_batch_insert(iocs: list[dict]):
    """
    Batch inserts IOCs into the database.

    Args:
        iocs: List of dictionaries, where each dictionary contains the IOC information.
    """
    try:
        if iocs is None or len(iocs) == 0:
            return

        conn = sqlite3.connect(sqlite_db_name)
        cursor = conn.cursor()

        sql_query = """
        INSERT INTO IOCs (message_id, channel_id, user_id, ioc_type, ioc_value, message, message_translated)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        # Prepare a list of tuples from the list of dictionaries for batch insertion
        iocs_values = [
            (
                ioc["message_id"],
                ioc["channel_id"],
                ioc["user_id"],
                ioc["ioc_type"],
                ioc["ioc_value"],
                ioc["original_message"],
                ioc["translated_message"],
            )
            for ioc in iocs
        ]

        cursor.executemany(sql_query, iocs_values)
        conn.commit()
    except sqlite3.DatabaseError as err:
        raise f"Database error: {err}"
    finally:
        conn.close()
