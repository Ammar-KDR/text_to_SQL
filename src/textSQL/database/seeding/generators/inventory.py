from __future__ import annotations

from datetime import datetime, timedelta
import random

from sqlalchemy import insert

from textSQL.database.models import (
    Warehouse,
    ProductVariant,
    Inventory,
    InventoryTransaction,
)


DATA_START = datetime(
    2024,
    1,
    1,
)

DATA_END = datetime(
    2026,
    9,
    15,
    23,
    59,
    59,
)


def random_datetime(
    start: datetime,
    end: datetime,
) -> datetime:

    seconds = int(
        (end - start).total_seconds()
    )

    return start + timedelta(
        seconds=random.randint(
            0,
            max(seconds, 0),
        )
    )


def generate_stock_level() -> int:

    stock_type = random.choices(
        [
            "normal",
            "low",
            "out",
        ],
        weights=[
            80,
            15,
            5,
        ],
        k=1,
    )[0]

    if stock_type == "out":
        return 0

    if stock_type == "low":
        return random.randint(
            1,
            8,
        )

    return random.randint(
        20,
        250,
    )


def split_quantity(
    quantity: int,
) -> list[int]:

    if quantity <= 0:
        return []

    if quantity < 20:
        return [quantity]

    transaction_count = random.choices(
        [1, 2, 3],
        weights=[25, 50, 25],
        k=1,
    )[0]

    transaction_count = min(
        transaction_count,
        quantity,
    )

    if transaction_count == 1:
        return [quantity]

    cut_points = sorted(
        random.sample(
            range(1, quantity),
            k=transaction_count - 1,
        )
    )

    parts = []

    previous = 0

    for point in cut_points:
        parts.append(
            point - previous
        )
        previous = point

    parts.append(
        quantity - previous
    )

    return parts


def seed_inventory(
    session,
):

    warehouses = (
        session.query(Warehouse)
        .order_by(Warehouse.warehouse_id)
        .all()
    )

    variants = (
        session.query(ProductVariant)
        .order_by(ProductVariant.variant_id)
        .all()
    )

    if not warehouses:
        raise RuntimeError(
            "No warehouses found."
        )

    if not variants:
        raise RuntimeError(
            "No product variants found."
        )

    print(
        f"Creating inventory for "
        f"{len(variants):,} variants..."
    )

    inventory_rows = []
    transaction_rows = []

    for variant in variants:

        maximum = min(
            len(warehouses),
            5,
        )

        minimum = min(
            2,
            maximum,
        )

        warehouse_count = (
            random.randint(
                minimum,
                maximum,
            )
        )

        selected_warehouses = (
            random.sample(
                warehouses,
                k=warehouse_count,
            )
        )

        for warehouse in (
            selected_warehouses
        ):

            quantity_on_hand = (
                generate_stock_level()
            )

            # Reserved stock will later be driven by
            # actual pending orders rather than random
            # unrelated values.
            quantity_reserved = 0

            inventory_rows.append(
                {
                    "warehouse_id":
                        warehouse.warehouse_id,

                    "variant_id":
                        variant.variant_id,

                    "quantity_on_hand":
                        quantity_on_hand,

                    "quantity_reserved":
                        quantity_reserved,
                }
            )

            # Baseline inventory history.
            # The sum of these positive transactions
            # exactly equals current quantity_on_hand.
            parts = split_quantity(
                quantity_on_hand
            )

            transaction_date = (
                DATA_START
                - timedelta(
                    days=random.randint(
                        1,
                        45,
                    )
                )
            )

            for index, quantity in enumerate(
                parts
            ):

                if index == 0:
                    transaction_type = (
                        "opening_stock"
                    )
                else:
                    transaction_type = (
                        "restock"
                    )

                transaction_rows.append(
                    {
                        "warehouse_id":
                            warehouse.warehouse_id,

                        "variant_id":
                            variant.variant_id,

                        "transaction_type":
                            transaction_type,

                        "quantity_change":
                            quantity,

                        "created_at":
                            transaction_date,
                    }
                )

                transaction_date = (
                    random_datetime(
                        max(
                            transaction_date,
                            DATA_START,
                        ),
                        DATA_END,
                    )
                )

    batch_size = 10_000

    print(
        f"Inserting "
        f"{len(inventory_rows):,} "
        f"inventory records..."
    )

    for start in range(
        0,
        len(inventory_rows),
        batch_size,
    ):

        session.execute(
            insert(
                Inventory.__table__
            ),
            inventory_rows[
                start:
                start + batch_size
            ],
        )

    print(
        f"Inserting "
        f"{len(transaction_rows):,} "
        f"inventory transactions..."
    )

    for start in range(
        0,
        len(transaction_rows),
        batch_size,
    ):

        session.execute(
            insert(
                InventoryTransaction
                .__table__
            ),
            transaction_rows[
                start:
                start + batch_size
            ],
        )

    session.commit()

    print(
        "Inventory domain complete:"
    )

    print(
        f"  inventory records: "
        f"{len(inventory_rows):,}"
    )

    print(
        f"  transactions: "
        f"{len(transaction_rows):,}"
    )