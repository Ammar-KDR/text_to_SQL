from textSQL.database.connection import (
    engine,
)

from textSQL.metadata.config import (
    load_metadata_config,
)

from textSQL.metadata.extractor import (
    extract_database_metadata,
)

from textSQL.metadata.graph import (
    SchemaGraph,
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

from textSQL.retrieval.seed_selector import SeedSelector
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
# BUILD RETRIEVAL COMPONENTS
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

    query_encoder=
        query_encoder,

    vector_store=
        vector_store,

    metadata_index=
        metadata_index,
)


dependency_resolver = (
    DependencyResolver(
        metadata_index
    )
)


graph_retriever = (
    GraphRetriever(

        metadata_index=
            metadata_index,

        graph=
            metadata.graph,
    )
)


fusion = Fusion()


context_builder = (
    ContextBuilder(
        metadata_index
    )
)


retriever = Retriever(

    dense_retriever=
        dense_retriever,

    dependency_resolver=
        dependency_resolver,

    graph_retriever=
        graph_retriever,

    fusion=
        fusion,

    context_builder=
        context_builder,
    seed_selector=seed_selector
)


# ============================================================
# DISPLAY
# ============================================================


def print_context(
    question,
    context,
):

    print(
        "\n"
        +
        "=" * 80
    )

    print(
        f"QUESTION: {question}"
    )

    print(
        "=" * 80
    )


    # --------------------------------------------------------
    # METRICS
    # --------------------------------------------------------

    print(
        "\nMETRICS:"
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
            "    authoritative_source: "
            f"{metric.authoritative_source}"
        )

        print(
            "    formula: "
            f"{metric.formula}"
        )

        print(
            "    required_tables: "
            f"{metric.required_tables}"
        )

        print(
            "    required_columns: "
            f"{metric.required_columns}"
        )


    # --------------------------------------------------------
    # TABLES
    # --------------------------------------------------------

    print(
        "\nTABLES:"
    )

    if not context.tables:

        print(
            "  <none>"
        )

    for table in context.tables:

        print(
            f"  - {table.qualified_name}"
        )


    # --------------------------------------------------------
    # RELATIONSHIPS
    # --------------------------------------------------------

    print(
        "\nRELATIONSHIPS:"
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


        for join in (
            relationship.join_conditions
        ):

            print(

                "      "
                f"{join.source_qualified_column}"
                " = "
                f"{join.target_qualified_column}"

            )


    # --------------------------------------------------------
    # JOIN PATHS
    # --------------------------------------------------------

    print(
        "\nJOIN PATHS:"
    )

    if not context.join_paths:

        print(
            "  <none>"
        )


    for index, path in enumerate(
        context.join_paths,
        start=1,
    ):

        print(
            f"  PATH {index}:"
        )

        print(
            "    "
            +
            " -> ".join(
                path.tables
            )
        )


        for relationship in (
            path.relationships
        ):

            for join in (
                relationship
                .join_conditions
            ):

                print(

                    "      JOIN: "
                    f"{join.source_qualified_column}"
                    " = "
                    f"{join.target_qualified_column}"

                )


    # --------------------------------------------------------
    # TRACE
    # --------------------------------------------------------

    print(
        "\nTRACE:"
    )

    for trace in context.trace:

        print(

            "  - "
            f"{trace.object_type}: "
            f"{trace.object_name} "
            f"score={trace.score:.6f}"

        )


# ============================================================
# REAL QUESTIONS
# ============================================================


questions = [

    "show revenue",

    "show revenue by customer",

    "show completed payments",

    "what were the top 10 products by revenue?",

]


for question in questions:

    dense = dense_retriever.retrieve(
    question,
    limit=5,
)

    print(
        "\nRAW DENSE RESULTS:"
    )

    for candidate in dense:

        print(
            f"  {candidate.score:.4f} | "
            f"{candidate.object_type:<10} | "
            f"{candidate.object_name}"
        )


    selected = seed_selector.select(
    question,
    dense,
)


    print(
        "\nSELECTED SEEDS:"
    )


    for candidate in selected:

        print(

            f"  {candidate.score:.4f} | "
            f"{candidate.object_type:<10} | "
            f"{candidate.object_name}"

    )
    context = retriever.retrieve(
        question,
        limit=5,
    )
    

    print_context(
        question,
        context,
    )