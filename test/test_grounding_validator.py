from textSQL.generation.models import (
    GenerationColumnContext,
    GenerationTableContext,
    GenerationContext,
    GenerationJoinCondition,
GenerationRelationshipContext,
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

            qualified_name=(
                "public.orders"
            ),

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

                GenerationColumnContext(
                    name="total_amount",
                    data_type="NUMERIC",
                    nullable=False,
                ),
            ],
        ),


        GenerationTableContext(

            qualified_name=(
                "public.customers"
            ),

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

            qualified_name=(
                "public.order_items"
            ),

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

            source_cardinality=(
                "many"
            ),

            target_cardinality=(
                "one"
            ),

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
# VALID PHYSICAL REFERENCES
# ============================================================


def test_known_table_and_qualified_column_pass():

    result = validate(
        """
        SELECT
            o.order_id
        FROM public.orders AS o;
        """
    )


    assert (
        result.valid
        is True
    )


    assert (
        result.issues
        ==
        []
    )


# ============================================================
# UNKNOWN TABLE
# ============================================================


def test_unknown_table_is_rejected():

    result = validate(
        """
        SELECT *
        FROM public.fake_orders;
        """
    )


    assert (
        result.valid
        is False
    )


    assert len(
        result.issues
    ) == 1


    issue = (
        result.issues[0]
    )


    assert (
        issue.code
        ==
        ValidationIssueCode
        .UNKNOWN_TABLE
    )


    assert (
        issue.object_name
        ==
        "public.fake_orders"
    )


# ============================================================
# DAY 6 HIDDEN HALLUCINATION
# ============================================================


def test_day6_hidden_table_hallucination_is_caught():

    result = validate(
        """
        SELECT *
        FROM warehouse.fake_sales;
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
        .UNKNOWN_TABLE

        and

        issue.object_name
        ==
        "warehouse.fake_sales"

        for issue
        in result.issues
    )


# ============================================================
# UNKNOWN QUALIFIED COLUMN
# ============================================================


def test_unknown_qualified_column_is_rejected():

    result = validate(
        """
        SELECT
            o.fake_column
        FROM public.orders AS o;
        """
    )


    assert (
        result.valid
        is False
    )


    issue = (
        result.issues[0]
    )


    assert (
        issue.code
        ==
        ValidationIssueCode
        .UNKNOWN_COLUMN
    )


    assert (
        issue.object_name
        ==
        "public.orders.fake_column"
    )


# ============================================================
# UNQUALIFIED COLUMN
# ============================================================


def test_unqualified_column_with_one_owner_passes():

    result = validate(
        """
        SELECT
            order_id
        FROM public.orders;
        """
    )


    assert (
        result.valid
        is True
    )


def test_unqualified_column_resolves_when_only_one_joined_table_has_it():

    result = validate(
        """
        SELECT
            email
        FROM public.orders
        JOIN public.customers
            ON (
                orders.customer_id
                =
                customers.customer_id
            );
        """
    )


    assert (
        result.valid
        is True
    )


# ============================================================
# AMBIGUOUS COLUMN
# ============================================================


def test_ambiguous_unqualified_column_is_rejected():

    result = validate(
        """
        SELECT
            customer_id
        FROM public.orders
        JOIN public.customers
            ON (
                orders.customer_id
                =
                customers.customer_id
            );
        """
    )


    assert (
        result.valid
        is False
    )


    issue = next(
        issue
        for issue
        in result.issues
        if (
            issue.code
            ==
            ValidationIssueCode
            .AMBIGUOUS_COLUMN
        )
    )


    assert (
        issue.object_name
        ==
        "customer_id"
    )


# ============================================================
# UNKNOWN UNQUALIFIED COLUMN
# ============================================================


def test_unknown_unqualified_column_is_rejected():

    result = validate(
        """
        SELECT
            fake_column
        FROM public.orders;
        """
    )


    assert (
        result.valid
        is False
    )


    assert (
        result.issues[0].code
        ==
        ValidationIssueCode
        .UNKNOWN_COLUMN
    )


    assert (
        result.issues[0].object_name
        ==
        "fake_column"
    )


# ============================================================
# CORRELATED SUBQUERY
# ============================================================


def test_valid_correlated_outer_column_passes():

    result = validate(
        """
        SELECT
            o.order_id
        FROM public.orders AS o
        WHERE EXISTS (
            SELECT 1
            FROM public.order_items AS oi
            WHERE
                oi.order_id
                =
                o.order_id
        );
        """
    )


    assert (
        result.valid
        is True
    )


def test_unknown_correlated_outer_column_is_rejected():

    result = validate(
        """
        SELECT
            o.order_id
        FROM public.orders AS o
        WHERE EXISTS (
            SELECT 1
            FROM public.order_items AS oi
            WHERE
                oi.order_id
                =
                o.fake_column
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
        .UNKNOWN_COLUMN

        and

        issue.object_name
        ==
        "public.orders.fake_column"

        for issue
        in result.issues
    )


# ============================================================
# UNKNOWN QUALIFIER
# ============================================================


def test_unknown_qualifier_is_rejected():

    result = validate(
        """
        SELECT
            x.order_id
        FROM public.orders AS o;
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
        .UNKNOWN_COLUMN

        and

        issue.object_name
        ==
        "x.order_id"

        for issue
        in result.issues
    )


# ============================================================
# LOGICAL SOURCES
# ============================================================


def test_cte_output_column_is_not_false_positive():

    result = validate(
        """
        WITH totals AS (
            SELECT
                o.customer_id,
                SUM(o.total_amount)
                    AS total_spend
            FROM public.orders AS o
            GROUP BY o.customer_id
        )
        SELECT
            t.total_spend
        FROM totals AS t;
        """
    )


    assert (
        result.valid
        is True
    )


# ============================================================
# MULTIPLE ISSUES
# ============================================================


def test_multiple_unknown_tables_are_reported():

    result = validate(
        """
        SELECT *
        FROM public.fake_orders AS fo
        JOIN public.fake_customers AS fc
            ON fo.customer_id = fc.customer_id;
        """
    )


    unknown_tables = {
        issue.object_name
        for issue
        in result.issues
        if (
            issue.code
            ==
            ValidationIssueCode
            .UNKNOWN_TABLE
        )
    }


    assert unknown_tables == {
        "public.fake_orders",
        "public.fake_customers",
    }


def test_unknown_cte_output_column_is_rejected():

    result = validate(
        """
        WITH totals AS (
            SELECT
                o.customer_id,
                SUM(o.total_amount)
                    AS total_spend
            FROM public.orders AS o
            GROUP BY o.customer_id
        )
        SELECT
            t.fake_column
        FROM totals AS t;
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
        .UNKNOWN_COLUMN

        and

        issue.object_name
        ==
        "t.fake_column"

        for issue
        in result.issues
    )


def test_known_cte_output_column_passes():

    result = validate(
        """
        WITH totals AS (
            SELECT
                o.customer_id,
                SUM(o.total_amount)
                    AS total_spend
            FROM public.orders AS o
            GROUP BY o.customer_id
        )
        SELECT
            t.total_spend
        FROM totals AS t;
        """
    )


    assert (
        result.valid
        is True
    )


def test_unknown_derived_table_output_is_rejected():

    result = validate(
        """
        SELECT
            x.fake_column
        FROM (
            SELECT
                o.order_id
            FROM public.orders AS o
        ) AS x;
        """
    )


    assert (
        result.valid
        is False
    )


    assert any(
        issue.object_name
        ==
        "x.fake_column"

        for issue
        in result.issues
    )


def test_derived_table_known_output_passes():

    result = validate(
        """
        SELECT
            x.order_id
        FROM (
            SELECT
                o.order_id
            FROM public.orders AS o
        ) AS x;
        """
    )


    assert (
        result.valid
        is True
    )


def test_cte_star_expands_using_generation_context():

    result = validate(
        """
        WITH customer_data AS (
            SELECT *
            FROM public.customers
        )
        SELECT
            c.email
        FROM customer_data AS c;
        """
    )


    assert (
        result.valid
        is True
    )


def test_fake_column_through_cte_star_is_rejected():

    result = validate(
        """
        WITH customer_data AS (
            SELECT *
            FROM public.customers
        )
        SELECT
            c.fake_column
        FROM customer_data AS c;
        """
    )


    assert (
        result.valid
        is False
    )


    assert any(
        issue.object_name
        ==
        "c.fake_column"

        for issue
        in result.issues
    )


def test_unqualified_column_from_logical_source_passes():

    result = validate(
        """
        WITH customer_data AS (
            SELECT
                c.email
            FROM public.customers AS c
        )
        SELECT
            email
        FROM customer_data;
        """
    )


    assert (
        result.valid
        is True
    )


def test_unqualified_column_is_ambiguous_across_physical_and_logical_sources():

    result = validate(
        """
        WITH customer_data AS (
            SELECT
                c.customer_id
            FROM public.customers AS c
        )
        SELECT
            customer_id
        FROM public.orders AS o
        JOIN customer_data AS cd
            ON (
                o.customer_id
                =
                cd.customer_id
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
        .AMBIGUOUS_COLUMN

        and

        issue.object_name
        ==
        "customer_id"

        for issue
        in result.issues
    )