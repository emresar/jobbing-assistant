import os
from dataclasses import dataclass
from typing import Any, Dict

import yaml


@dataclass
class Config:
    endpoint_url: str
    tags_url: str
    docs_dir: str
    num_predict: int
    num_ctx: int
    model: str
    temperature: float


def load_config() -> Config:
    config_file = os.environ.get("CONFIG_FILE", "config.yaml")
    with open(config_file, "r") as f:
        config_dict = yaml.safe_load(f)
    return Config(**config_dict)
