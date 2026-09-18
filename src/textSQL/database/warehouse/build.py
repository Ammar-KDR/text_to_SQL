
from textSQL.database.connection import (
    SessionLocal,
)

from textSQL.database.warehouse.loader import (
    build_warehouse,
)


def main():

    with SessionLocal() as session:

        build_warehouse(
            session,
            reset=True,
        )


if __name__ == "__main__":
    main()