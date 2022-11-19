import argparse
import sys
import unittest

from section1.main import execute_process_task
from section1.util.config_reader import ConfigReader
from section1.util.logger import logger
from section1.util.path_finder import get_config_file_path


def test():
    tests = unittest.TestLoader().discover("section1/test", pattern='test*.py')
    result = unittest.TextTestRunner(verbosity=2).run(tests)
    if result.wasSuccessful():
        return 0
    else:
        return 1


def run(args: argparse.Namespace):
    # Read configuration file
    task_config = ConfigReader.read_yaml_config(
        get_config_file_path(args.task_config)
    )
    sql_kwargs = args.sql_kwargs or {}
    execute_process_task(
        process_config=task_config,
        sql_kwargs=sql_kwargs
    )


class KeyValue(argparse.Action):
    # Constructor calling
    def __call__(self, parser, namespace,
                 values, option_string=None):
        setattr(namespace, self.dest, dict())
        # Split into key and value & assign into dictionary
        for value in values:
            key, value = value.split('=')
            getattr(namespace, self.dest)[key] = value


if __name__ == "__main__":
    usage = """
    # For running unittest
    python3 section1_manage.py --test

    # For running process csv task
    python3 section1_manage.py --task-config section1_process.yaml
    """
    parser = argparse.ArgumentParser(description="Data ingestion testing or deployment", usage=usage)
    parser.add_argument("--test", action="store_true", default=False, help="Data processing function unittest")
    parser.add_argument("--task-config", help="Processing task configuration filename, eg. --task-config process.yaml")
    parser.add_argument("--sql-kwargs", nargs="*", action=KeyValue,
                        help="KV pair to be used in task_config SQL, eg. "
                             "--kwargs start_date=2022-01-01 end_date=2022-01-02")
    args = parser.parse_args()

    if not args.test and not args.task_config:
        logger.error("Argument 'task_config' is a must for data processing task")
        sys.exit(1)
    if args.test:
        test()
    else:
        run(args)
