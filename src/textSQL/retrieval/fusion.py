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


        for candidate_list in candidate_lists:

            for rank, candidate in enumerate(
                candidate_list,
                start=1,
            ):

                rrf = (
                    1 /
                    (
                        self.k + rank
                    )
                )


                scores[
                    candidate.object_id
                ] = (
                    scores.get(
                        candidate.object_id,
                        0
                    )
                    +
                    rrf
                )


                if candidate.object_id not in candidates:

                    candidates[
                        candidate.object_id
                    ] = []


                candidates[
                    candidate.object_id
                ].append(
                    candidate
                )

        fused = []


        for object_id, score in scores.items():

            original = candidates[object_id]

            first = original[0]


            fused.append(

                FusedCandidate(

                    object_id=object_id,

                    object_type=
                    first.object_type,

                    object_name=
                    first.object_name,

                    rrf_score=score,

                    sources=[
                        c.source
                        for c in original
                    ],

                    original_candidates=original,

                )
            )


        return sorted(
            fused,
            key=lambda x: x.rrf_score,
            reverse=True,
        )