from __future__ import annotations

from datetime import timedelta
import random

from sqlalchemy import insert, select

from textSQL.database.models import (
    Order,
    OrderItem,
    ProductVariant,
    Shipment,
    ShipmentItem,
    Review,
)


RATING_DISTRIBUTION = [
    (5, 0.50),
    (4, 0.30),
    (3, 0.15),
    (2, 0.04),
    (1, 0.01),
]


COMMENTS = {
    5: [
        "Excellent product and very satisfied with the purchase.",
        "Great quality and exactly what I expected.",
        "Very happy with this product.",
        "Excellent value for money.",
        "Would definitely purchase again.",
    ],

    4: [
        "Good product overall.",
        "Very good quality with minor issues.",
        "Satisfied with the purchase.",
        "Good value and works as expected.",
        "Overall a positive experience.",
    ],

    3: [
        "Average product, but acceptable.",
        "Works as expected but nothing exceptional.",
        "The product is fine for the price.",
        "Some aspects could be improved.",
        "Decent overall experience.",
    ],

    2: [
        "The product did not fully meet expectations.",
        "Quality could be significantly better.",
        "Several issues affected the experience.",
        "Not very satisfied with the purchase.",
    ],

    1: [
        "Very disappointed with the product.",
        "The product did not meet expectations.",
        "Poor overall experience.",
        "Would not purchase this product again.",
    ],
}


def weighted_rating():

    ratings = [
        value
        for value, _
        in RATING_DISTRIBUTION
    ]

    weights = [
        weight
        for _, weight
        in RATING_DISTRIBUTION
    ]

    return random.choices(
        ratings,
        weights=weights,
        k=1,
    )[0]


def seed_reviews(
    session,
    target_count: int,
):

    print(
        f"Preparing up to "
        f"{target_count:,} reviews..."
    )

    eligible = (
        session.execute(
            select(
                Order.customer_id,
                OrderItem.order_item_id,
                ProductVariant.product_id,
                Shipment.delivered_at,
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
            .join(
                ShipmentItem,
                ShipmentItem.order_item_id
                == OrderItem.order_item_id,
            )
            .join(
                Shipment,
                Shipment.shipment_id
                == ShipmentItem.shipment_id,
            )
            .where(
                Shipment.delivered_at
                .is_not(None)
            )
            .where(
                Order.order_status.in_(
                    [
                        "delivered",
                        "refunded",
                    ]
                )
            )
            .distinct()
        )
        .all()
    )

    if not eligible:

        raise RuntimeError(
            "No delivered order items "
            "available for reviews."
        )

    sample_size = min(
        target_count,
        len(eligible),
    )

    selected = random.sample(
        eligible,
        k=sample_size,
    )

    rows = []

    for (
        customer_id,
        order_item_id,
        product_id,
        delivered_at,
    ) in selected:

        rating = weighted_rating()

        # Not every user leaves written text.
        if random.random() < 0.72:
            comment = random.choice(
                COMMENTS[rating]
            )
        else:
            comment = None

        created_at = (
            delivered_at
            + timedelta(
                days=random.randint(
                    1,
                    30,
                )
            )
        )

        rows.append(
            {
                "customer_id":
                    customer_id,

                "product_id":
                    product_id,

                "order_item_id":
                    order_item_id,

                "rating":
                    rating,

                "comment":
                    comment,

                "created_at":
                    created_at,
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
                Review
            ),
            rows[
                start:
                start + batch_size
            ],
        )

    session.commit()

    print(
        f"Reviews complete: "
        f"{len(rows):,}"
    )