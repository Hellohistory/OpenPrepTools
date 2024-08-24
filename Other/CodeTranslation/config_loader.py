# config_loader.py

import yaml


def load_config(file_path="config.yaml"):
    with open(file_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    return config
