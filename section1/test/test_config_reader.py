import unittest

from section1.util.config_reader import ConfigReader
from section1.util.path_finder import get_config_file_path


class TestConfigReader(unittest.TestCase):
    test_config_yaml_path = "section1_test_config.yaml"

    def test_read_yaml_config(self):
        test_config = ConfigReader.read_yaml_config(get_config_file_path(TestConfigReader.test_config_yaml_path))
        self.assertEqual(len(test_config.keys()), 2)
        self.assertEqual(test_config["test_name"], "test_name")
