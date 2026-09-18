from __future__ import annotations

from decimal import Decimal
import random
import re

from sqlalchemy import insert

from textSQL.database.models import (
    Brand,
    Category,
    Product,
    ProductVariant,
    ProductCategory,
)


PRODUCT_PROFILES = [
    {
        "keywords": ["laptop", "notebook"],
        "family": "Laptop",
        "price": (550, 2400),
        "sizes": ["13-inch", "14-inch", "15-inch", "16-inch"],
        "colors": ["Black", "Silver", "Gray"],
    },
    {
        "keywords": ["phone", "smartphone", "mobile"],
        "family": "Smartphone",
        "price": (220, 1600),
        "sizes": ["128GB", "256GB", "512GB"],
        "colors": ["Black", "White", "Blue", "Silver"],
    },
    {
        "keywords": ["tablet"],
        "family": "Tablet",
        "price": (180, 1300),
        "sizes": ["64GB", "128GB", "256GB"],
        "colors": ["Black", "Silver", "Gray"],
    },
    {
        "keywords": ["monitor", "display"],
        "family": "Monitor",
        "price": (120, 1100),
        "sizes": ["24-inch", "27-inch", "32-inch", "34-inch"],
        "colors": ["Black", "White"],
    },
    {
        "keywords": ["headphone", "audio", "earphone"],
        "family": "Headphones",
        "price": (30, 550),
        "sizes": ["Standard"],
        "colors": ["Black", "White", "Blue"],
    },
    {
        "keywords": ["tv", "television"],
        "family": "Smart TV",
        "price": (280, 3200),
        "sizes": ["43-inch", "50-inch", "55-inch", "65-inch"],
        "colors": ["Black"],
    },
    {
        "keywords": ["shoe", "footwear", "sneaker"],
        "family": "Shoes",
        "price": (35, 320),
        "sizes": ["39", "40", "41", "42", "43", "44"],
        "colors": ["Black", "White", "Gray", "Blue", "Brown"],
    },
    {
        "keywords": ["shirt", "clothing", "apparel", "fashion"],
        "family": "Apparel",
        "price": (15, 190),
        "sizes": ["S", "M", "L", "XL"],
        "colors": ["Black", "White", "Blue", "Gray", "Green"],
    },
    {
        "keywords": ["chair", "furniture"],
        "family": "Furniture",
        "price": (60, 850),
        "sizes": ["Standard"],
        "colors": ["Black", "White", "Brown", "Gray"],
    },
    {
        "keywords": ["bag", "backpack"],
        "family": "Bag",
        "price": (20, 450),
        "sizes": ["Small", "Medium", "Large"],
        "colors": ["Black", "Brown", "Blue", "Gray"],
    },
    {
        "keywords": ["watch"],
        "family": "Watch",
        "price": (40, 1400),
        "sizes": ["Standard"],
        "colors": ["Black", "Silver", "Gold"],
    },
    {
        "keywords": ["kitchen", "appliance"],
        "family": "Appliance",
        "price": (30, 900),
        "sizes": ["Standard"],
        "colors": ["Black", "White", "Silver"],
    },
    {
        "keywords": ["sport", "fitness"],
        "family": "Sports Equipment",
        "price": (20, 750),
        "sizes": ["Small", "Medium", "Large"],
        "colors": ["Black", "Blue", "Red"],
    },
    {
        "keywords": ["beauty", "cosmetic"],
        "family": "Beauty Product",
        "price": (10, 250),
        "sizes": ["Small", "Standard", "Large"],
        "colors": ["Standard"],
    },
]


GENERIC_PROFILE = {
    "family": "Product",
    "price": (15, 700),
    "sizes": ["Standard"],
    "colors": ["Standard"],
}


SERIES_NAMES = [
    "Essential",
    "Core",
    "Plus",
    "Prime",
    "Edge",
    "Nova",
    "Elite",
    "Pro",
    "Ultra",
    "Studio",
]


def get_profile(category_name: str):

    category_lower = category_name.lower()

    for profile in PRODUCT_PROFILES:

        if any(
            keyword in category_lower
            for keyword in profile["keywords"]
        ):
            return profile

    profile = GENERIC_PROFILE.copy()

    clean_name = (
        category_name
        .replace("&", "")
        .strip()
    )

    if clean_name:
        profile["family"] = clean_name

    return profile


def brand_label(name: str) -> str:

    name = re.sub(
        r"\b(LLC|Ltd|PLC|Inc|Group)\b",
        "",
        name,
        flags=re.IGNORECASE,
    )

    name = re.sub(
        r"\s+",
        " ",
        name,
    ).strip()

    words = name.split()

    return " ".join(words[:2])


def variant_count() -> int:

    return random.choices(
        [1, 2, 3, 4, 5, 6],
        weights=[5, 15, 25, 25, 20, 10],
        k=1,
    )[0]


def make_price(
    low: float,
    high: float,
) -> Decimal:

    value = round(
        random.uniform(
            low,
            high
        )
    )

    value = max(
        value,
        10
    )

    return Decimal(
        f"{value - 0.01:.2f}"
    )


def seed_products(
    session,
    count: int,
):

    print(
        f"Creating {count:,} products..."
    )

    brands = (
        session.query(Brand)
        .all()
    )

    categories = (
        session.query(Category)
        .all()
    )

    if not brands:
        raise RuntimeError(
            "No brands found. Seed brands first."
        )

    if not categories:
        raise RuntimeError(
            "No categories found. Seed categories first."
        )

    # A leaf category is a category that is not
    # a parent of another category.
    parent_ids = {
        category.parent_category_id
        for category in categories
        if category.parent_category_id is not None
    }

    leaf_categories = [
        category
        for category in categories
        if category.category_id not in parent_ids
    ]

    if not leaf_categories:
        leaf_categories = categories

    # Gives some categories naturally higher popularity.
    category_weights = {
        category.category_id:
            random.uniform(0.5, 3.0)
        for category in leaf_categories
    }

    products = []
    metadata = []

    for index in range(1, count + 1):

        brand = random.choice(
            brands
        )

        category = random.choices(
            leaf_categories,
            weights=[
                category_weights[
                    c.category_id
                ]
                for c in leaf_categories
            ],
            k=1,
        )[0]

        profile = get_profile(
            category.category_name
        )

        series = random.choice(
            SERIES_NAMES
        )

        model_number = random.randint(
            100,
            9999,
        )

        product_name = (
            f"{brand_label(brand.brand_name)} "
            f"{profile['family']} "
            f"{series} {model_number}"
        )

        description = (
            f"{profile['family']} from "
            f"{brand.brand_name}, designed for "
            f"the {category.category_name} category."
        )

        product = Product(
            name=product_name,
            brand_id=brand.brand_id,
            description=description,
        )

        products.append(
            product
        )

        metadata.append(
            {
                "product": product,
                "category": category,
                "profile": profile,
            }
        )

    session.add_all(
        products
    )

    session.flush()

    print(
        "Creating product-category mappings..."
    )

    category_rows = []

    for item in metadata:

        product = item["product"]
        primary = item["category"]

        assigned_ids = {
            primary.category_id
        }

        category_rows.append(
            {
                "product_id":
                    product.product_id,

                "category_id":
                    primary.category_id,
            }
        )

        # About 15% of products legitimately belong
        # to another reporting category.
        if (
            random.random() < 0.15
            and len(leaf_categories) > 1
        ):

            alternatives = [
                category
                for category
                in leaf_categories
                if category.category_id
                not in assigned_ids
            ]

            secondary = random.choice(
                alternatives
            )

            category_rows.append(
                {
                    "product_id":
                        product.product_id,

                    "category_id":
                        secondary.category_id,
                }
            )

    session.execute(
        insert(ProductCategory.__table__),
        category_rows,
    )

    print(
        "Creating product variants..."
    )

    variant_rows = []

    variant_columns = (
        ProductVariant
        .__table__
        .columns
        .keys()
    )

    # Handles either SKU or sku depending
    # on how your model was written.
    if "SKU" in variant_columns:
        sku_column = "SKU"
    else:
        sku_column = "sku"

    for item in metadata:

        product = item["product"]
        profile = item["profile"]

        combinations = [
            (size, color)
            for size in profile["sizes"]
            for color in profile["colors"]
        ]

        requested_count = min(
            variant_count(),
            len(combinations),
        )

        selected = random.sample(
            combinations,
            k=requested_count,
        )

        base_price = make_price(
            *profile["price"]
        )

        for variant_index, (
            size,
            color,
        ) in enumerate(
            selected,
            start=1,
        ):

            price_multiplier = (
                Decimal("1.00")
                + Decimal(
                    str(
                        random.uniform(
                            -0.04,
                            0.08,
                        )
                    )
                )
            )

            price = (
                base_price
                * price_multiplier
            ).quantize(
                Decimal("0.01")
            )

            sku = (
                f"P{product.product_id:06d}"
                f"-V{variant_index:02d}"
            )

            row = {
                "product_id":
                    product.product_id,

                sku_column:
                    sku,

                "size":
                    size,

                "color":
                    color,

                "price":
                    price,
            }

            variant_rows.append(
                row
            )

    # Insert in chunks.
    batch_size = 10_000

    for start in range(
        0,
        len(variant_rows),
        batch_size,
    ):

        session.execute(
            insert(
                ProductVariant.__table__
            ),
            variant_rows[
                start:
                start + batch_size
            ],
        )

    session.commit()

    print(
        "Product domain complete:"
    )

    print(
        f"  products: {len(products):,}"
    )

    print(
        f"  variants: {len(variant_rows):,}"
    )

    print(
        f"  category mappings: "
        f"{len(category_rows):,}"
    )

    return {
        "products": len(products),
        "variants": len(variant_rows),
    }