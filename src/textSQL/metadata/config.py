import yaml
from pathlib import Path

def load_metadata_config(
    path: str
) -> dict:

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as file:

        return yaml.safe_load(file)