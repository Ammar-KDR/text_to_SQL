from textSQL.retrieval.model import (
    FusedCandidate,
)


class Fusion:


    def __init__(
        self,
        k: int = 60,
    ):

        self.k = k


    def combine(
        self,
        *candidate_lists,
    ):

        scores = {}

        candidates = {}

        seen_source_votes = set()


        for candidate_list in candidate_lists:

            for rank, candidate in enumerate(
                candidate_list,
                start=1,
            ):

                vote_key = (

                    candidate.object_id,

                    candidate.source,

                )


                # The same retrieval source
                # must not vote more than once
                # for the same metadata object.
                #
                # Example:
                #
                # Dense candidate appears again
                # inside DependencyResolver output.
                #
                # That is still ONE dense signal.
                if (
                    vote_key
                    in seen_source_votes
                ):

                    continue


                seen_source_votes.add(
                    vote_key
                )


                rrf = (

                    1

                    /

                    (
                        self.k
                        +
                        rank
                    )
                )


                scores[
                    candidate.object_id
                ] = (

                    scores.get(
                        candidate.object_id,
                        0,
                    )

                    +

                    rrf
                )


                if (
                    candidate.object_id
                    not in candidates
                ):

                    candidates[
                        candidate.object_id
                    ] = []


                candidates[
                    candidate.object_id
                ].append(
                    candidate
                )


        fused = []


        for (
            object_id,
            score,
        ) in scores.items():

            original = (
                candidates[
                    object_id
                ]
            )

            first = (
                original[0]
            )


            sources = list(

                dict.fromkeys(

                    candidate.source

                    for candidate
                    in original

                )
            )


            fused.append(

                FusedCandidate(

                    object_id=
                        object_id,

                    object_type=
                        first.object_type,

                    object_name=
                        first.object_name,

                    rrf_score=
                        score,

                    sources=
                        sources,

                    original_candidates=
                        original,
                )
            )


        return sorted(

            fused,

            key=lambda candidate:
                candidate.rrf_score,

            reverse=True,
        )