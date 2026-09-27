import pytest

from textSQL.metadata.models import (
    TableMetadata,
    ColumnMetadata,
)

from textSQL.metadata.extractor import (
    enrich_table_metadata,
)


def build_table():

    return TableMetadata(

        name="payments",

        schema_name="public",

        columns=[

            ColumnMetadata(
                name="payment_status",
                data_type="VARCHAR",
                nullable=False,
            ),

            ColumnMetadata(
                name="attempted_at",
                data_type="TIMESTAMP",
                nullable=False,
            ),
        ],
    )


def test_enriches_table_semantics():

    table = build_table()


    result = enrich_table_metadata(

        table,

        {
            "description":
                "Payment attempts.",

            "business_role":
                "Payment processing state.",

            "columns": {},
        },
    )


    assert (
        result.description
        ==
        "Payment attempts."
    )


    assert (
        result.business_role
        ==
        "Payment processing state."
    )


def test_enriches_column_semantics():

    table = build_table()


    result = enrich_table_metadata(

        table,

        {
            "columns": {

                "payment_status": {

                    "description":
                        "Payment state.",

                    "business_meaning":
                        "Completed means successful.",

                    "allowed_values": [
                        "pending",
                        "completed",
                        "failed",
                    ],
                }
            }
        },
    )


    status_column = next(

        column

        for column
        in result.columns

        if (
            column.name
            ==
            "payment_status"
        )
    )


    assert (
        status_column.description
        ==
        "Payment state."
    )


    assert (
        status_column.business_meaning
        ==
        "Completed means successful."
    )


    assert (
        status_column.allowed_values
        ==
        [
            "pending",
            "completed",
            "failed",
        ]
    )


def test_enrichment_preserves_structural_metadata():

    table = build_table()


    result = enrich_table_metadata(

        table,

        {
            "columns": {

                "payment_status": {

                    "allowed_values": [
                        "completed"
                    ]
                }
            }
        },
    )


    column = result.columns[0]


    assert (
        column.name
        ==
        "payment_status"
    )

    assert (
        column.data_type
        ==
        "VARCHAR"
    )

    assert (
        column.nullable
        is False
    )


def test_unknown_column_is_rejected():

    table = build_table()


    with pytest.raises(
        ValueError,
        match="unknown columns",
    ):

        enrich_table_metadata(

            table,

            {
                "columns": {

                    "does_not_exist": {
                        "description":
                            "bad config"
                    }
                }
            },
        )