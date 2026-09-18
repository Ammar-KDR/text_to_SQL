from sqlalchemy import text


def clear_database(session):

    tables = [
        "role_permissions",
        "user_roles",
        "permissions",
        "roles",

        "customer_addresses",
        "customer_events",
        "customers",
        "users",

        "product_categories",
        "product_variants",
        "products",
        "categories",
        "brands",

        "warehouses",
        "inventory_transactions",
        "inventory",
        "campaign_conversions",
        "customer_campaigns",
        "campaign_products",
        "campaigns",
        "reviews",

    ]

    for table in tables:
        session.execute(
            text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")
        )

    session.commit()