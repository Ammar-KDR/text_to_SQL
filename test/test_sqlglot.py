from sqlglot import parse_one, exp


sql = """
SELECT
    order_id,
    customer_id
FROM public.orders
WHERE customer_id IN (
    SELECT customer_id
    FROM public.customers
)
"""


tree = parse_one(
    sql,
    read="postgres",
)


print("=" * 80)
print("ROOT")
print("=" * 80)

print(type(tree).__name__)
print(tree.sql(dialect="postgres"))
print()


print("=" * 80)
print("FULL AST DUMP")
print("=" * 80)

print(tree.dump())
print()


print("=" * 80)
print("ALL SELECT NODES")
print("=" * 80)

for index, select in enumerate(tree.find_all(exp.Select), start=1):
    print(
        f"SELECT #{index}:",
        select.sql(dialect="postgres"),
    )

print()


print("=" * 80)
print("SUBQUERIES")
print("=" * 80)

for subquery in tree.find_all(exp.Subquery):
    print(
        "node type:",
        type(subquery).__name__,
        "| sql:",
        subquery.sql(dialect="postgres"),
    )

print()


print("=" * 80)
print("TABLES")
print("=" * 80)

for table in tree.find_all(exp.Table):
    print(
        "name:",
        table.name,
        "| schema:",
        table.db,
        "| sql:",
        table.sql(dialect="postgres"),
    )

print()


print("=" * 80)
print("COLUMNS")
print("=" * 80)

for column in tree.find_all(exp.Column):
    print(
        "name:",
        column.name,
        "| table:",
        column.table,
        "| sql:",
        column.sql(dialect="postgres"),
    )

print()


print("=" * 80)
print("NODE + PARENT")
print("=" * 80)

for node in tree.walk():
    print(
        type(node).__name__,
        "-> parent:",
        type(node.parent).__name__
        if node.parent
        else None,
    )