class Config:
    SPARK_PROCESS = "spark_process"
    SPARK_INPUT = "input"
    SPARK_INPUT_SRC = "src"
    SPARK_INPUT_SRC_PATH = "src_path"
    SPARK_INPUT_CSV_SEPARATOR = "csv_separator"
    SPARK_INPUT_VIEW_NAME = "view_name"
    SPARK_QUERY = "query"
    SPARK_OUTPUT = "output"
    SPARK_OUTPUT_DEST = "dest"
    SPARK_OUTPUT_DEST_PATH = "dest_path"
    SPARK_PARALLELISM = "parallelism"
    SPARK_DRIVER_MEMORY = "spark_driver_memory"
    SPARK_EXECUTOR_CORES = "spark_executor_cores"  # For cluster master
    SPARK_EXECUTOR_MEMORY = "spark_executor_memory"  # For cluster master
    SPARK_CLUSTER_MASTER = "cluster_master"
    DEPLOYMENT_ENV = "DEPLOYMENT_ENV"
