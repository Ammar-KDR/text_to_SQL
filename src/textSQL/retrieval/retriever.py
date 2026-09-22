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

class Retriever:


    def __init__(
        self,
        dense_retriever: DenseRetriever,
        dependency_resolver: DependencyResolver,
        graph_retriever: GraphRetriever,
        fusion: Fusion,
        context_builder: ContextBuilder,
        seed_selector: SeedSelector | None=None,
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


        graph_candidates = (
            self.graph_retriever
            .retrieve(
                dependency_candidates
            )
        )


        fused_candidates = (
            self.fusion
            .combine(

                seed_candidates,

                dependency_candidates,

                graph_candidates,

            )
        )


        context = (
            self.context_builder
            .build(

                question,

                fused_candidates,

            )
        )


        return context