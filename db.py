import sqlite3

sqlite_db_name: str = "app.db"


def start_database():
    """
    Creates the database for the application if it does not already exist.
    """
    try:
        # Create or connect to the SQLite3 database
        conn = sqlite3.connect(sqlite_db_name)

        # Create a cursor object to execute SQL commands
        cursor = conn.cursor()

        # Create the Messages table if it doesn't exist
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS Messages (
                id INTEGER PRIMARY KEY,
                entity_id INTEGER,
                start_offset_id INTEGER, 
                last_offset_id INTEGER,
                collection_start_timestamp INTEGER,
                collection_end_timestamp INTEGER
            )
        """
        )
        # Fetch names of all tables
        res = cursor.execute("SELECT name FROM sqlite_master")
        all_tables: tuple[str] = res.fetchone()

        # Commit the transaction and close the connection
        conn.commit()
        conn.close()

        if "Messages" not in all_tables:
            print(f"Failed to create Messages table")
            raise
    except sqlite3.DatabaseError as err:
        raise err


def messages_get_offset_id(entity_id: int):
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

        # Get last row in Messages of a specified entity id (most recent Messages collection of a particular entity)
        res = cursor.execute(
            f"""
            SELECT * FROM Messages WHERE entity_id={entity_id} ORDER BY ID DESC LIMIT 1;
        """
        )
        returned_result: list[tuple] = res.fetchall()  # returns all resulting rows

        offset_id: int = 0
        entity_id: int = entity_id
        if offset_id is not None and len(returned_result) > 0:
            offset_id = returned_result[0][3]
        print(f"Latest offset id of {entity_id} from database: {offset_id}")

        # Commit the transaction and close the connection
        conn.commit()
        conn.close()

        return offset_id

    except sqlite3.DatabaseError as err:
        raise err


def messages_insert_offset_id(
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

        # Create the Messages table if it doesn't exist
        cursor.execute(
            f"""
            INSERT INTO Messages (
                entity_id, start_offset_id, last_offset_id, collection_start_timestamp, collection_end_timestamp
            ) 
            VALUES (
                {entity_id}, {start_offset_id}, {last_offset_id}, {collection_start_timestamp}, {collection_end_timestamp}
            )
        """
        )

        # Commit the transaction and close the connection
        conn.commit()
        conn.close()
    except sqlite3.DatabaseError as err:
        raise err
