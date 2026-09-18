from __future__ import annotations

from datetime import datetime, timedelta
import random

from sqlalchemy import insert

from textSQL.database.models import (
    User,
    Customer,
    CustomerAddress,
    CustomerEvent,
)

from textSQL.database.seeding import fake


DATA_START = datetime(2024, 1, 1)
DATA_END = datetime(2026, 9, 15, 23, 59, 59)


COUNTRIES = [
    ("Jordan", 0.45),
    ("Saudi Arabia", 0.30),
    ("UAE", 0.15),
    ("Kuwait", 0.07),
    ("Qatar", 0.03),
]


CITIES = {
    "Jordan": [
        "Amman",
        "Irbid",
        "Zarqa",
        "Aqaba",
        "Salt",
        "Madaba",
    ],

    "Saudi Arabia": [
        "Riyadh",
        "Jeddah",
        "Dammam",
        "Khobar",
        "Mecca",
        "Medina",
    ],

    "UAE": [
        "Dubai",
        "Abu Dhabi",
        "Sharjah",
        "Ajman",
    ],

    "Kuwait": [
        "Kuwait City",
        "Hawalli",
        "Salmiya",
        "Farwaniya",
    ],

    "Qatar": [
        "Doha",
        "Al Rayyan",
        "Al Wakrah",
    ],
}


ADDRESS_TYPES = [
    "home",
    "work",
    "shipping",
    "billing",
]


BEHAVIOR_SEGMENTS = [
    ("premium", 0.05),
    ("regular", 0.55),
    ("occasional", 0.30),
    ("dormant", 0.10),
]


EVENT_TYPES = {
    "premium": [
        ("product_view", 0.45),
        ("search", 0.13),
        ("add_to_cart", 0.18),
        ("remove_from_cart", 0.05),
        ("wishlist", 0.08),
        ("checkout_started", 0.11),
    ],

    "regular": [
        ("product_view", 0.52),
        ("search", 0.17),
        ("add_to_cart", 0.14),
        ("remove_from_cart", 0.05),
        ("wishlist", 0.06),
        ("checkout_started", 0.06),
    ],

    "occasional": [
        ("product_view", 0.58),
        ("search", 0.22),
        ("add_to_cart", 0.09),
        ("remove_from_cart", 0.04),
        ("wishlist", 0.05),
        ("checkout_started", 0.02),
    ],

    "dormant": [
        ("product_view", 0.65),
        ("search", 0.25),
        ("add_to_cart", 0.05),
        ("remove_from_cart", 0.02),
        ("wishlist", 0.03),
    ],
}


EVENT_COUNT_RANGES = {
    "premium": (70, 180),
    "regular": (15, 70),
    "occasional": (3, 20),
    "dormant": (0, 4),
}


def weighted_choice(options):
    values = [value for value, _ in options]
    weights = [weight for _, weight in options]

    return random.choices(
        values,
        weights=weights,
        k=1,
    )[0]


def random_datetime_between(
    start: datetime,
    end: datetime,
    *,
    bias: str = "uniform",
) -> datetime:

    if start >= end:
        return start

    start_ts = start.timestamp()
    end_ts = end.timestamp()

    if bias == "recent":
        value = random.triangular(
            start_ts,
            end_ts,
            end_ts,
        )

    elif bias == "old":
        value = random.triangular(
            start_ts,
            end_ts,
            start_ts,
        )

    else:
        value = random.uniform(
            start_ts,
            end_ts,
        )

    return datetime.fromtimestamp(value)


def generate_country() -> str:
    return weighted_choice(COUNTRIES)


def generate_phone(country: str) -> str | None:

    # A small percentage of customers have no stored phone.
    if random.random() < 0.06:
        return None

    if country == "Jordan":
        return f"+9627{random.randint(70000000, 99999999)}"

    if country == "Saudi Arabia":
        return f"+9665{random.randint(10000000, 99999999)}"

    if country == "UAE":
        return f"+9715{random.randint(10000000, 99999999)}"

    if country == "Kuwait":
        return f"+965{random.randint(10000000, 99999999)}"

    if country == "Qatar":
        return f"+974{random.randint(30000000, 79999999)}"

    return None


def generate_postal_code(country: str) -> str | None:

    # UAE and Qatar commonly don't use conventional postal
    # codes in the same way as many other countries.
    if country in {"UAE", "Qatar"}:
        return None

    return str(
        random.randint(10000, 99999)
    )


def derive_customer_status(
    user_status: str | None,
) -> str:

    # Customer business state is correlated with,
    # but not identical to, authentication state.

    if user_status == "suspended":

        return random.choices(
            ["blocked", "inactive", "active"],
            weights=[0.75, 0.20, 0.05],
            k=1,
        )[0]

    if user_status == "inactive":

        return random.choices(
            ["inactive", "active", "blocked"],
            weights=[0.65, 0.30, 0.05],
            k=1,
        )[0]

    return random.choices(
        ["active", "inactive", "blocked"],
        weights=[0.90, 0.08, 0.02],
        k=1,
    )[0]


def derive_behavior_segment(
    customer_status: str,
) -> str:

    if customer_status == "blocked":

        return random.choices(
            ["dormant", "occasional"],
            weights=[0.85, 0.15],
            k=1,
        )[0]

    if customer_status == "inactive":

        return random.choices(
            ["dormant", "occasional", "regular"],
            weights=[0.55, 0.35, 0.10],
            k=1,
        )[0]

    return weighted_choice(
        BEHAVIOR_SEGMENTS
    )


def address_count() -> int:

    # Some customers registered/browsed but never supplied
    # an address yet.
    return random.choices(
        [0, 1, 2, 3],
        weights=[0.08, 0.67, 0.20, 0.05],
        k=1,
    )[0]


def customer_event_count(
    segment: str,
) -> int:

    low, high = EVENT_COUNT_RANGES[segment]

    return random.randint(
        low,
        high,
    )


def seed_customers(
    session,
    count: int,
):

    users = (
        session.query(User)
        .order_by(User.user_id)
        .limit(int(count * 0.80))
        .all()
    )

    registered_target = int(
        count * 0.80
    )

    if len(users) < registered_target:

        raise RuntimeError(
            f"Need {registered_target} users for an "
            f"80% registered-customer ratio, but only "
            f"{len(users)} users exist."
        )

    customer_objects = []

    # Temporary metadata used by address/event generation.
    profiles = []

    # --------------------------------------------------
    # Registered customers
    # --------------------------------------------------

    for user in users:

        country = generate_country()

        # A customer profile cannot logically exist
        # before the user's account.
        registered_at = random_datetime_between(
            user.created_at,
            min(
                user.created_at + timedelta(days=3),
                DATA_END,
            ),
        )

        customer_status = derive_customer_status(
            user.account_status
        )

        segment = derive_behavior_segment(
            customer_status
        )

        customer = Customer(
            user_id=user.user_id,
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            phone=generate_phone(country),
            customer_status=customer_status,
            registered_at=registered_at,

            # Orders are the source of truth.
            # This gets populated after order generation.
            last_order_date=None,
        )

        customer_objects.append(customer)

        profiles.append(
            {
                "customer": customer,
                "country": country,
                "segment": segment,
            }
        )

    # --------------------------------------------------
    # Guest customers
    # --------------------------------------------------

    guest_count = (
        count - len(customer_objects)
    )

    for _ in range(guest_count):

        country = generate_country()

        registered_at = random_datetime_between(
            DATA_START,
            DATA_END,
        )

        customer_status = random.choices(
            ["active", "inactive", "blocked"],
            weights=[0.88, 0.09, 0.03],
            k=1,
        )[0]

        segment = derive_behavior_segment(
            customer_status
        )

        customer = Customer(
            user_id=None,
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            phone=generate_phone(country),
            customer_status=customer_status,
            registered_at=registered_at,
            last_order_date=None,
        )

        customer_objects.append(customer)

        profiles.append(
            {
                "customer": customer,
                "country": country,
                "segment": segment,
            }
        )

    session.add_all(
        customer_objects
    )

    # Need customer_id values before creating
    # dependent address/event rows.
    session.flush()

    return profiles


def seed_customer_addresses(
    session,
    profiles,
    *,
    batch_size: int = 10_000,
):

    batch = []

    inserted = 0

    for profile in profiles:

        customer = profile["customer"]
        country = profile["country"]

        count = address_count()

        if count == 0:
            continue

        types = random.sample(
            ADDRESS_TYPES,
            k=min(
                count,
                len(ADDRESS_TYPES),
            ),
        )

        for address_type in types:

            city = random.choice(
                CITIES[country]
            )

            batch.append(
                {
                    "customer_id":
                        customer.customer_id,

                    "address_type":
                        address_type,

                    "city":
                        city,

                    "country":
                        country,

                    "postal_code":
                        generate_postal_code(
                            country
                        ),
                }
            )

            if len(batch) >= batch_size:

                session.execute(
                    insert(CustomerAddress),
                    batch,
                )

                inserted += len(batch)

                batch.clear()

    if batch:

        session.execute(
            insert(CustomerAddress),
            batch,
        )

        inserted += len(batch)

    return inserted


def seed_customer_events(
    session,
    profiles,
    *,
    batch_size: int = 10_000,
):

    batch = []

    inserted = 0

    for profile in profiles:

        customer = profile["customer"]
        segment = profile["segment"]

        count = customer_event_count(
            segment
        )

        if count == 0:
            continue

        if customer.customer_status == "active":
            time_bias = "recent"

        elif customer.customer_status == "inactive":
            time_bias = "old"

        else:
            time_bias = "old"

        event_options = EVENT_TYPES[
            segment
        ]

        for _ in range(count):

            event_type = weighted_choice(
                event_options
            )

            event_time = (
                random_datetime_between(
                    customer.registered_at,
                    DATA_END,
                    bias=time_bias,
                )
            )

            batch.append(
                {
                    "customer_id":
                        customer.customer_id,

                    "event_type":
                        event_type,

                    "timestamp":
                        event_time,
                }
            )

            if len(batch) >= batch_size:

                session.execute(
                    insert(CustomerEvent),
                    batch,
                )

                inserted += len(batch)

                batch.clear()

    if batch:

        session.execute(
            insert(CustomerEvent),
            batch,
        )

        inserted += len(batch)

    return inserted


def seed_customer_domain(
    session,
    customer_count: int,
    *,
    event_batch_size: int = 10_000,
):

    print(
        f"Creating {customer_count:,} customers..."
    )

    profiles = seed_customers(
        session,
        customer_count,
    )

    print(
        "Creating customer addresses..."
    )

    address_count_inserted = (
        seed_customer_addresses(
            session,
            profiles,
        )
    )

    print(
        "Creating customer behavior events..."
    )

    event_count_inserted = (
        seed_customer_events(
            session,
            profiles,
            batch_size=event_batch_size,
        )
    )

    session.commit()

    registered = sum(
        1
        for profile in profiles
        if profile["customer"].user_id
        is not None
    )

    guests = (
        len(profiles) - registered
    )

    print(
        "Customer domain complete:"
    )

    print(
        f"  customers:  {len(profiles):,}"
    )

    print(
        f"  registered: {registered:,}"
    )

    print(
        f"  guests:     {guests:,}"
    )

    print(
        f"  addresses:  "
        f"{address_count_inserted:,}"
    )

    print(
        f"  events:     "
        f"{event_count_inserted:,}"
    )

    return profiles