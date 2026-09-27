from textSQL.database.connection import (
    engine,
)

from textSQL.metadata.config import (
    load_metadata_config,
)

from textSQL.metadata.extractor import (
    extract_database_metadata,
)

from textSQL.retrieval.index import (
    MetadataIndex,
)

from textSQL.embeddings.encoder import (
    BGEEncoder,
)

from textSQL.retrieval.query_encoder import (
    QueryEncoder,
)

from textSQL.vectorstore.qdrant import (
    QdrantVectorStore,
)

from textSQL.retrieval.dense_retriever import (
    DenseRetriever,
)

from textSQL.retrieval.dependency_resolver import (
    DependencyResolver,
)

from textSQL.retrieval.graph_retriever import (
    GraphRetriever,
)

from textSQL.retrieval.fusion import (
    Fusion,
)

from textSQL.retrieval.context_builder import (
    ContextBuilder,
)

from textSQL.retrieval.retriever import (
    Retriever,
)

from textSQL.retrieval.seed_selector import (
    SeedSelector,
)

from textSQL.llm.factory import (
    build_llm_client,
)

from textSQL.generation.generator import (
    SQLGenerator,
)

from textSQL.generation.errors import (
    GenerationError,
)

from textSQL.llm.errors import (
    LLMProviderError,
)

from textSQL.generation.errors import (
    GenerationError,
    InvalidStructuredOutputError,
)

from textSQL.retrieval.temporal_resolver import TemporalDependencyResolver
# ============================================================
# BUILD REAL METADATA
# ============================================================


print(
    "\nLoading metadata..."
)


config = load_metadata_config(
    "src/textSQL/config/metadata_config.yaml"
)


metadata = extract_database_metadata(
    engine,
    config,
)


print(
    f"Loaded {len(metadata.metrics)} metrics"
)


# ============================================================
# BUILD REAL RETRIEVAL PIPELINE
# ============================================================


metadata_index = MetadataIndex(
    metadata,
    metadata.graph,
)


seed_selector = SeedSelector(
    metadata_index
)


encoder = BGEEncoder()


query_encoder = QueryEncoder(
    encoder
)


vector_store = QdrantVectorStore()


dense_retriever = DenseRetriever(

    query_encoder=(
        query_encoder
    ),

    vector_store=(
        vector_store
    ),

    metadata_index=(
        metadata_index
    ),
)


dependency_resolver = (
    DependencyResolver(
        metadata_index
    )
)


graph_retriever = (
    GraphRetriever(

        metadata_index=(
            metadata_index
        ),

        graph=(
            metadata.graph
        ),
    )
)


fusion = Fusion()


context_builder = (
    ContextBuilder(
        metadata_index
    )
)
temporal_resolver = (
    TemporalDependencyResolver(
        metadata_index
    )
)


retriever = Retriever(

    dense_retriever=(
        dense_retriever
    ),

    dependency_resolver=(
        dependency_resolver
    ),

    graph_retriever=(
        graph_retriever
    ),

    fusion=(
        fusion
    ),

    context_builder=(
        context_builder
    ),

    seed_selector=(
        seed_selector
    ),

    temporal_resolver=(
        temporal_resolver
    ),
)


# ============================================================
# BUILD REAL GENERATION PIPELINE
# ============================================================


llm_client = (
    build_llm_client()
)


sql_generator = SQLGenerator(
    llm_client=(
        llm_client
    )
)


# ============================================================
# DISPLAY HELPERS
# ============================================================


def print_retrieved_context(
    context,
):

    print(
        "\nRETRIEVED METRICS:"
    )

    if not context.metrics:

        print(
            "  <none>"
        )


    for metric in context.metrics:

        print(
            f"  - {metric.name}"
        )

        print(
            "    source: "
            f"{metric.authoritative_source}"
        )


    print(
        "\nRETRIEVED TABLES:"
    )

    if not context.tables:

        print(
            "  <none>"
        )


    for table in context.tables:

        print(
            f"  - {table.qualified_name}"
        )


    print(
        "\nRETRIEVED RELATIONSHIPS:"
    )

    if not context.relationships:

        print(
            "  <none>"
        )


    for relationship in (
        context.relationships
    ):

        print(
            "  - "
            f"{relationship.source_qualified_name}"
            " -> "
            f"{relationship.target_qualified_name}"
        )


        for condition in (
            relationship.join_conditions
        ):

            print(
                "      "
                f"{condition.source_qualified_column}"
                " = "
                f"{condition.target_qualified_column}"
            )


    print(
        "\nJOIN PATHS:"
    )

    if not context.join_paths:

        print(
            "  <none>"
        )


    for path in context.join_paths:

        print(
            "  - "
            +
            " -> ".join(
                path.tables
            )
        )


def print_generation_result(
    result,
):

    print(
        "\nGENERATION STATUS:"
    )

    print(
        f"  {result.status.value}"
    )


    print(
        "\nSQL:"
    )

    print(
        result.sql
        or
        "<none>"
    )


    print(
        "\nEXPLANATION:"
    )

    print(
        result.explanation
    )


    print(
        "\nTABLES USED:"
    )

    for table in (
        result.tables_used
    ):

        print(
            f"  - {table}"
        )


    print(
        "\nCOLUMNS USED:"
    )

    for column in (
        result.columns_used
    ):

        print(
            f"  - {column}"
        )


    print(
        "\nASSUMPTIONS:"
    )

    if not result.assumptions:

        print(
            "  <none>"
        )

    for assumption in (
        result.assumptions
    ):

        print(
            f"  - {assumption}"
        )


    if (
        result.clarification_question
    ):

        print(
            "\nCLARIFICATION:"
        )

        print(
            result
            .clarification_question
        )


        if (
            result
            .clarification_options
        ):

            print(
                "\nOPTIONS:"
            )

            for option in (
                result
                .clarification_options
            ):

                print(
                    f"  - {option}"
                )


# ============================================================
# REPRESENTATIVE DAY 6 QUESTIONS
# ============================================================


questions = [

    # Simple / table-level
    "How many customers are registered?",

    # # Operational / OLTP
     "How many completed payments were attempted last month?",

    # # Analytical / OLAP
    "What were the top 10 products by revenue?",

    # Metric + dimension + date
    "What was revenue by campaign last quarter?",

    # # Materially ambiguous
    "Who are our best customers?",

    # Known schema limitation
    (
        "Which exact product was viewed "
        "most often by customers?"
    ),
]


# ============================================================
# RUN
# ============================================================


for question in questions:

    print(
        "\n\n"
        +
        "=" * 100
    )

    print(
        f"QUESTION: {question}"
    )

    print(
        "=" * 100
    )


    try:

        context = retriever.retrieve(
            question,
            limit=5,
        )


        print_retrieved_context(
            context
        )


        result = (
            sql_generator.generate(
                context
            )
        )


        print_generation_result(
            result
        )


    except LLMProviderError as exc:

        print(
            "\nLLM PROVIDER ERROR:"
        )

        print(
            f"  {exc}"
        )
    except InvalidStructuredOutputError as exc:

        print(
            "\nINVALID STRUCTURED OUTPUT:"
        )

        print(
            "\nRAW MODEL RESPONSE:"
        )

        print(
            exc.raw_response
        )


        print(
            "\nVALIDATION ERRORS:"
        )

        for error in (
            exc.validation_errors
            or []
        ):

            print(
                f"  - {error}"
        )

    except GenerationError as exc:

        print(
            "\nGENERATION ERROR:"
        )

        print(
            f"  {exc}"
        )


    except Exception as exc:

        print(
            "\nUNEXPECTED ERROR:"
        )

        print(
            f"  {type(exc).__name__}: "
            f"{exc}"
        )