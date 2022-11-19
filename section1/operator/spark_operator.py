import os

from pyspark.sql import SparkSession
from pyspark.sql.dataframe import DataFrame

from section1.util.logger import logger


class SparkOperator:
    # https://www.ibm.com/docs/en/izoda/1.1.0?topic=guide-memory-cpu-configuration-options
    def __init__(self, cluster_master: str = None, local_cpu: int = 3,
                 spark_driver_memory: str = "1g", spark_executor_cores: str = "2", spark_executor_memory: str = "2g"):
        """
        :param local_cpu: number of driver to be used in local master
        :param spark_driver_memory: amount of driver memory, driver mainly used to create DAG and schedule job

        Only 1 executor (also acts as driver) will be allowed in standalone Spark (
        https://livebook.manning.com/book/spark-in-action/chapter-11/23). All applications submitted to the standalone
        mode cluster will run in FIFO (first-in-first-out) order, and each application will try to use all available nodes.

        Parameter only works in cluster master
        :param cluster_master: name of the distribution cluster, leave as None to start standalone sparksession
        :param spark_executor_cores: amount of executor thread for executing DAG/ processing
        :param spark_executor_memory: amount of executor memory for executing DAG/ processing
            (memory in 1 executor shared among all executor cores of that executor)
        """
        self.spark: SparkSession = None
        self.create_spark_session(local_cpu=local_cpu, cluster_master=cluster_master,
                                  spark_executor_memory=spark_executor_memory,
                                  spark_executor_cores=spark_executor_cores, spark_driver_memory=spark_driver_memory)

    def create_spark_session(self, local_cpu: int, cluster_master: str, spark_driver_memory: str,
                             spark_executor_cores: str, spark_executor_memory: str):
        error = False
        error_message = ""
        try:
            if not cluster_master:
                # Export Spark environment variable in case hostname mapping not available in /etc/hosts
                # SPARK_LOCAL_HOSTNAME and SPARK_LOCAL_IP not available in SparkSession config
                os.environ["SPARK_LOCAL_IP"] = "127.0.0.1"
                self.spark = SparkSession \
                    .builder \
                    .appName("project-data-pipeline") \
                    .master(f"local[{local_cpu}]") \
                    .config("spark.driver.memory", spark_driver_memory) \
                    .config("spark.cores.max", f"{local_cpu}") \
                    .config("spark.memory.fraction", "0.9") \
                    .config("spark.memory.memoryFraction", "0.5") \
                    .getOrCreate()
            else:
                self.spark = SparkSession \
                    .builder \
                    .appName("project-data-pipeline") \
                    .master(cluster_master) \
                    .config("spark.driver.memory", spark_driver_memory) \
                    .config("spark.cores.max", f"{local_cpu}") \
                    .config("spark.executor.cores", spark_executor_cores) \
                    .config("spark.executor.memory", spark_executor_memory) \
                    .getOrCreate()
            ui_web_url = self.spark.sparkContext.uiWebUrl
            logger.info(f"SparkSession created successful, web UI available on {ui_web_url}")
        except Exception as e:
            error = True
            error_message = f"Exception occurred during spark session initialization - '{e}'"
        finally:
            if error:
                raise Exception(error_message)

    def create_view(self, source: str = None, view_name: str = None, csv_separator: str = None, source_path: str = None,
                    view_query: str = None, db_name: str = None, db_user: str = None, db_host: str = None,
                    db_password: str = None, db_port: str = None, **kwargs) -> None:
        error = False
        error_message = ""
        try:
            df: DataFrame = None
            if source == "csv":
                df = self.spark.read \
                    .option("sep", csv_separator) \
                    .option("header", "true") \
                    .option("enforceSchema", "true") \
                    .csv(source_path)
            elif source == "postgresql":
                df = self.spark.read.format("jdbc") \
                    .option("url", f"jdbc:postgresql://{db_host}:{db_port}/{db_name}") \
                    .option("query", view_query) \
                    .option("user", db_user) \
                    .option("password", db_password) \
                    .option("pushDownPredicate", "true") \
                    .option("driver", "org.postgresql.Driver") \
                    .load()
            else:
                error = True
                error_message = f"Spark view from '{source}' is currently not supported yet"
                logger.info(error_message)
            if df:
                df.createOrReplaceTempView(view_name)
                logger.info("Showing dataframe schema")
                df.printSchema()
        except Exception as e:
            error = True
            error_message = f"Exception occurred during spark session create_view - '{e}'"
        finally:
            if error:
                raise Exception(error_message)

    def execute_query(self, query: str) -> DataFrame:
        error = False
        error_message = ""
        try:
            logger.info(f"Spark query: \n{query}")
            df = self.spark.sql(query)
            logger.info("Showing dataframe schema")
            df.printSchema()
            return df
        except Exception as e:
            error = True
            error_message = f"Exception occurred during spark session execute_query - '{e}'"
        finally:
            if error:
                raise Exception(error_message)

    def write_to_dest(self, df: DataFrame, dest: str = None, dest_path: str = None, mode: str = "overwrite"):
        error = False
        error_message = ""
        try:
            if dest == "csv":
                df.write.mode(mode) \
                    .option("header", "true") \
                    .csv(dest_path)
            else:
                error = True
                error_message = f"Write to '{dest}' is currently not supported yet"
                logger.info(error_message)
        except Exception as e:
            error = True
            error_message = f"Exception occurred during spark session create_view - '{e}'"
        finally:
            if error:
                raise Exception(error_message)

    def stop(self):
        try:
            if self.spark:
                self.spark.stop()
                logger.info("SparkSession stopped successful")
        except Exception:
            logger.info("Error in stop spark session or spark session already stopped", exc_info=True)
