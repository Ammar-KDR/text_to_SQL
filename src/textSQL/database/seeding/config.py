from dataclasses import dataclass


@dataclass(frozen=True)
class SeedConfig:

    users: int = 40000
    customers: int = 50000

    brands: int = 200
    categories: int = 100
    products: int = 5000
    variants_per_product: int = 4
    roles: int=5
    warehouses: int = 5

    campaigns: int = 100

    orders: int = 250000

    reviews: int = 10000

    events: int = 200000
    permessions : int=30
    customer_insert_batch_size: int = 5_000
    event_insert_batch_size: int = 10_000
    

    order_batch_size: int = 2_500
    transaction_insert_batch_size: int = 10_000
    campaigns: int = 100
    reviews: int = 100_000

    marketing_batch_size: int = 10_000
    review_batch_size: int = 10_000



CONFIG = SeedConfig()



