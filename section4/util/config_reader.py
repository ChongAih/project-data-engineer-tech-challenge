import yaml
from configobj import ConfigObj


class ConfigReader:
    @staticmethod
    def read_ini_config(config_path: str) -> dict:
        config = ConfigObj(config_path)
        return config.dict()

    @staticmethod
    def read_yaml_config(config_path: str) -> dict:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        return config
