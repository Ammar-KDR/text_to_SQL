from __future__ import annotations

from sqlalchemy import text


WAREHOUSE_CUTOFF = "2026-09-15"


def clear_warehouse(session):

    print("Clearing warehouse...")

    session.execute(
        text(
            """
            TRUNCATE TABLE
                warehouse.fact_sales,
                warehouse.fact_customer_activity,
                warehouse.fact_inventory_snapshot,
                warehouse.dim_campaign,
                warehouse.dim_category,
                warehouse.dim_product,
                warehouse.dim_customer,
                warehouse.dim_date
            RESTART IDENTITY CASCADE;
            """
        )
    )

    session.commit()


def load_dim_date(session):

    print("Loading dim_date...")

    session.execute(
        text(
            """
            INSERT INTO warehouse.dim_date (
                date_key,
                full_date,
                year,
                quarter,
                month,
                month_name,
                week,
                day
            )
            SELECT
                TO_CHAR(d, 'YYYYMMDD')::INTEGER,
                d::DATE,
                EXTRACT(YEAR FROM d)::INTEGER,
                EXTRACT(QUARTER FROM d)::INTEGER,
                EXTRACT(MONTH FROM d)::INTEGER,
                TO_CHAR(d, 'Month'),
                EXTRACT(WEEK FROM d)::INTEGER,
                EXTRACT(DAY FROM d)::INTEGER
            FROM generate_series(
                DATE '2024-01-01',
                DATE '2026-12-31',
                INTERVAL '1 day'
            ) AS d;
            """
        )
    )


def load_dim_customer(session):

    print("Loading dim_customer...")

    session.execute(
        text(
            """
            INSERT INTO warehouse.dim_customer (
                customer_id,
                first_name,
                last_name,
                country,
                customer_status,
                effective_start_date,
                effective_end_date,
                is_current
            )
            SELECT
                c.customer_id,
                c.first_name,
                c.last_name,

                COALESCE(
                    address.country,
                    'Unknown'
                ) AS country,

                c.customer_status,
                c.registered_at,
                NULL,
                TRUE

            FROM customers c

            LEFT JOIN LATERAL (
                SELECT ca.country
                FROM customer_addresses ca
                WHERE ca.customer_id = c.customer_id

                ORDER BY
                    CASE ca.address_type
                        WHEN 'shipping' THEN 1
                        WHEN 'home' THEN 2
                        WHEN 'billing' THEN 3
                        WHEN 'work' THEN 4
                        ELSE 5
                    END,
                    ca.address_id

                LIMIT 1
            ) address
            ON TRUE;
            """
        )
    )


def load_dim_category(session):

    print("Loading dim_category...")

    session.execute(
        text(
            """
            WITH RECURSIVE category_tree AS (

                SELECT
                    c.category_id,
                    c.category_name,
                    c.parent_category_id,

                    NULL::VARCHAR
                        AS parent_category_name,

                    c.category_name
                        AS top_level_category,

                    0
                        AS category_level

                FROM categories c

                WHERE c.parent_category_id IS NULL


                UNION ALL


                SELECT
                    child.category_id,
                    child.category_name,
                    child.parent_category_id,

                    parent.category_name
                        AS parent_category_name,

                    tree.top_level_category,

                    tree.category_level + 1

                FROM categories child

                JOIN category_tree tree
                    ON child.parent_category_id
                    = tree.category_id

                JOIN categories parent
                    ON parent.category_id
                    = child.parent_category_id
            )

            INSERT INTO warehouse.dim_category (
                category_id,
                category_name,
                parent_category_name,
                top_level_category,
                category_level
            )

            SELECT
                category_id,
                category_name,
                parent_category_name,
                top_level_category,
                category_level

            FROM category_tree;
            """
        )
    )


def load_dim_product(session):

    print("Loading dim_product...")

    session.execute(
        text(
            '''
            INSERT INTO warehouse.dim_product (
                product_id,
                variant_id,
                product_name,
                brand_name,
                sku,
                size,
                color
            )

            SELECT
                p.product_id,
                pv.variant_id,
                p.name,
                b.brand_name,
                pv.sku,
                pv.size,
                pv.color

            FROM products p

            JOIN brands b
                ON b.brand_id = p.brand_id

            JOIN product_variants pv
                ON pv.product_id = p.product_id;
            '''
        )
    )


def load_dim_campaign(session):

    print("Loading dim_campaign...")

    session.execute(
        text(
            """
            INSERT INTO warehouse.dim_campaign (
                campaign_id,
                campaign_name,
                campaign_type
            )

            SELECT
                campaign_id,
                campaign_name,
                campaign_type

            FROM campaigns;
            """
        )
    )


def load_dimensions(session):

    load_dim_date(session)
    load_dim_customer(session)
    load_dim_category(session)
    load_dim_product(session)
    load_dim_campaign(session)

    session.commit()

    print("Dimensions complete")

def load_fact_sales(session):

    print("Loading fact_sales...")

    session.execute(
        text(
            """
            WITH refund_totals AS (

                SELECT
                    p.order_id,
                    COALESCE(
                        SUM(r.refund_amount),
                        0
                    ) AS refunded_amount

                FROM payments p

                JOIN refunds r
                    ON r.payment_id = p.payment_id

                WHERE r.refund_status = 'completed'

                GROUP BY p.order_id
            ),

            sale_source AS (

                SELECT
                    o.order_id,
                    o.customer_id,
                    o.created_at,

                    oi.order_item_id,
                    oi.variant_id,
                    oi.quantity,
                    oi.unit_price,
                    oi.unit_cost,
                    oi.discount_amount,

                    pv.product_id,

                    COALESCE(
                        rt.refunded_amount,
                        0
                    ) AS refunded_amount,

                    CASE
                        WHEN o.total_amount > 0
                        THEN LEAST(
                            COALESCE(
                                rt.refunded_amount,
                                0
                            )
                            / o.total_amount,
                            1
                        )
                        ELSE 0
                    END AS refund_ratio

                FROM orders o

                JOIN order_items oi
                    ON oi.order_id = o.order_id

                JOIN product_variants pv
                    ON pv.variant_id
                    = oi.variant_id

                LEFT JOIN refund_totals rt
                    ON rt.order_id = o.order_id

                WHERE o.order_status IN (
                    'processing',
                    'shipped',
                    'delivered',
                    'refunded'
                )
            ),

            enriched AS (

                SELECT
                    s.*,

                    (
                        s.unit_price
                        * s.quantity
                        - s.discount_amount
                    )
                    * (
                        1 - s.refund_ratio
                    ) AS net_revenue,

                    (
                        s.unit_cost
                        * s.quantity
                    )
                    * (
                        1 - s.refund_ratio
                    ) AS net_cost

                FROM sale_source s
            )

            INSERT INTO warehouse.fact_sales (
                date_key,
                customer_key,
                product_key,
                category_key,
                campaign_key,
                order_id,
                quantity,
                revenue,
                cost,
                profit
            )

            SELECT
                TO_CHAR(
                    e.created_at,
                    'YYYYMMDD'
                )::INTEGER,

                dc.customer_key,

                dp.product_key,

                dcat.category_key,

                dcamp.campaign_key,

                e.order_id,

                e.quantity,

                ROUND(
                    e.net_revenue,
                    2
                ),

                ROUND(
                    e.net_cost,
                    2
                ),

                ROUND(
                    e.net_revenue
                    - e.net_cost,
                    2
                )

            FROM enriched e

            JOIN warehouse.dim_customer dc
                ON dc.customer_id
                = e.customer_id
                AND dc.is_current = TRUE

            JOIN warehouse.dim_product dp
                ON dp.variant_id
                = e.variant_id

            LEFT JOIN LATERAL (

                SELECT
                    pc.category_id

                FROM product_categories pc

                JOIN warehouse.dim_category cat
                    ON cat.category_id
                    = pc.category_id

                WHERE pc.product_id
                    = e.product_id

                ORDER BY
                    cat.category_level DESC,
                    pc.category_id

                LIMIT 1

            ) canonical_category
            ON TRUE

            LEFT JOIN warehouse.dim_category dcat
                ON dcat.category_id
                = canonical_category.category_id

            LEFT JOIN campaign_conversions cc
                ON cc.order_id = e.order_id

            LEFT JOIN warehouse.dim_campaign dcamp
                ON dcamp.campaign_id
                = cc.campaign_id;
            """
        )
    )

    session.commit()

    print("fact_sales complete")

def load_fact_customer_activity(session):

    print(
        "Loading fact_customer_activity..."
    )

    # ---------------------------------------
    # General customer events
    # ---------------------------------------

    session.execute(
        text(
            """
            INSERT INTO warehouse.fact_customer_activity (
                date_key,
                customer_key,
                product_key,
                campaign_key,
                activity_type,
                activity_count
            )

            SELECT
                TO_CHAR(
                    ce.timestamp,
                    'YYYYMMDD'
                )::INTEGER,

                dc.customer_key,

                NULL,

                NULL,

                ce.event_type,

                1

            FROM customer_events ce

            JOIN warehouse.dim_customer dc
                ON dc.customer_id
                = ce.customer_id
                AND dc.is_current = TRUE;
            """
        )
    )

    # ---------------------------------------
    # Marketing interactions
    # ---------------------------------------

    session.execute(
        text(
            """
            INSERT INTO warehouse.fact_customer_activity (
                date_key,
                customer_key,
                product_key,
                campaign_key,
                activity_type,
                activity_count
            )

            SELECT
                TO_CHAR(
                    cc.created_at,
                    'YYYYMMDD'
                )::INTEGER,

                dc.customer_key,

                NULL,

                dcamp.campaign_key,

                'campaign_' ||
                    cc.interaction_type,

                1

            FROM customer_campaigns cc

            JOIN warehouse.dim_customer dc
                ON dc.customer_id
                = cc.customer_id
                AND dc.is_current = TRUE

            JOIN warehouse.dim_campaign dcamp
                ON dcamp.campaign_id
                = cc.campaign_id;
            """
        )
    )

    # ---------------------------------------
    # Reviews
    # ---------------------------------------

    session.execute(
        text(
            """
            INSERT INTO warehouse.fact_customer_activity (
                date_key,
                customer_key,
                product_key,
                campaign_key,
                activity_type,
                activity_count
            )

            SELECT
                TO_CHAR(
                    r.created_at,
                    'YYYYMMDD'
                )::INTEGER,

                dc.customer_key,

                dp.product_key,

                NULL,

                'review',

                1

            FROM reviews r

            JOIN warehouse.dim_customer dc
                ON dc.customer_id
                = r.customer_id
                AND dc.is_current = TRUE

            JOIN order_items oi
                ON oi.order_item_id
                = r.order_item_id

            JOIN warehouse.dim_product dp
                ON dp.variant_id
                = oi.variant_id;
            """
        )
    )

    session.commit()

    print(
        "fact_customer_activity complete"
    )

def load_fact_inventory_snapshot(
    session,
):

    print(
        "Loading fact_inventory_snapshot..."
    )

    session.execute(
        text(
            """
            INSERT INTO warehouse.fact_inventory_snapshot (
                date_key,
                product_key,
                warehouse_id,
                quantity_on_hand,
                quantity_reserved
            )

            SELECT
                20260915,

                dp.product_key,

                i.warehouse_id,

                i.quantity_on_hand,

                i.quantity_reserved

            FROM inventory i

            JOIN warehouse.dim_product dp
                ON dp.variant_id
                = i.variant_id;
            """
        )
    )

    session.commit()

    print(
        "fact_inventory_snapshot complete"
    )

def build_warehouse(
    session,
    *,
    reset: bool = True,
):

    print(
        "Starting warehouse build..."
    )

    if reset:
        clear_warehouse(
            session
        )

    load_dimensions(
        session
    )

    load_fact_sales(
        session
    )

    load_fact_customer_activity(
        session
    )

    load_fact_inventory_snapshot(
        session
    )

    print(
        "Warehouse build complete"
    )