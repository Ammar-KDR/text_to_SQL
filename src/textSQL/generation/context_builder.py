from textSQL.generation.models import (
    GenerationColumnContext,
    GenerationTableContext,
    GenerationJoinCondition,
    GenerationRelationshipContext,
    GenerationJoinPathContext,
    GenerationMetricContext,
    GenerationContext,
    GenerationTemporalConstraint,
)

from textSQL.retrieval.model import (
    RetrievedContext,
)


class GenerationContextBuilder:


    def build(
        self,
        retrieved_context: RetrievedContext,
    ) -> GenerationContext:

        tables = [
            self._build_table(table)
            for table
            in retrieved_context.tables
        ]


        relationships = [
            self._build_relationship(
                relationship
            )
            for relationship
            in retrieved_context.relationships
        ]


        join_paths = [
            self._build_join_path(
                join_path
            )
            for join_path
            in retrieved_context.join_paths
        ]


        metrics = [
            self._build_metric(metric)
            for metric
            in retrieved_context.metrics
        ]

        temporal_constraints = [

        self._build_temporal_constraint(
            constraint
        )

        for constraint
        in retrieved_context
        .temporal_constraints
    ]


        return GenerationContext(

            tables=tables,

            relationships=relationships,

            join_paths=join_paths,

            metrics=metrics,
            temporal_constraints=temporal_constraints
        )


    def _build_table(
        self,
        table,
    ) -> GenerationTableContext:

        columns = [

            GenerationColumnContext(

                name=column.name,

                data_type=column.data_type,

                nullable=column.nullable,

                is_primary_key=(
                    column.is_primary_key
                ),

                is_unique=(
                    column.is_unique
                ),

                description=(
                    column.description
                ),

                business_meaning=(
                    column.business_meaning
                ),
                allowed_values=(
    column.allowed_values
),
            )

            for column
            in table.columns
        ]


        return GenerationTableContext(

            qualified_name=(
                table.qualified_name
            ),

            description=(
                table.description
            ),

            business_role=(
                table.business_role
            ),

            primary_keys=(
                table.primary_keys
            ),

            columns=columns,
        )


    def _build_relationship(
        self,
        relationship,
    ) -> GenerationRelationshipContext:

        join_conditions = [

            GenerationJoinCondition(

                source_column=(
                    condition
                    .source_qualified_column
                ),

                target_column=(
                    condition
                    .target_qualified_column
                ),
            )

            for condition
            in relationship.join_conditions
        ]


        return GenerationRelationshipContext(

            relationship_id=(
                relationship.object_id
            ),

            source_table=(
                relationship
                .source_qualified_name
            ),

            target_table=(
                relationship
                .target_qualified_name
            ),

            relationship_type=(
                relationship
                .relationship_type
            ),

            source_cardinality=(
                relationship
                .source_cardinality
            ),

            target_cardinality=(
                relationship
                .target_cardinality
            ),

            through_table=(
                relationship
                .through_qualified_name
            ),

            join_conditions=(
                join_conditions
            ),

            business_meaning=(
                relationship
                .business_meaning
            ),
        )


    def _build_join_path(
        self,
        join_path,
    ) -> GenerationJoinPathContext:

        return GenerationJoinPathContext(

            tables=list(
                join_path.tables
            ),

            relationship_ids=[

                relationship.object_id

                for relationship
                in join_path.relationships
            ],
        )


    def _build_metric(
        self,
        metric,
    ) -> GenerationMetricContext:

        return GenerationMetricContext(

            name=metric.name,

            description=(
                metric.description
            ),

            domain=metric.domain,

            formula=metric.formula,

            authoritative_source=(
                metric.authoritative_source
            ),

            required_tables=list(
                metric.required_tables
            ),

            required_columns=list(
                metric.required_columns
            ),

            required_metrics=list(
                metric.required_metrics
            ),

            business_rules=list(
                metric.business_rules
            ),

            forbidden_sources=list(
                metric.forbidden_sources
            ),
        )
    def _build_temporal_constraint(
    self,
    constraint,
) -> GenerationTemporalConstraint:

        return GenerationTemporalConstraint(

            phrase=(
                constraint.phrase
            ),

            column=(
                constraint.column
            ),

            start_expression=(
                constraint.start_expression
            ),

            end_expression=(
                constraint.end_expression
            ),

            start_inclusive=(
                constraint.start_inclusive
            ),

            end_inclusive=(
                constraint.end_inclusive
            ),
        )