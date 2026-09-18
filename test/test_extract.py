from textSQL.database.connection import engine
from textSQL.metadata.extractor import (
    extract_database_metadata
)
from textSQL.metadata.config import (
    load_metadata_config
)


config = load_metadata_config(
    "src/textSQL/config/metadata_config.yaml"
)


metadata = extract_database_metadata(
    engine,
    config
)


print(
    metadata.model_dump_json(
        indent=2
    )
)