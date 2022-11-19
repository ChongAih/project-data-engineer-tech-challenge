import os
import sys
from string import Template

from pyspark.sql import DataFrame

from section1.config import Config
from section1.operator.spark_operator import SparkOperator
from section1.util.logger import logger
from section1.util.path_finder import get_resource_src_path, get_resource_dest_path


def execute_process_task(process_config: dict, sql_kwargs: dict):
    spark_op: SparkOperator = None
    try:
        # Get Spark operators
        spark_op = SparkOperator(
            **get_spark_configuration(task_config=process_config)
        )
        # Execute process logic
        create_view_process_df(process_config=process_config, spark_op=spark_op, sql_kwargs=sql_kwargs)
    except Exception as e:
        logger.info(f"Exception occurred during execute_process_task - {e}", exc_info=True)
        sys.exit(1)
    finally:
        if spark_op:
            spark_op.stop()


def get_spark_configuration(task_config: dict) -> dict:
    return {
        "local_cpu": task_config.get(Config.SPARK_PARALLELISM, 2),
        "spark_driver_memory": task_config.get(Config.SPARK_DRIVER_MEMORY, "1g"),
        "spark_executor_cores": task_config.get(Config.SPARK_EXECUTOR_CORES, 2),
        "spark_executor_memory": task_config.get(Config.SPARK_EXECUTOR_MEMORY, "1g"),
        "cluster_master": task_config.get(Config.SPARK_CLUSTER_MASTER, None)
    }


def create_view_process_df(process_config: dict, spark_op: SparkOperator, sql_kwargs: dict) -> DataFrame:
    spark_process_config: dict = process_config[Config.SPARK_PROCESS]
    for process, config in spark_process_config.items():
        # Get input config
        input_config = config[Config.SPARK_INPUT]
        source = input_config.get(Config.SPARK_INPUT_SRC, None)
        source_path = os.path.join(get_resource_src_path(), input_config.get(Config.SPARK_INPUT_SRC_PATH, ""))
        csv_separator = input_config.get(Config.SPARK_INPUT_CSV_SEPARATOR, None)
        view_name = input_config[Config.SPARK_INPUT_VIEW_NAME]

        # Create SQL view
        spark_op.create_view(source=source, csv_separator=csv_separator, source_path=source_path, view_name=view_name)

        # Get process query and create processed DF/DAG
        # Lazy transformation (operation not performed yet until action is called)
        sql_kwargs.update({Config.SPARK_INPUT_VIEW_NAME: view_name})
        process_query = Template(config[Config.SPARK_QUERY]).substitute(**sql_kwargs)
        df = spark_op.execute_query(query=process_query)

        # Write to destination - actual operation starts
        output_config = config[Config.SPARK_OUTPUT]
        dest = output_config.get(Config.SPARK_OUTPUT_DEST, None)
        dest_path = os.path.join(get_resource_dest_path(), output_config.get(Config.SPARK_OUTPUT_DEST_PATH, ""))
        spark_op.write_to_dest(df=df, dest=dest, dest_path=dest_path)
