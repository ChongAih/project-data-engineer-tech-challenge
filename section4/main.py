import os
import sys
from datetime import date, timedelta, datetime
from typing import Iterable

import requests
from psycopg2.extras import execute_values

from section4.config import Config
from section4.operator.postgresql_operator import PostgreSQLOperator, get_postgresql_connection, get_upsert_query
from section4.util.logger import logger


def execute_process_task(postgresql_config: dict, process_config: dict):
    postgresql_operator: PostgreSQLOperator = None
    try:
        # Get PostgreSQL and Spark operators
        postgresql_operator: PostgreSQLOperator = PostgreSQLOperator(
            **get_master_db_credential(postgresql_config=postgresql_config)
        )

        country = process_config.get(Config.COUNTRY, "singapore")
        interval = process_config.get(Config.INTERVAL, 60)
        response_record = process_covid_response_json(country=country, interval=interval)

        upsert_to_postgresql(
            postgresql_config=postgresql_config,
            process_config=process_config,
            response_record=response_record
        )
    except Exception as e:
        logger.info(f"Exception occurred during execute_process_task - {e}", exc_info=True)
        sys.exit(1)
    finally:
        if postgresql_operator:
            postgresql_operator.close()


def get_master_db_credential(postgresql_config: dict) -> dict:
    return {
        "db_name": postgresql_config[Config.POSTGRES_DB],
        "db_user": postgresql_config[Config.POSTGRES_USER],
        "db_password": postgresql_config[Config.POSTGRES_PASSWORD],
        "db_host": postgresql_config[Config.POSTGRES_HOSTNAME] if os.getenv(Config.DEPLOYMENT_ENV) else
        postgresql_config[Config.POSTGRES_EXTERNAL_HOSTNAME],
        "db_port": postgresql_config[Config.POSTGRES_PORT] if os.getenv(Config.DEPLOYMENT_ENV) else
        postgresql_config[Config.POSTGRES_EXTERNAL_PORT]
    }


def get_covid_response_json(country: str, start_date: date = None, end_date: date = None, interval: int = 60):
    url = f"https://api.covid19api.com/country/{country.lower()}/status/confirmed"

    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=interval + Config.PAST_X_AVERAGE)
    start_date_str = start_date.strftime("%Y-%m-%dT%H:%M:%S+08:00")
    end_date_str = end_date.strftime("%Y-%m-%dT%H:%M:%S+08:00")
    params = {"from": start_date_str, "to": end_date_str}

    logger.info(f"URL: {url}, start_date: {start_date_str}, end_date: {end_date_str}")

    response_json = requests.request("GET", url, params=params).json()
    if isinstance(response_json, dict) and "message" in response_json and response_json["message"] == "Not Found":
        raise Exception(f"Data not found - URL: '{url}', "
                        f"start_date: {start_date_str}, end_date: {end_date_str}")

    return response_json


def process_covid_response_json(country: str, start_date: date = None, end_date: date = None, interval: int = 60):
    response_json = get_covid_response_json(country=country, start_date=start_date,
                                            end_date=end_date, interval=interval)
    countries = []
    num_cases = []
    dates = []
    for i in range(1, len(response_json)):
        record = response_json[i]
        record_bef = response_json[i - 1]
        if i != 0:
            countries.append(record["CountryCode"])
            num_cases.append(record["Cases"] - record_bef["Cases"])
            dates.append(datetime.strptime(record["Date"], "%Y-%m-%dT%H:%M:%SZ").date())
    num_p7d_avg_cases = get_moving_average(num_cases=num_cases)
    countries = countries[len(countries) - len(num_p7d_avg_cases):]
    num_cases = num_cases[len(num_cases) - len(num_p7d_avg_cases):]
    dates = dates[len(dates) - len(num_p7d_avg_cases):]
    output = [*zip(countries, dates, num_cases, num_p7d_avg_cases)]
    return output


def get_moving_average(num_cases: list, window_size: int = Config.PAST_X_AVERAGE):
    i = 0
    moving_averages = []
    while i < len(num_cases) - window_size + 1:
        window = num_cases[i: i + window_size]
        window_average = int(sum(window) / window_size)
        moving_averages.append(window_average)
        i += 1
    return moving_averages


def upsert_to_postgresql(postgresql_config: dict, process_config: dict, response_record: list):
    # Create upsert query for batch upsert
    upsert_query = get_upsert_query(
        cols=process_config[Config.TABLE_COLUMNS],
        table_name=process_config[Config.TABLE],
        unique_key=process_config[Config.UNIQUE_COLUMNS]
    )
    logger.info(f"upsert_query: {upsert_query}")
    database_credential = get_master_db_credential(postgresql_config=postgresql_config)

    record_upserted = batch_and_upsert(
        df_partition=response_record,
        sql=upsert_query,
        database_credentials=database_credential,
        batch_size=1000
    )

    logger.info(f"Total number of records upserted: {record_upserted}")


def batch_and_upsert(df_partition: Iterable,
                     sql: str,
                     database_credentials: dict,
                     batch_size: int = 1000):
    """
    Batch the input dataframe_partition as per batch_size and upsert
    to postgres using psycopg2 execute values.
    :param df_partition: Pyspark DataFrame partition
    :param sql: query to insert/upsert the spark dataframe partition to postgres.
    :param database_credentials: postgres database credentials
    :param batch_size: size of batch per round trip to database
    :return: total records processed.
    """
    conn, cur = None, None
    counter = 0
    batch = []
    for record in df_partition:
        counter += 1
        batch.append(record)
        if not conn:
            conn = get_postgresql_connection(**database_credentials)
            cur = conn.cursor()
        if counter % batch_size == 0:
            execute_values(
                cur=cur, sql=sql,
                argslist=batch,
                page_size=batch_size
            )
            conn.commit()
            batch = []
    if batch:
        execute_values(
            cur=cur, sql=sql,
            argslist=batch,
            page_size=batch_size
        )
        conn.commit()
    if cur:
        cur.close()
    if conn:
        conn.close()
    return counter
