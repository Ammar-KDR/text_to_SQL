from datetime import datetime, timedelta
import random

from faker import Faker

from textSQL.database.models import User, UserRole, Role


fake = Faker()


ACCOUNT_STATUSES = [
    ("active", 0.85),
    ("inactive", 0.10),
    ("suspended", 0.05),
]


def weighted_choice(values):
    choices = [item[0] for item in values]
    weights = [item[1] for item in values]

    return random.choices(
        choices,
        weights=weights,
        k=1
    )[0]


def random_date():

    start = datetime(2024, 1, 1)
    end = datetime(2026, 12, 31)

    days = (end - start).days

    return start + timedelta(
        days=random.randint(0, days)
    )
def generate_last_login(status):

    if status == "active":
        return random_date()

    if status == "inactive":
        return random_date() if random.random() < 0.5 else None

    if status == "suspended":
        return random_date()

def seed_users(session, count):

    users = []

    for _ in range(count):
        status = weighted_choice(ACCOUNT_STATUSES)

        user = User(
            email=fake.unique.email(),
            password_hash="$2b$12$synthetic_hash",
            account_status=weighted_choice(
                ACCOUNT_STATUSES
            ),
            created_at=random_date(),
            last_login_at=generate_last_login(status)
        )

        users.append(user)


    session.add_all(users)

    session.flush()


    assign_customer_role(
        session,
        users
    )

    session.commit()

    return users



def assign_customer_role(session, users):

    customer_role = (
        session.query(Role)
        .filter(
            Role.role_name == "customer"
        )
        .first()
    )

    if not customer_role:
        raise Exception(
            "Customer role not found. Seed roles first."
        )


    mappings = []

    for user in users:

        mappings.append(
            UserRole(
                user_id=user.user_id,
                role_id=customer_role.role_id
            )
        )

    session.add_all(mappings)