from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from itertools import accumulate
import random
import uuid

from sqlalchemy import insert

from textSQL.database.models import (
    Customer,
    CustomerAddress,
    ProductVariant,
    Inventory,
    InventoryTransaction,

    Order,
    OrderItem,
    OrderStatusHistory,

    PaymentMethod,
    Payment,
    Refund,

    ShippingMethod,
    Shipment,
    ShipmentItem,
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


TAX_RATES = {
    "Jordan": Decimal("0.16"),
    "Saudi Arabia": Decimal("0.15"),
    "UAE": Decimal("0.05"),
    "Kuwait": Decimal("0.00"),
    "Qatar": Decimal("0.00"),
}


def money(value) -> Decimal:

    return Decimal(value).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def random_datetime_between(
    start: datetime,
    end: datetime,
    *,
    recent_bias: bool = False,
):

    if start >= end:
        return start

    start_ts = start.timestamp()
    end_ts = end.timestamp()

    if recent_bias:

        value = random.triangular(
            start_ts,
            end_ts,
            end_ts,
        )

    else:

        value = random.uniform(
            start_ts,
            end_ts,
        )

    return datetime.fromtimestamp(
        value
    )


def choose_order_status(
    created_at: datetime,
) -> str:

    age_days = (
        DATA_END - created_at
    ).days

    if age_days <= 1:

        return random.choices(
            [
                "pending",
                "processing",
                "shipped",
                "cancelled",
                "delivered",
            ],
            weights=[
                35,
                40,
                15,
                5,
                5,
            ],
            k=1,
        )[0]

    if age_days <= 5:

        return random.choices(
            [
                "processing",
                "shipped",
                "delivered",
                "cancelled",
                "refunded",
            ],
            weights=[
                20,
                35,
                35,
                7,
                3,
            ],
            k=1,
        )[0]

    if age_days <= 14:

        return random.choices(
            [
                "shipped",
                "delivered",
                "cancelled",
                "refunded",
            ],
            weights=[
                10,
                75,
                8,
                7,
            ],
            k=1,
        )[0]

    return random.choices(
        [
            "delivered",
            "cancelled",
            "refunded",
        ],
        weights=[
            88,
            7,
            5,
        ],
        k=1,
    )[0]


def order_item_count():

    return random.choices(
        [1, 2, 3, 4, 5, 6],
        weights=[
            20,
            25,
            25,
            15,
            10,
            5,
        ],
        k=1,
    )[0]


def item_quantity():

    return random.choices(
        [1, 2, 3, 4],
        weights=[
            78,
            17,
            4,
            1,
        ],
        k=1,
    )[0]


def payment_method_name(
    country: str,
):

    if country == "Saudi Arabia":

        return random.choices(
            [
                "Visa",
                "Mastercard",
                "Apple Pay",
                "Mada",
                "Cash on Delivery",
            ],
            weights=[
                24,
                20,
                20,
                28,
                8,
            ],
            k=1,
        )[0]

    return random.choices(
        [
            "Visa",
            "Mastercard",
            "Apple Pay",
            "Cash on Delivery",
            "Bank Transfer",
        ],
        weights=[
            33,
            27,
            17,
            17,
            6,
        ],
        k=1,
    )[0]


def historical_price(
    current_price: Decimal,
) -> Decimal:

    factor = Decimal(
        str(
            random.uniform(
                0.90,
                1.08,
            )
        )
    )

    return money(
        current_price * factor
    )


def unit_cost(
    price: Decimal,
) -> Decimal:

    # Gross margin varies by product.
    cost_ratio = Decimal(
        str(
            random.uniform(
                0.48,
                0.78,
            )
        )
    )

    return money(
        price * cost_ratio
    )


def discount_rate():

    return Decimal(
        str(
            random.choices(
                [
                    0,
                    0.05,
                    0.10,
                    0.15,
                    0.20,
                ],
                weights=[
                    60,
                    15,
                    12,
                    8,
                    5,
                ],
                k=1,
            )[0]
        )
    )


def shipping_amount(
    merchandise_after_discount: Decimal,
):

    if merchandise_after_discount >= Decimal(
        "150.00"
    ):
        return Decimal("0.00")

    return random.choice(
        [
            Decimal("4.99"),
            Decimal("6.99"),
            Decimal("9.99"),
        ]
    )


def build_status_timeline(
    created_at: datetime,
    final_status: str,
):

    rows = [
        (
            "pending",
            created_at,
        )
    ]

    if final_status == "pending":
        return rows

    if final_status == "cancelled":

        cancel_time = min(
            created_at
            + timedelta(
                hours=random.randint(
                    1,
                    48,
                )
            ),
            DATA_END,
        )

        rows.append(
            (
                "cancelled",
                cancel_time,
            )
        )

        return rows

    processing_at = min(
        created_at
        + timedelta(
            hours=random.randint(
                1,
                24,
            )
        ),
        DATA_END,
    )

    rows.append(
        (
            "processing",
            processing_at,
        )
    )

    if final_status == "processing":
        return rows

    shipped_at = min(
        processing_at
        + timedelta(
            hours=random.randint(
                12,
                72,
            )
        ),
        DATA_END,
    )

    rows.append(
        (
            "shipped",
            shipped_at,
        )
    )

    if final_status == "shipped":
        return rows

    delivered_at = min(
        shipped_at
        + timedelta(
            days=random.randint(
                1,
                5,
            )
        ),
        DATA_END,
    )

    rows.append(
        (
            "delivered",
            delivered_at,
        )
    )

    if final_status == "delivered":
        return rows

    refunded_at = min(
        delivered_at
        + timedelta(
            days=random.randint(
                1,
                14,
            )
        ),
        DATA_END,
    )

    rows.append(
        (
            "refunded",
            refunded_at,
        )
    )

    return rows


def prepare_customer_data(
    session,
):

    customers = (
        session.query(
            Customer.customer_id,
            Customer.customer_status,
            Customer.registered_at,
        )
        .all()
    )

    addresses = (
        session.query(
            CustomerAddress.customer_id,
            CustomerAddress.country,
        )
        .order_by(
            CustomerAddress.address_id
        )
        .all()
    )

    country_by_customer = {}

    for customer_id, country in addresses:

        if customer_id not in (
            country_by_customer
        ):

            country_by_customer[
                customer_id
            ] = country

    buyer_ids = []
    buyer_weights = []
    registration = {}

    for customer in customers:

        customer_id = (
            customer.customer_id
        )

        if customer_id not in (
            country_by_customer
        ):
            continue

        registration[
            customer_id
        ] = customer.registered_at

        if (
            customer.customer_status
            == "active"
        ):
            weight = random.uniform(
                1.0,
                8.0,
            )

        elif (
            customer.customer_status
            == "inactive"
        ):
            weight = random.uniform(
                0.15,
                1.0,
            )

        else:
            weight = random.uniform(
                0.01,
                0.10,
            )

        # Heavy-tail purchasing behavior.
        weight *= random.paretovariate(
            2.5
        )

        buyer_ids.append(
            customer_id
        )

        buyer_weights.append(
            weight
        )

    return (
        buyer_ids,
        list(
            accumulate(
                buyer_weights
            )
        ),
        registration,
        country_by_customer,
    )


def prepare_variant_data(
    session,
):

    variants = (
        session.query(
            ProductVariant.variant_id,
            ProductVariant.price,
        )
        .all()
    )

    variant_prices = {
        variant.variant_id:
            Decimal(
                str(variant.price)
            )
        for variant in variants
    }

    # Keep some catalog items with no sales.
    active_variants = [
        variant.variant_id
        for variant in variants
        if random.random() < 0.88
    ]

    popularity = [
        random.paretovariate(2.0)
        for _ in active_variants
    ]

    cumulative = list(
        accumulate(
            popularity
        )
    )

    return (
        active_variants,
        cumulative,
        variant_prices,
    )


def prepare_inventory(
    session,
):

    rows = (
        session.query(
            Inventory.inventory_id,
            Inventory.warehouse_id,
            Inventory.variant_id,
            Inventory.quantity_on_hand,
            Inventory.quantity_reserved,
        )
        .all()
    )

    inventory_state = {}

    by_variant = defaultdict(
        list
    )

    for row in rows:

        state = {
            "inventory_id":
                row.inventory_id,

            "warehouse_id":
                row.warehouse_id,

            "variant_id":
                row.variant_id,

            "quantity_on_hand":
                row.quantity_on_hand,

            "quantity_reserved":
                row.quantity_reserved,
        }

        inventory_state[
            row.inventory_id
        ] = state

        by_variant[
            row.variant_id
        ].append(
            state
        )

    return (
        inventory_state,
        by_variant,
    )


def choose_stock_location(
    variant_id,
    quantity,
    inventory_by_variant,
):

    candidates = []

    for stock in inventory_by_variant[
        variant_id
    ]:

        available = (
            stock["quantity_on_hand"]
            - stock["quantity_reserved"]
        )

        if available >= quantity:

            candidates.append(
                stock
            )

    if not candidates:
        return None

    return max(
        candidates,
        key=lambda row:
            row["quantity_on_hand"]
            - row[
                "quantity_reserved"
            ],
    )


def select_variant(
    variant_ids,
    variant_cumulative,
    inventory_by_variant,
    quantity,
):

    for _ in range(25):

        variant_id = random.choices(
            variant_ids,
            cum_weights=
                variant_cumulative,
            k=1,
        )[0]

        stock = choose_stock_location(
            variant_id,
            quantity,
            inventory_by_variant,
        )

        if stock is not None:
            return variant_id, stock

    raise RuntimeError(
        "Could not find sufficient inventory."
    )


def seed_orders(
    session,
    order_count: int,
    *,
    batch_size: int = 2_500,
):

    print(
        "Preparing commerce state..."
    )

    (
        buyer_ids,
        buyer_cumulative,
        registration,
        country_by_customer,
    ) = prepare_customer_data(
        session
    )

    (
        variant_ids,
        variant_cumulative,
        variant_prices,
    ) = prepare_variant_data(
        session
    )

    (
        inventory_state,
        inventory_by_variant,
    ) = prepare_inventory(
        session
    )

    payment_methods = {
        row.method_name:
            row.payment_method_id
        for row in (
            session.query(
                PaymentMethod
            ).all()
        )
    }

    shipping_methods = [
        row.shipping_method_id
        for row in (
            session.query(
                ShippingMethod
            ).all()
        )
    ]

    if not payment_methods:
        raise RuntimeError(
            "Payment methods missing."
        )

    if not shipping_methods:
        raise RuntimeError(
            "Shipping methods missing."
        )

    last_order_date = {}

    total_items = 0
    total_payments = 0
    total_refunds = 0
    total_shipments = 0

    inventory_transactions = []

    print(
        f"Creating {order_count:,} orders..."
    )

    for batch_start in range(
        0,
        order_count,
        batch_size,
    ):

        current_batch_size = min(
            batch_size,
            order_count
            - batch_start,
        )

        order_rows = []
        order_metadata = []

        # ------------------------------------------
        # Generate orders and their line specs
        # ------------------------------------------

        for _ in range(
            current_batch_size
        ):

            customer_id = random.choices(
                buyer_ids,
                cum_weights=
                    buyer_cumulative,
                k=1,
            )[0]

            country = (
                country_by_customer[
                    customer_id
                ]
            )

            registered_at = (
                registration[
                    customer_id
                ]
            )

            created_at = (
                random_datetime_between(
                    max(
                        registered_at,
                        DATA_START,
                    ),
                    DATA_END,
                    recent_bias=(
                        random.random()
                        < 0.30
                    ),
                )
            )

            final_status = (
                choose_order_status(
                    created_at
                )
            )

            item_specs = []

            used_variants = set()

            subtotal = Decimal(
                "0.00"
            )

            total_discount = Decimal(
                "0.00"
            )

            total_tax = Decimal(
                "0.00"
            )

            tax_rate = TAX_RATES.get(
                country,
                Decimal("0.00"),
            )

            requested_items = (
                order_item_count()
            )

            for _ in range(
                requested_items
            ):

                quantity = (
                    item_quantity()
                )

                for _attempt in range(
                    20
                ):

                    (
                        variant_id,
                        stock,
                    ) = select_variant(
                        variant_ids,
                        variant_cumulative,
                        inventory_by_variant,
                        quantity,
                    )

                    if variant_id not in (
                        used_variants
                    ):
                        break

                    # end of retry loop

                if final_status == "processing":
                    stock["quantity_reserved"] += quantity

                elif final_status in {
                        "shipped",
                        "delivered",
                        "refunded",
                    }:
                    stock["quantity_on_hand"] -= quantity

                used_variants.add(
                        variant_id
                    )

                

                price = historical_price(
                    variant_prices[
                        variant_id
                    ]
                )

                cost = unit_cost(
                    price
                )

                gross = money(
                    price * quantity
                )

                discount = money(
                    gross
                    * discount_rate()
                )

                taxable = (
                    gross - discount
                )

                tax = money(
                    taxable
                    * tax_rate
                )

                line_total = money(
                    taxable + tax
                )

                subtotal += gross
                total_discount += (
                    discount
                )
                total_tax += tax

                item_specs.append(
                    {
                        "variant_id":
                            variant_id,

                        "quantity":
                            quantity,

                        "unit_price":
                            price,

                        "unit_cost":
                            cost,

                        "discount_amount":
                            discount,

                        "tax_amount":
                            tax,

                        "line_total":
                            line_total,

                        "stock":
                            stock,
                    }
                )

            merchandise = (
                subtotal
                - total_discount
            )

            shipping = (
                shipping_amount(
                    merchandise
                )
            )

            total = money(
                merchandise
                + total_tax
                + shipping
            )

            order_rows.append(
                {
                    "customer_id":
                        customer_id,

                    "order_status":
                        final_status,

                    "subtotal_amount":
                        money(subtotal),

                    "discount_amount":
                        money(
                            total_discount
                        ),

                    "shipping_amount":
                        shipping,

                    "tax_amount":
                        money(total_tax),

                    "total_amount":
                        total,

                    "created_at":
                        created_at,
                }
            )

            order_metadata.append(
                {
                    "customer_id":
                        customer_id,

                    "country":
                        country,

                    "created_at":
                        created_at,

                    "status":
                        final_status,

                    "total":
                        total,

                    "items":
                        item_specs,
                }
            )

        # ------------------------------------------
        # Insert orders
        # ------------------------------------------

        order_result = (
            session.execute(
                insert(
                    Order
                )
                .returning(
                    Order.order_id,
                    sort_by_parameter_order=True,
                ),
                order_rows,
            )
        )

        order_ids = (
            order_result
            .scalars()
            .all()
        )

        # ------------------------------------------
        # Build order items
        # ------------------------------------------

        item_rows = []
        item_metadata = []

        for order_id, meta in zip(
            order_ids,
            order_metadata,
        ):

            meta["order_id"] = (
                order_id
            )

            current_last = (
                last_order_date.get(
                    meta[
                        "customer_id"
                    ]
                )
            )

            if (
                current_last is None
                or meta["created_at"]
                > current_last
            ):
                last_order_date[
                    meta["customer_id"]
                ] = meta[
                    "created_at"
                ]

            for item in meta["items"]:

                item_rows.append(
                    {
                        "order_id":
                            order_id,

                        "variant_id":
                            item[
                                "variant_id"
                            ],

                        "quantity":
                            item[
                                "quantity"
                            ],

                        "unit_price":
                            item[
                                "unit_price"
                            ],

                        "unit_cost":
                            item[
                                "unit_cost"
                            ],

                        "discount_amount":
                            item[
                                "discount_amount"
                            ],

                        "tax_amount":
                            item[
                                "tax_amount"
                            ],

                        "line_total":
                            item[
                                "line_total"
                            ],
                    }
                )

                item_metadata.append(
                    {
                        "order_id":
                            order_id,

                        "order":
                            meta,

                        **item,
                    }
                )

        item_result = (
            session.execute(
                insert(
                    OrderItem
                )
                .returning(
                    OrderItem.order_item_id,
                    sort_by_parameter_order=True,
                ),
                item_rows,
            )
        )

        item_ids = (
            item_result
            .scalars()
            .all()
        )

        for item_id, meta in zip(
            item_ids,
            item_metadata,
        ):

            meta["order_item_id"] = (
                item_id
            )

        total_items += len(
            item_rows
        )

        # ------------------------------------------
        # Status history
        # ------------------------------------------

        status_rows = []

        timelines = {}

        for meta in order_metadata:

            timeline = (
                build_status_timeline(
                    meta["created_at"],
                    meta["status"],
                )
            )

            timelines[
                meta["order_id"]
            ] = timeline

            for status, changed_at in (
                timeline
            ):

                status_rows.append(
                    {
                        "order_id":
                            meta["order_id"],

                        "status":
                            status,

                        "changed_at":
                            changed_at,
                    }
                )

        session.execute(
            insert(
                OrderStatusHistory
            ),
            status_rows,
        )

        # ------------------------------------------
        # Payments
        # ------------------------------------------

        payment_rows = []
        payment_meta = []

        for meta in order_metadata:

            method_name = (
                payment_method_name(
                    meta["country"]
                )
            )

            method_id = (
                payment_methods[
                    method_name
                ]
            )

            status = meta["status"]

            # Some successful orders had a
            # failed attempt first.
            successful_order = (
                status
                in {
                    "processing",
                    "shipped",
                    "delivered",
                    "refunded",
                }
            )

            if (
                successful_order
                and random.random()
                < 0.08
            ):

                payment_rows.append(
                    {
                        "order_id":
                            meta["order_id"],

                        "payment_method_id":
                            method_id,

                        "amount":
                            meta["total"],

                        "payment_status":
                            "failed",

                        "attempted_at":
                            meta["created_at"]
                            + timedelta(
                                minutes=random.randint(
                                    1,
                                    20,
                                )
                            ),

                        "completed_at":
                            None,

                        "transaction_reference":
                            None,
                    }
                )

                payment_meta.append(
                    {
                        "order":
                            meta,

                        "successful":
                            False,

                        "needs_refund":
                            False,
                    }
                )

            if successful_order:

                attempted_at = (
                    meta["created_at"]
                    + timedelta(
                        minutes=random.randint(
                            1,
                            60,
                        )
                    )
                )

                completed_at = (
                    attempted_at
                    + timedelta(
                        minutes=random.randint(
                            0,
                            10,
                        )
                    )
                )

                payment_rows.append(
                    {
                        "order_id":
                            meta["order_id"],

                        "payment_method_id":
                            method_id,

                        "amount":
                            meta["total"],

                        "payment_status":
                            "completed",

                        "attempted_at":
                            attempted_at,

                        "completed_at":
                            completed_at,

                        "transaction_reference":
                            "TXN-"
                            + uuid.uuid4().hex[
                                :20
                            ].upper(),
                    }
                )

                payment_meta.append(
                    {
                        "order":
                            meta,

                        "successful":
                            True,

                        "needs_refund":
                            (
                                status
                                == "refunded"
                            ),
                    }
                )

            elif status == "pending":

                payment_rows.append(
                    {
                        "order_id":
                            meta["order_id"],

                        "payment_method_id":
                            method_id,

                        "amount":
                            meta["total"],

                        "payment_status":
                            "pending",

                        "attempted_at":
                            meta["created_at"],

                        "completed_at":
                            None,

                        "transaction_reference":
                            None,
                    }
                )

                payment_meta.append(
                    {
                        "order":
                            meta,

                        "successful":
                            False,

                        "needs_refund":
                            False,
                    }
                )

            elif status == "cancelled":

                # Most cancelled orders never
                # completed payment.
                if random.random() < 0.75:

                    payment_rows.append(
                        {
                            "order_id":
                                meta["order_id"],

                            "payment_method_id":
                                method_id,

                            "amount":
                                meta["total"],

                            "payment_status":
                                "failed",

                            "attempted_at":
                                meta[
                                    "created_at"
                                ],

                            "completed_at":
                                None,

                            "transaction_reference":
                                None,
                        }
                    )

                    payment_meta.append(
                        {
                            "order":
                                meta,

                            "successful":
                                False,

                            "needs_refund":
                                False,
                        }
                    )

                else:

                    payment_rows.append(
                        {
                            "order_id":
                                meta["order_id"],

                            "payment_method_id":
                                method_id,

                            "amount":
                                meta["total"],

                            "payment_status":
                                "completed",

                            "attempted_at":
                                meta[
                                    "created_at"
                                ],

                            "completed_at":
                                meta[
                                    "created_at"
                                ]
                                + timedelta(
                                    minutes=5
                                ),

                            "transaction_reference":
                                "TXN-"
                                + uuid.uuid4()
                                .hex[:20]
                                .upper(),
                        }
                    )

                    payment_meta.append(
                        {
                            "order":
                                meta,

                            "successful":
                                True,

                            "needs_refund":
                                True,
                        }
                    )

        payment_result = (
            session.execute(
                insert(
                    Payment
                )
                .returning(
                    Payment.payment_id,
                    sort_by_parameter_order=True,
                ),
                payment_rows,
            )
        )

        payment_ids = (
            payment_result
            .scalars()
            .all()
        )

        total_payments += len(
            payment_rows
        )

        # ------------------------------------------
        # Refunds
        # ------------------------------------------

        refund_rows = []

        for payment_id, meta in zip(
            payment_ids,
            payment_meta,
        ):

            if not meta[
                "needs_refund"
            ]:
                continue

            order_meta = (
                meta["order"]
            )

            if (
                order_meta["status"]
                == "cancelled"
            ):

                refund_amount = (
                    order_meta[
                        "total"
                    ]
                )

                reason = (
                    "order_cancelled"
                )

            else:

                if random.random() < 0.65:

                    refund_amount = (
                        order_meta[
                            "total"
                        ]
                    )

                    reason = (
                        "full_return"
                    )

                else:

                    refund_amount = money(
                        order_meta[
                            "total"
                        ]
                        * Decimal(
                            str(
                                random.uniform(
                                    0.20,
                                    0.70,
                                )
                            )
                        )
                    )

                    reason = (
                        "partial_return"
                    )

            refund_time = (
                timelines[
                    order_meta[
                        "order_id"
                    ]
                ][-1][1]
            )

            refund_rows.append(
                {
                    "payment_id":
                        payment_id,

                    "refund_amount":
                        refund_amount,

                    "refund_status":
                        "completed",

                    "reason":
                        reason,

                    "created_at":
                        refund_time,
                }
            )

        if refund_rows:

            session.execute(
                insert(
                    Refund
                ),
                refund_rows,
            )

        total_refunds += len(
            refund_rows
        )

        # ------------------------------------------
        # Shipments + inventory movement
        # ------------------------------------------

        shipment_rows = []
        shipment_meta = []

        items_by_order = defaultdict(
            list
        )

        for item in item_metadata:

            items_by_order[
                item["order_id"]
            ].append(
                item
            )

        for meta in order_metadata:

            status = meta["status"]

            if status in {
                "pending",
                "cancelled",
            }:
                continue

            timeline = timelines[
                meta["order_id"]
            ]

            timeline_map = {
                status_name:
                    timestamp
                for (
                    status_name,
                    timestamp
                ) in timeline
            }

            grouped = defaultdict(
                list
            )

            for item in items_by_order[
                meta["order_id"]
            ]:

                stock = item["stock"]

                grouped[
                    stock[
                        "warehouse_id"
                    ]
                ].append(
                    item
                )

            for warehouse_id, items in (
                grouped.items()
            ):

                shipment_status = (
                    status
                )

                if status == "refunded":
                    shipment_status = (
                        "delivered"
                    )

                shipped_at = (
                    timeline_map.get(
                        "shipped"
                    )
                )

                delivered_at = (
                    timeline_map.get(
                        "delivered"
                    )
                )

                shipment_rows.append(
                    {
                        "order_id":
                            meta["order_id"],

                        "warehouse_id":
                            warehouse_id,

                        "shipping_method_id":
                            random.choice(
                                shipping_methods
                            ),

                        "tracking_number":
                            "TRK-"
                            + uuid.uuid4()
                            .hex[:16]
                            .upper(),

                        "shipment_status":
                            shipment_status,

                        "shipped_at":
                            shipped_at,

                        "delivered_at":
                            delivered_at,
                    }
                )

                shipment_meta.append(
                    {
                        "order":
                            meta,

                        "items":
                            items,

                        "shipped_at":
                            shipped_at,

                        "delivered_at":
                            delivered_at,
                    }
                )

        if shipment_rows:

            shipment_result = (
                session.execute(
                    insert(
                        Shipment
                    )
                    .returning(
                        Shipment.shipment_id,
                        sort_by_parameter_order=True,
                    ),
                    shipment_rows,
                )
            )

            shipment_ids = (
                shipment_result
                .scalars()
                .all()
            )

            shipment_item_rows = []

            for shipment_id, meta in zip(
                shipment_ids,
                shipment_meta,
            ):

                order_meta = (
                    meta["order"]
                )

                status = (
                    order_meta["status"]
                )

                for item in meta[
                    "items"
                ]:

                    shipment_item_rows.append(
                        {
                            "shipment_id":
                                shipment_id,

                            "order_item_id":
                                item[
                                    "order_item_id"
                                ],

                            "quantity":
                                item[
                                    "quantity"
                                ],
                        }
                    )

                    stock = (
                        item["stock"]
                    )

                    quantity = (
                        item["quantity"]
                    )

                    if status in {
                        "shipped",
                        "delivered",
                        "refunded",
                    }:

                        inventory_transactions.append(
                            {
                                "warehouse_id":
                                    stock[
                                        "warehouse_id"
                                    ],

                                "variant_id":
                                    stock[
                                        "variant_id"
                                    ],

                                "transaction_type":
                                    "sale",

                                "quantity_change":
                                    -quantity,

                                "created_at":
                                    meta[
                                        "shipped_at"
                                    ]
                                    or order_meta[
                                        "created_at"
                                    ],
                            }
                        )

                        # Most returned merchandise
                        # can be placed back into stock.
                        if (
                            status
                            == "refunded"
                            and random.random()
                            < 0.70
                        ):

                            stock[
                                "quantity_on_hand"
                            ] += quantity

                            inventory_transactions.append(
                                {
                                    "warehouse_id":
                                        stock[
                                            "warehouse_id"
                                        ],

                                    "variant_id":
                                        stock[
                                            "variant_id"
                                        ],

                                    "transaction_type":
                                        "return_restock",

                                    "quantity_change":
                                        quantity,

                                    "created_at":
                                        timelines[
                                            order_meta[
                                                "order_id"
                                            ]
                                        ][-1][1],
                                }
                            )

            session.execute(
                insert(
                    ShipmentItem
                ),
                shipment_item_rows,
            )

            total_shipments += len(
                shipment_rows
            )

        # ------------------------------------------
        # Inventory transaction batches
        # ------------------------------------------

        if len(
            inventory_transactions
        ) >= 10_000:

            session.execute(
                insert(
                    InventoryTransaction
                ),
                inventory_transactions,
            )

            inventory_transactions.clear()

        session.flush()

        completed = min(
            batch_start
            + current_batch_size,
            order_count,
        )

        print(
            f"  {completed:,} / "
            f"{order_count:,} orders"
        )

    # ----------------------------------------------
    # Remaining inventory transactions
    # ----------------------------------------------

    if inventory_transactions:

        session.execute(
            insert(
                InventoryTransaction
            ),
            inventory_transactions,
        )

    # ----------------------------------------------
    # Persist final inventory state
    # ----------------------------------------------

    session.bulk_update_mappings(
        Inventory,
        [
            {
                "inventory_id":
                    state[
                        "inventory_id"
                    ],

                "quantity_on_hand":
                    state[
                        "quantity_on_hand"
                    ],

                "quantity_reserved":
                    state[
                        "quantity_reserved"
                    ],
            }

            for state
            in inventory_state.values()
        ],
    )

    # ----------------------------------------------
    # Derived customer.last_order_date
    # ----------------------------------------------

    session.bulk_update_mappings(
        Customer,
        [
            {
                "customer_id":
                    customer_id,

                "last_order_date":
                    date,
            }

            for (
                customer_id,
                date
            )
            in last_order_date.items()
        ],
    )

    session.commit()

    print(
        "Transactional domain complete:"
    )

    print(
        f"  orders:    "
        f"{order_count:,}"
    )

    print(
        f"  items:     "
        f"{total_items:,}"
    )

    print(
        f"  payments:  "
        f"{total_payments:,}"
    )

    print(
        f"  refunds:   "
        f"{total_refunds:,}"
    )

    print(
        f"  shipments: "
        f"{total_shipments:,}"
    )