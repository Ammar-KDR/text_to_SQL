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
    ]

    for table in tables:
        session.execute(
            text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")
        )

    session.commit()