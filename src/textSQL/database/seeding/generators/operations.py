from textSQL.database.models import Warehouse


WAREHOUSES = [
    ("Amman DC", "Jordan"),
    ("Riyadh DC", "Saudi Arabia"),
    ("Dubai DC", "UAE"),
    ("Jeddah DC", "Saudi Arabia"),
    ("Doha DC", "Qatar"),
]


def seed_warehouses(session):

    warehouses = [
        Warehouse(
            warehouse_name=name,
            location=location
        )
        for name, location in WAREHOUSES
    ]

    session.add_all(warehouses)

    session.commit()