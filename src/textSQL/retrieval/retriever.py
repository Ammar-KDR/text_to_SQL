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

from textSQL.retrieval.model import (
    RetrievedContext,
)

from textSQL.retrieval.seed_selector import (
    SeedSelector,
)
from textSQL.retrieval.temporal_resolver import (
    TemporalDependencyResolver,
)
class Retriever:


    def __init__(
        self,
        dense_retriever: DenseRetriever,
        dependency_resolver: DependencyResolver,
        graph_retriever: GraphRetriever,
        fusion: Fusion,
        context_builder: ContextBuilder,
        seed_selector: SeedSelector | None=None,
        temporal_resolver: (TemporalDependencyResolver| None) = None,
    ):

        self.dense_retriever = (
            dense_retriever
        )

        self.dependency_resolver = (
            dependency_resolver
        )

        self.graph_retriever = (
            graph_retriever
        )

        self.fusion = fusion

        self.context_builder = (
            context_builder
        )

        self.seed_selector = (
            seed_selector
        )
        self.temporal_resolver = (
            temporal_resolver
        )


    def retrieve(
        self,
        question: str,
        limit: int = 5,
    ) -> RetrievedContext:


        dense_candidates = (
            self.dense_retriever
            .retrieve(
                question,
                limit,
            )
        )
        if self.seed_selector is not None:

            seed_candidates = (
                self.seed_selector
                .select(
                    question,
                    dense_candidates,
                )
            )

        else:

            seed_candidates = (
                dense_candidates
            )


        dependency_candidates = (
            self.dependency_resolver
            .resolve(
                seed_candidates
            )
        )
        if (
            self.temporal_resolver
            is not None
        ):

            temporal_resolution = (
                self.temporal_resolver
                .resolve(
                    question,
                    dependency_candidates,
                )
            )


            resolved_candidates = (
                temporal_resolution
                .candidates
            )


            temporal_constraints = (
                temporal_resolution
                .constraints
            )

        else:

            resolved_candidates = (
                dependency_candidates
            )

            temporal_constraints = []


        graph_candidates = (
            self.graph_retriever
            .retrieve(
                resolved_candidates
            )
        )


        fused_candidates = (
            self.fusion
            .combine(

                seed_candidates,

                resolved_candidates,

                graph_candidates,

            )
        )


        context = (
            self.context_builder
            .build(

                question,

                fused_candidates,
        temporal_constraints=(
            temporal_constraints
        ),

            )
        )


        return context