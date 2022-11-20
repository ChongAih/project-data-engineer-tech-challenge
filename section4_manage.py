import argparse
import sys

from section4.main import execute_process_task
from section4.util.config_reader import ConfigReader
from section4.util.logger import logger
from section4.util.path_finder import get_config_file_path


def run(args: argparse.Namespace):
    # Read configuration file
    postgresql_config = ConfigReader.read_ini_config(
        get_config_file_path(args.postgresql_config)
    )
    task_config = ConfigReader.read_yaml_config(
        get_config_file_path(args.task_config)
    )
    execute_process_task(
        postgresql_config=postgresql_config,
        process_config=task_config
    )


if __name__ == "__main__":
    usage = """
    # For running process task
    python3 manage.py --postgresql-config postgresql.ini --task-config process.yaml
    """
    parser = argparse.ArgumentParser(description="Data ingestion deployment", usage=usage)
    parser.add_argument("--postgresql-config", default="section4_postgresql.ini",
                        help="PostgreSQL configuration filename, eg. --postgresql-config postgresql.ini")
    parser.add_argument("--task-config", help="Processing task configuration filename, eg. --task-config process.yaml")
    args = parser.parse_args()
    if not args.task_config:
        logger.error("Argument 'task_config' is a must for data processing task")
        sys.exit(1)
    run(args)
