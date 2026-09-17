from sqlalchemy.orm import Session

from .config import DEFAULT_CONFIG
from .generators.user import seed_users


# def seed_database(session: Session):

#     config = DEFAULT_CONFIG

#     print("Starting database seed...")

#     seed_roles(session, config)

#     seed_users(session, config)

#     seed_customers(session, config)

#     seed_products(session, config)

#     seed_orders(session, config)

#     seed_inventory(session, config)

#     seed_marketing(session, config)

#     seed_reviews(session, config)

#     print("Database seed completed")

from textSQL.database.connection import SessionLocal

from .config import SeedConfig

from .generators.security import seed_security
from .generators.catalog import (
    seed_brands,
    seed_categories,
)
from .generators.operations import (
    seed_warehouses,
)
from .helpers import clear_database

def seed_database(reset=False):

    with SessionLocal() as session:

        if reset:
            print("Clearing database...")
            clear_database(session)


        print("Seeding reference data...")


        seed_security(session)
        seed_users(session,20000)

        seed_brands(
            session,
            SeedConfig.brands
        )

        seed_categories(session)

        seed_warehouses(session)
        


        print("Reference data complete")


if __name__ == "__main__":

    import sys

    reset = "--reset" in sys.argv

    seed_database(reset=reset)
    

