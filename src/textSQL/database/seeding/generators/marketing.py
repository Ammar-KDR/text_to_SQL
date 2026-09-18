from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
import random

from sqlalchemy import insert, select

from textSQL.database.models import (
    Campaign,
    CampaignProduct,
    CustomerCampaign,
    CampaignConversion,
    Customer,
    Product,
    Order,
    OrderItem,
    ProductVariant,
)


DATA_START = datetime(2024, 1, 1)

DATA_END = datetime(
    2026,
    9,
    15,
    23,
    59,
    59,
)


CAMPAIGN_TYPES = [
    "seasonal",
    "flash_sale",
    "acquisition",
    "retention",
    "loyalty",
    "category_promotion",
]


CAMPAIGN_PREFIXES = [
    "Winter",
    "Spring",
    "Summer",
    "Autumn",
    "Ramadan",
    "Eid",
    "Weekend",
    "Back to School",
    "New Customer",
    "Loyalty",
    "Mega Sale",
    "Clearance",
]


CAMPAIGN_SUFFIXES = [
    "Sale",
    "Savings",
    "Rewards",
    "Special",
    "Campaign",
    "Promotion",
    "Deals",
]


def random_campaign_dates():

    start = DATA_START + timedelta(
        days=random.randint(
            0,
            (DATA_END - DATA_START).days - 60,
        )
    )

    duration = random.randint(
        5,
        45,
    )

    end = min(
        start + timedelta(days=duration),
        DATA_END,
    )

    return start, end


def campaign_budget():

    return Decimal(
        str(
            random.choice(
                [
                    2500,
                    5000,
                    7500,
                    10000,
                    15000,
                    25000,
                    40000,
                    60000,
                    100000,
                ]
            )
        )
    )


def seed_campaigns(
    session,
    count: int,
):

    print(
        f"Creating {count:,} campaigns..."
    )

    campaigns = []

    used_names = set()

    for index in range(
        1,
        count + 1,
    ):

        start_date, end_date = (
            random_campaign_dates()
        )

        while True:

            name = (
                f"{random.choice(CAMPAIGN_PREFIXES)} "
                f"{random.choice(CAMPAIGN_SUFFIXES)} "
                f"{start_date.year}"
            )

            if name not in used_names:
                break

            name = f"{name} {index}"

            if name not in used_names:
                break

        used_names.add(name)

        campaigns.append(
            Campaign(
                campaign_name=name,
                campaign_type=random.choice(
                    CAMPAIGN_TYPES
                ),
                budget=campaign_budget(),
                start_date=start_date,
                end_date=end_date,
                created_at=max(
                    DATA_START,
                    start_date
                    - timedelta(
                        days=random.randint(
                            7,
                            60,
                        )
                    ),
                ),
            )
        )

    session.add_all(
        campaigns
    )

    session.flush()

    return campaigns


def seed_campaign_products(
    session,
    campaigns,
):

    products = (
        session.query(
            Product.product_id
        )
        .all()
    )

    product_ids = [
        row.product_id
        for row in products
    ]

    rows = []

    campaign_products = {}

    for campaign in campaigns:

        number_products = random.randint(
            15,
            min(
                150,
                len(product_ids),
            ),
        )

        selected_products = random.sample(
            product_ids,
            k=number_products,
        )

        campaign_products[
            campaign.campaign_id
        ] = set(
            selected_products
        )

        for product_id in selected_products:

            discount = random.choice(
                [
                    5,
                    10,
                    15,
                    20,
                    25,
                    30,
                ]
            )

            rows.append(
                {
                    "campaign_id":
                        campaign.campaign_id,

                    "product_id":
                        product_id,

                    "discount_percentage":
                        Decimal(
                            str(discount)
                        ),

                    "created_at":
                        campaign.created_at,
                }
            )

    session.execute(
        insert(
            CampaignProduct
        ),
        rows,
    )

    return campaign_products


def random_timestamp(
    start: datetime,
    end: datetime,
):

    if start >= end:
        return start

    seconds = int(
        (end - start)
        .total_seconds()
    )

    return start + timedelta(
        seconds=random.randint(
            0,
            max(
                seconds,
                0,
            ),
        )
    )


def seed_customer_campaigns(
    session,
    campaigns,
):

    customer_ids = [
        row.customer_id
        for row in (
            session.query(
                Customer.customer_id
            ).all()
        )
    ]

    rows = []

    campaign_customer_map = {}

    for campaign in campaigns:

        audience_size = random.randint(
            500,
            3500,
        )

        audience_size = min(
            audience_size,
            len(customer_ids),
        )

        audience = random.sample(
            customer_ids,
            audience_size,
        )

        campaign_customer_map[
            campaign.campaign_id
        ] = set(audience)

        for customer_id in audience:

            interaction = random.choices(
                [
                    "received",
                    "opened",
                    "clicked",
                ],
                weights=[
                    55,
                    30,
                    15,
                ],
                k=1,
            )[0]

            rows.append(
                {
                    "customer_id":
                        customer_id,

                    "campaign_id":
                        campaign.campaign_id,

                    "interaction_type":
                        interaction,

                    "created_at":
                        random_timestamp(
                            campaign.start_date,
                            campaign.end_date,
                        ),
                }
            )

    batch_size = 10_000

    for start in range(
        0,
        len(rows),
        batch_size,
    ):

        session.execute(
            insert(
                CustomerCampaign
            ),
            rows[
                start:
                start + batch_size
            ],
        )

    return campaign_customer_map


def seed_campaign_conversions(
    session,
    campaigns,
    campaign_products,
    campaign_customer_map,
):

    conversion_rows = []

    converted_pairs = set()

    for campaign in campaigns:

        product_ids = list(
            campaign_products[
                campaign.campaign_id
            ]
        )

        if not product_ids:
            continue

        candidate_orders = (
            session.execute(
                select(
                    Order.order_id,
                    Order.customer_id,
                    Order.created_at,
                )
                .join(
                    OrderItem,
                    OrderItem.order_id
                    == Order.order_id,
                )
                .join(
                    ProductVariant,
                    ProductVariant.variant_id
                    == OrderItem.variant_id,
                )
                .where(
                    Order.created_at
                    >= campaign.start_date,
                )
                .where(
                    Order.created_at
                    <= campaign.end_date,
                )
                .where(
                    ProductVariant.product_id
                    .in_(product_ids)
                )
                .where(
                    Order.order_status.in_(
                        [
                            "processing",
                            "shipped",
                            "delivered",
                            "refunded",
                        ]
                    )
                )
                .distinct()
                .limit(1500)
            )
            .all()
        )

        if not candidate_orders:
            continue

        random.shuffle(
            candidate_orders
        )

        target_conversion_count = max(
            1,
            int(
                len(candidate_orders)
                * random.uniform(
                    0.08,
                    0.25,
                )
            ),
        )

        selected = candidate_orders[
            :target_conversion_count
        ]

        for order_id, customer_id, created_at in selected:

            if (
                customer_id
                not in campaign_customer_map[
                    campaign.campaign_id
                ]
            ):
                continue

            key = (
                campaign.campaign_id,
                order_id,
            )

            if key in converted_pairs:
                continue

            converted_pairs.add(key)

            conversion_rows.append(
                {
                    "campaign_id":
                        campaign.campaign_id,

                    "customer_id":
                        customer_id,

                    "order_id":
                        order_id,

                    "attribution_type":
                        random.choices(
                            [
                                "last_click",
                                "view_through",
                                "promo_code",
                            ],
                            weights=[
                                65,
                                20,
                                15,
                            ],
                            k=1,
                        )[0],

                    "created_at":
                        created_at,
                }
            )

    if conversion_rows:

        session.execute(
            insert(
                CampaignConversion
            ),
            conversion_rows,
        )

    # Upgrade matching customer_campaign records
    # to their furthest funnel stage.
    for row in conversion_rows:

        session.query(
            CustomerCampaign
        ).filter(
            CustomerCampaign.customer_id
            == row["customer_id"],
            CustomerCampaign.campaign_id
            == row["campaign_id"],
        ).update(
            {
                "interaction_type":
                    "converted"
            },
            synchronize_session=False,
        )

    return len(
        conversion_rows
    )


def seed_marketing_domain(
    session,
    campaign_count: int,
):

    campaigns = seed_campaigns(
        session,
        campaign_count,
    )

    print(
        "Assigning products to campaigns..."
    )

    campaign_products = (
        seed_campaign_products(
            session,
            campaigns,
        )
    )

    print(
        "Generating campaign audiences..."
    )

    campaign_customer_map = (
        seed_customer_campaigns(
            session,
            campaigns,
        )
    )

    print(
        "Generating attributed conversions..."
    )

    conversions = (
        seed_campaign_conversions(
            session,
            campaigns,
            campaign_products,
            campaign_customer_map,
        )
    )

    session.commit()

    print(
        "Marketing domain complete:"
    )

    print(
        f"  campaigns:   "
        f"{len(campaigns):,}"
    )

    print(
        f"  conversions: "
        f"{conversions:,}"
    )