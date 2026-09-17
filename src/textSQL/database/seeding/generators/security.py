from textSQL.database.models import (
    Role,
    Permission,
    RolePermission,
)


DEFAULT_ROLES = [
    "admin",
    "manager",
    "customer_support",
    "warehouse_staff",
    "customer",
]


DEFAULT_PERMISSIONS = [
    "manage_users",
    "view_users",
    "manage_products",
    "view_products",
    "manage_orders",
    "view_orders",
    "process_payments",
    "manage_inventory",
    "view_inventory",
    "manage_campaigns",
    "view_reports",
]


def seed_security(session):

    roles = [
        Role(role_name=name)
        for name in DEFAULT_ROLES
    ]

    permissions = [
        Permission(permission_name=name)
        for name in DEFAULT_PERMISSIONS
    ]

    session.add_all(roles)
    session.add_all(permissions)

    session.flush()


    admin = roles[0]

    mappings = [
        RolePermission(
            role_id=admin.role_id,
            permission_id=p.permission_id
        )
        for p in permissions
    ]

    session.add_all(mappings)

    session.commit()