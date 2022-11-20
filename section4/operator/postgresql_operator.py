from typing import List

import psycopg2
from psycopg2 import OperationalError

from section4.util.logger import logger, get_strip_query


class PostgreSQLOperator:
    def __init__(self, db_name: str, db_user: str, db_password: str, db_host: str, db_port: str):
        self.connection = None
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.db_host = db_host
        self.db_port = db_port
        self.create_connection(
            db_name=db_name,
            db_user=db_user,
            db_password=db_password,
            db_host=db_host,
            db_port=db_port
        )

    def create_connection(self, db_name: str, db_user: str, db_password: str, db_host: str, db_port: str):
        try:
            self.connection = get_postgresql_connection(
                db_name=db_name, db_user=db_user, db_password=db_password, db_host=db_host, db_port=db_port
            )
            logger.info(f"PostgreSQL DB connected successful, host:port - {db_host}:{db_port}")
        except OperationalError as e:
            logger.error(f"OperationalError occurred during connection to DB - '{e}'", exc_info=True)

    def execute_query(self, query: str, connection=None) -> list:
        connection = self.connection if not connection else connection
        try:
            connection.autocommit = True
            cursor = connection.cursor()
            logger.info(f"PostgreSQL query: \n{get_strip_query(query)}")
            cursor.execute(query)
            rows = []
            if cursor.description:
                for row in cursor:
                    rows.append(row)
            logger.info("PostgreSQL DB query executed successful")
            return rows
        except OperationalError as e:
            logger.error(f"OperationalError occurred during query to DB - '{e}'", exc_info=True)

    def show_table_schema(self, table: str, connection=None) -> None:
        query = f"""
            SELECT 
               table_name, 
               column_name, 
               data_type 
            FROM 
               information_schema.columns
            WHERE 
               table_name = '{table}'
        """
        rows = self.execute_query(query=query, connection=connection)
        for row in rows:
            logger.info(f"table_name: {row[0]}; column_name: {row[2]}, data_type: {row[2]}")

    def truncate_table(self, table: str, connection=None) -> None:
        query = f"""
            TRUNCATE TABLE {table}
        """
        self.execute_query(query=query, connection=connection)

    def close(self):
        if self.connection:
            self.connection.close()
            logger.info("PostgreSQL DB connection closed successful")


def get_postgresql_connection(db_name: str, db_user: str, db_password: str, db_host: str, db_port: str):
    return psycopg2.connect(
        database=db_name,
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port,
    )


def get_upsert_query(cols: List[str], table_name: str, unique_key: List[str],
                     cols_not_for_update: List[str] = None) -> str:
    # Create upsert query based on the unique index key
    cols_str = ", ".join(cols)
    insert_query = f"INSERT INTO {table_name} ({cols_str}) VALUES %s "

    if cols_not_for_update is not None:
        cols_not_for_update.extend(unique_key)
    else:
        cols_not_for_update = [col for col in unique_key]

    unique_key_str = ", ".join(unique_key)
    update_cols = [col for col in cols if col not in cols_not_for_update]
    update_cols_str = ", ".join(update_cols)

    update_cols_with_excluded_markers = [f'EXCLUDED.{col}' for col in update_cols]
    update_cols_with_excluded_markers_str = ', '.join(update_cols_with_excluded_markers)

    on_conflict_clause = (f" ON CONFLICT ({unique_key_str}) DO UPDATE SET ({update_cols_str})"
                          f" = ({update_cols_with_excluded_markers_str});")

    return insert_query + on_conflict_clause
