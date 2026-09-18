from sqlalchemy.orm import Session

from .config import CONFIG
from .generators.user import seed_users
from .generators.product import (
    seed_products,
)

from .generators.inventory import (
    seed_inventory,
)


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
from .generators.customer import (
    seed_customer_domain,
)
from .generators.commerce_reference import (
    seed_commerce_reference,
)

from .generators.order import (
    seed_orders,
)
from .generators.marketing import (
    seed_marketing_domain,
)

from .generators.review import (
    seed_reviews,
)
def seed_database(reset=False):

    with SessionLocal() as session:

        if reset:
            print("Clearing database...")
            clear_database(session)

        print("Seeding reference data...")

        seed_security(session)

        seed_brands(
            session,
            CONFIG.brands,
        )

        seed_categories(session)

        seed_warehouses(session)

        print(
            "Reference data complete"
        )

        print("Seeding users...")

        seed_users(
            session,
            CONFIG.users,
        )

        print("Users complete")

        print(
            "Seeding customer domain..."
        )

        seed_customer_domain(
            session,
            CONFIG.customers,
            event_batch_size=
                CONFIG.event_insert_batch_size,
        )
        print(
    "Seeding product domain..."
)
        

        seed_products(
            session,
            CONFIG.products,
        )


        print(
            "Seeding inventory domain..."
        )

        seed_inventory(
            session,
        )
        print(
    "Seeding commerce reference data..."
)

        seed_commerce_reference(
            session
        )


        print(
            "Seeding transactional domain..."
        )
        
        seed_orders(
            session,
            CONFIG.orders,
            batch_size=
                CONFIG.order_batch_size,
        )
        print(
    "Seeding marketing domain..."
)

        seed_marketing_domain(
            session,
            CONFIG.campaigns,
        )


        print(
            "Seeding reviews..."
        )

        seed_reviews(
            session,
            CONFIG.reviews,
        )


if __name__ == "__main__":

    import sys

    reset = "--reset" in sys.argv

    seed_database(reset=reset)

    

