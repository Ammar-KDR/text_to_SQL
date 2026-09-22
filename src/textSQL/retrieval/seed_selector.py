import re

from textSQL.metadata.models import (
    MetricMetadata,
    TableMetadata,
)

from textSQL.retrieval.index import (
    MetadataIndex,
)

from textSQL.retrieval.model import (
    RetrievalCandidate,
)


class SeedSelector:


    def __init__(
        self,
        metadata_index: MetadataIndex,
        max_score_gap: float = 0.02,
        max_ranked_seeds: int = 2,
    ):

        self.metadata_index = metadata_index

        self.max_score_gap = max_score_gap

        self.max_ranked_seeds = (
            max_ranked_seeds
        )


    def select(
        self,
        question: str,
        candidates: list[
            RetrievalCandidate
        ],
    ) -> list[
        RetrievalCandidate
    ]:

        if not candidates:
            return []


        question_tokens = (
            self._tokens(question)
        )


        selected = {}


        # ----------------------------------------------------
        # 1. Explicit dense matches
        # ----------------------------------------------------

        for candidate in candidates:

            if self._explicit_match(
                question,
                candidate,
            ):

                selected[
                    candidate.object_id
                ] = candidate


        # ----------------------------------------------------
        # 2. If explicit intent exists,
        #    trust it over semantic top-1.
        # ----------------------------------------------------

        if selected:

            table_candidates = (
                self._find_explicit_tables(

                    question_tokens,

                    candidates,

                    list(
                        selected.values()
                    ),
                )
            )


            for candidate in table_candidates:

                selected[
                    candidate.object_id
                ] = candidate


            return list(
                selected.values()
            )


        # ----------------------------------------------------
        # 3. No explicit match:
        #    fall back to semantic ranking.
        # ----------------------------------------------------

        top = candidates[0]


        selected[
            top.object_id
        ] = top


        ranked_count = 1


        for candidate in candidates[1:]:

            if (
                ranked_count
                >=
                self.max_ranked_seeds
            ):
                break


            score_gap = (
                top.score
                -
                candidate.score
            )


            if (
                score_gap
                >
                self.max_score_gap
            ):
                continue


            selected[
                candidate.object_id
            ] = candidate

            ranked_count += 1


        return list(
            selected.values()
        )


    # ========================================================
    # EXPLICIT MATCHING
    # ========================================================


    def _explicit_match(
    self,
    question: str,
    candidate: RetrievalCandidate,
) -> bool:

        obj = (
            self.metadata_index
            .get_object(
                candidate.object_id
            )
        )


        if obj is None:
            return False


        phrases = []


        if isinstance(
            obj,
            MetricMetadata,
        ):

            phrases.append(
                obj.name
            )

            phrases.extend(
                obj.synonyms
            )


        elif isinstance(
            obj,
            TableMetadata,
        ):

            phrases.append(
                obj.name
            )


        else:
            return False


        return any(

            self._phrase_matches(
                question,
                phrase,
            )

            for phrase in phrases
        )


    # ========================================================
    # EXPLICIT TABLE / DIMENSION MATCHING
    # ========================================================


    def _find_explicit_tables(
        self,
        question_tokens: set[str],
        dense_candidates: list[
            RetrievalCandidate
        ],
        selected_candidates: list[
            RetrievalCandidate
        ],
    ) -> list[
        RetrievalCandidate
    ]:

        matching_tables = []


        unique_tables = {

            table.qualified_name:
                table

            for table
            in self.metadata_index
            .tables.values()

        }


        for table in (
            unique_tables.values()
        ):

            table_tokens = (
                self._table_tokens(
                    table.name
                )
            )


            if not table_tokens:
                continue


            if not table_tokens.issubset(
                question_tokens
            ):
                continue


            matching_tables.append(
                table
            )


        if not matching_tables:
            return []


        # Tables already guaranteed through
        # selected metric dependencies do not
        # need to become explicit seeds.

        required_tables = (
        self._required_tables(
            selected_candidates
        )
    )


    # ----------------------------------------------------
    # A selected metric may already provide the semantic
    # entity requested by the user.
    #
    # Example:
    #
    # top_products
    #     requires warehouse.dim_product
    #
    # Question:
    #     "top 10 products by revenue"
    #
    # In that case "product" is already represented by
    # dim_product. Do NOT additionally select
    # public.products merely because its bare name also
    # matches the word "products".
    # ----------------------------------------------------

        satisfied_entity_signatures = set()


        for required_table_name in required_tables:

            required_table = (
                self.metadata_index
                .get_table(
                    required_table_name
                )
            )


            if required_table is None:
                continue


            entity_tokens = (
                self._table_tokens(
                    required_table.name
                )
            )


            if not entity_tokens:
                continue


            if entity_tokens.issubset(
                question_tokens
            ):

                satisfied_entity_signatures.add(

                    frozenset(
                        entity_tokens
                    )

                )


        filtered_tables = []


        for table in matching_tables:

            # Exact dependency already exists.
            if (
                table.qualified_name
                in required_tables
            ):
                continue


            table_signature = frozenset(

                self._table_tokens(
                    table.name
                )

            )


            # Another required table already represents
            # this same semantic entity.
            #
            # warehouse.dim_product
            # and
            # public.products
            #
            # both normalize to {"product"}.
            if (
                table_signature
                in satisfied_entity_signatures
            ):
                continue


            filtered_tables.append(
                table
            )


        matching_tables = (
            filtered_tables
        )


        if not matching_tables:
            return []

        # ----------------------------------------------------
        # Use selected metrics/tables as graph anchors.
        #
        # Example:
        #
        # revenue
        #   -> warehouse.fact_sales
        #
        # "customer"
        #   could mean:
        #
        # public.customers
        # warehouse.dim_customer
        #
        # dim_customer is directly connected
        # to fact_sales, so it wins.
        # ----------------------------------------------------

        anchors = self._anchor_tables(
            selected_candidates
        )


        if anchors:

            scored = []


            for table in matching_tables:

                distance = (
                    self._minimum_graph_distance(
                        anchors,
                        table.qualified_name,
                    )
                )


                if distance is None:
                    continue


                scored.append(
                    (
                        distance,
                        table,
                    )
                )


            if scored:

                minimum = min(
                    distance
                    for distance, _
                    in scored
                )


                matching_tables = [

                    table

                    for distance, table
                    in scored

                    if distance == minimum

                ]


        # If ambiguity remains, prefer a table
        # that was actually returned by dense
        # retrieval.

        dense_map = {

            candidate.object_id:
                candidate

            for candidate
            in dense_candidates

        }


        dense_matches = [

            (
                dense_map[
                    f"table_{table.qualified_name}"
                ],
                table,
            )

            for table
            in matching_tables

            if (
                f"table_{table.qualified_name}"
                in dense_map
            )

        ]


        if dense_matches:

            dense_matches.sort(

                key=lambda item:
                    item[0].score,

                reverse=True,
            )


            return [
                dense_matches[0][0]
            ]


        # No evidence to choose between multiple
        # equally valid tables -> do not guess.

        if len(matching_tables) != 1:
            return []


        table = matching_tables[0]


        return [

            RetrievalCandidate(

                object_id=
                    f"table_{table.qualified_name}",

                object_type=
                    "table",

                object_name=
                    table.name,

                score=
                    1.0,

                source=
                    "explicit",
            )

        ]


    # ========================================================
    # GRAPH HELPERS
    # ========================================================


    def _anchor_tables(
        self,
        candidates: list[
            RetrievalCandidate
        ],
    ) -> set[str]:

        anchors = set()


        for candidate in candidates:

            obj = (
                self.metadata_index
                .get_object(
                    candidate.object_id
                )
            )


            if isinstance(
                obj,
                TableMetadata,
            ):

                anchors.add(
                    obj.qualified_name
                )


            elif isinstance(
                obj,
                MetricMetadata,
            ):

                table_names = list(
                    obj.required_tables
                )


                if obj.authoritative_source:

                    table_names.append(
                        obj.authoritative_source
                    )


                for table_name in (
                    table_names
                ):

                    table = (
                        self.metadata_index
                        .get_table(
                            table_name
                        )
                    )


                    if table is not None:

                        anchors.add(
                            table.qualified_name
                        )


        return anchors


    def _required_tables(
        self,
        candidates: list[
            RetrievalCandidate
        ],
    ) -> set[str]:

        required = set()


        for candidate in candidates:

            obj = (
                self.metadata_index
                .get_object(
                    candidate.object_id
                )
            )


            if not isinstance(
                obj,
                MetricMetadata,
            ):
                continue


            for table_name in (
                obj.required_tables
            ):

                table = (
                    self.metadata_index
                    .get_table(
                        table_name
                    )
                )


                if table is not None:

                    required.add(
                        table.qualified_name
                    )


        return required


    def _minimum_graph_distance(
        self,
        anchors: set[str],
        target: str,
    ) -> int | None:

        distances = []


        for anchor in anchors:

            if anchor == target:

                distances.append(0)

                continue


            path = (
                self.metadata_index
                .graph
                .find_path(
                    anchor,
                    target,
                )
            )


            if path is not None:

                distances.append(
                    len(path)
                )


        if not distances:
            return None


        return min(
            distances
        )


    # ========================================================
    # TEXT NORMALIZATION
    # ========================================================


    def _phrase_matches(
    self,
    question: str,
    phrase: str,
) -> bool:

        question_words = (
            self._normalized_words(
                question
            )
        )

        phrase_words = (
            self._normalized_words(
                phrase
            )
        )


        if not phrase_words:
            return False


        # Numbers often appear inside natural
        # ranking phrases:
        #
        # "top 10 products"
        # "top 5 customers"
        #
        # They should not prevent matching:
        #
        # "top products"
        question_words = [

            word

            for word in question_words

            if not word.isdigit()

        ]


        if (
            len(phrase_words)
            >
            len(question_words)
        ):
            return False


        phrase_length = (
            len(phrase_words)
        )


        for index in range(

            len(question_words)
            -
            phrase_length
            +
            1

        ):

            window = (
                question_words[
                    index:
                    index + phrase_length
                ]
            )


            if window == phrase_words:
                return True


        return False

    def _table_tokens(
        self,
        name: str,
    ) -> set[str]:

        tokens = (
            self._tokens(
                name
            )
        )


        tokens.discard(
            "dim"
        )

        tokens.discard(
            "fact"
        )


        return tokens


    @classmethod
    def _tokens(
        cls,
        text: str,
    ) -> set[str]:

        return set(
            cls._normalized_words(
                text
            )
        )

    @staticmethod
    def _normalized_words(
        text: str,
    ) -> list[str]:

        text = (
            text
            .lower()
            .replace(
                "_",
                " ",
            )
        )


        words = re.findall(
            r"[a-z0-9]+",
            text,
        )


        normalized = []


        for word in words:

            if (
                word.endswith("ies")
                and
                len(word) > 3
            ):

                word = (
                    word[:-3]
                    +
                    "y"
                )


            elif (
                word.endswith("s")
                and
                len(word) > 3
                and
                word not in {
                    "sales"
                }
            ):

                word = word[:-1]


            normalized.append(
                word
            )


        return normalized