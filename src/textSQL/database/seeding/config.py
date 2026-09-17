from dataclasses import dataclass


@dataclass(frozen=True)
class SeedConfig:

    users: int = 5000
    customers: int = 10000

    brands: int = 200
    categories: int = 100
    products: int = 500
    variants_per_product: int = 4
    roles: int=5
    warehouses: int = 5

    campaigns: int = 100

    orders: int = 50000

    reviews: int = 10000

    events: int = 200000
    permessions : int=30



DEFAULT_CONFIG = SeedConfig()