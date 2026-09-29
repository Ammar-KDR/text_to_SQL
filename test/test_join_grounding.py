from textSQL.generation.models import (
    GenerationColumnContext,
    GenerationTableContext,
    GenerationJoinCondition,
    GenerationRelationshipContext,
    GenerationContext,
)

from textSQL.validation.analyzer import (
    ASTAnalyzer,
)

from textSQL.validation.models import (
    ValidationIssueCode,
)

from textSQL.validation.parser import (
    SQLParser,
)

from textSQL.validation.validator import (
    GroundingValidator,
)


# ============================================================
# HELPERS
# ============================================================


def build_context():

    return GenerationContext(

        tables=[

            GenerationTableContext(
                qualified_name="public.orders",
                columns=[
                    GenerationColumnContext(
                        name="order_id",
                        data_type="BIGINT",
                        nullable=False,
                    ),
                    GenerationColumnContext(
                        name="customer_id",
                        data_type="BIGINT",
                        nullable=False,
                    ),
                ],
            ),

            GenerationTableContext(
                qualified_name="public.customers",
                columns=[
                    GenerationColumnContext(
                        name="customer_id",
                        data_type="BIGINT",
                        nullable=False,
                    ),
                    GenerationColumnContext(
                        name="email",
                        data_type="VARCHAR",
                        nullable=False,
                    ),
                ],
            ),

            GenerationTableContext(
                qualified_name="public.order_items",
                columns=[
                    GenerationColumnContext(
                        name="order_item_id",
                        data_type="BIGINT",
                        nullable=False,
                    ),
                    GenerationColumnContext(
                        name="order_id",
                        data_type="BIGINT",
                        nullable=False,
                    ),
                ],
            ),
        ],

        relationships=[

            GenerationRelationshipContext(

                relationship_id=(
                    "orders_customers"
                ),

                source_table=(
                    "public.orders"
                ),

                target_table=(
                    "public.customers"
                ),

                relationship_type=(
                    "many-to-one"
                ),

                source_cardinality="many",

                target_cardinality="one",

                join_conditions=[

                    GenerationJoinCondition(

                        source_column=(
                            "public.orders."
                            "customer_id"
                        ),

                        target_column=(
                            "public.customers."
                            "customer_id"
                        ),
                    )
                ],
            ),

            GenerationRelationshipContext(

                relationship_id=(
                    "order_items_orders"
                ),

                source_table=(
                    "public.order_items"
                ),

                target_table=(
                    "public.orders"
                ),

                relationship_type=(
                    "many-to-one"
                ),

                source_cardinality="many",

                target_cardinality="one",

                join_conditions=[

                    GenerationJoinCondition(

                        source_column=(
                            "public.order_items."
                            "order_id"
                        ),

                        target_column=(
                            "public.orders."
                            "order_id"
                        ),
                    )
                ],
            ),
        ],
    )


def validate(
    sql: str,
):

    parsed = (
        SQLParser()
        .parse(
            sql
        )
    )


    analysis = (
        ASTAnalyzer()
        .analyze(
            parsed
        )
    )


    return (
        GroundingValidator()
        .validate(
            analysis=analysis,
            context=build_context(),
        )
    )


# ============================================================
# VALID RELATIONSHIP
# ============================================================


def test_valid_join_relationship_passes():

    result = validate(
        """
        SELECT
            o.order_id,
            c.email
        FROM public.orders AS o
        JOIN public.customers AS c
            ON (
                o.customer_id
                =
                c.customer_id
            );
        """
    )


    assert (
        result.valid
        is True
    )


# ============================================================
# REVERSED EQUALITY
# ============================================================


def test_reversed_join_equality_passes():

    result = validate(
        """
        SELECT
            o.order_id
        FROM public.orders AS o
        JOIN public.customers AS c
            ON (
                c.customer_id
                =
                o.customer_id
            );
        """
    )


    assert (
        result.valid
        is True
    )


# ============================================================
# INVENTED JOIN CONDITION
# ============================================================


def test_wrong_join_columns_are_rejected():

    result = validate(
        """
        SELECT
            o.order_id
        FROM public.orders AS o
        JOIN public.customers AS c
            ON (
                o.order_id
                =
                c.customer_id
            );
        """
    )


    assert (
        result.valid
        is False
    )


    assert any(
        issue.code
        ==
        ValidationIssueCode
        .INVALID_JOIN

        for issue
        in result.issues
    )


# ============================================================
# NO RETRIEVED RELATIONSHIP
# ============================================================


def test_join_between_unrelated_tables_is_rejected():

    result = validate(
        """
        SELECT *
        FROM public.customers AS c
        JOIN public.order_items AS oi
            ON (
                c.customer_id
                =
                oi.order_id
            );
        """
    )


    assert (
        result.valid
        is False
    )


    assert any(
        issue.code
        ==
        ValidationIssueCode
        .INVALID_JOIN

        for issue
        in result.issues
    )


# ============================================================
# EXTRA INVENTED CROSS-TABLE EQUALITY
# ============================================================


def test_extra_cross_table_equality_is_rejected():

    result = validate(
        """
        SELECT *
        FROM public.orders AS o
        JOIN public.customers AS c
            ON (
                o.customer_id
                =
                c.customer_id

                AND

                o.order_id
                =
                c.customer_id
            );
        """
    )


    assert (
        result.valid
        is False
    )


    assert any(
        issue.code
        ==
        ValidationIssueCode
        .INVALID_JOIN

        for issue
        in result.issues
    )


# ============================================================
# OR CONDITION
# ============================================================


def test_join_with_or_is_rejected():

    result = validate(
        """
        SELECT *
        FROM public.orders AS o
        JOIN public.customers AS c
            ON (
                o.customer_id
                =
                c.customer_id

                OR

                c.email = 'test@example.com'
            );
        """
    )


    assert (
        result.valid
        is False
    )


    assert any(
        issue.code
        ==
        ValidationIssueCode
        .INVALID_JOIN

        for issue
        in result.issues
    )


# ============================================================
# CROSS JOIN
# ============================================================
def test_join_without_relationship_condition_is_rejected():

    result = validate(
        """
        SELECT *
        FROM public.orders AS o
        CROSS JOIN public.customers AS c;
        """
    )


    assert (
        result.valid
        is False
    )


    assert any(
        issue.code
        ==
        ValidationIssueCode
        .INVALID_JOIN

        for issue
        in result.issues
    )
# ============================================================
# LOGICAL SOURCE FAILS CLOSED
# ============================================================


def test_join_to_cte_fails_closed():

    result = validate(
        """
        WITH customer_data AS (
            SELECT
                customer_id
            FROM public.customers
        )
        SELECT *
        FROM public.orders AS o
        JOIN customer_data AS c
            ON (
                o.customer_id
                =
                c.customer_id
            );
        """
    )


    assert (
        result.valid
        is False
    )


    assert any(
        issue.code
        ==
        ValidationIssueCode
        .INVALID_JOIN

        for issue
        in result.issues
    )