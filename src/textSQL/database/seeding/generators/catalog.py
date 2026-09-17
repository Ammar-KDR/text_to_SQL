from textSQL.database.models import (
    Brand,
    Category,
)

from faker import Faker


fake = Faker()


def seed_brands(session, count):

    brands = []
    existing_names = set()

    while len(brands) < count:

        name = fake.company()

        if name in existing_names:
            continue

        existing_names.add(name)

        brands.append(
            Brand(
                brand_name=name
            )
        )

    session.add_all(brands)
    session.commit()



def seed_categories(session):

    categories = []


    top_categories = [
        "Electronics",
        "Home",
        "Office",
        "Sports",
        "Fashion",
    ]


    for parent in top_categories:

        parent_category = Category(
            category_name=parent,
            parent_category_id=None
        )

        session.add(parent_category)
        session.flush()


        for i in range(5):

            categories.append(
                Category(
                    category_name=f"{parent} - {i+1}",
                    parent_category_id=parent_category.category_id
                )
            )


    session.add_all(categories)

    session.commit()