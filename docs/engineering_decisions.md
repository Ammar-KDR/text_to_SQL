# Engineering Decision

Decision:

Create a realistic e-commerce OLTP and OLAP database before implementing Text-to-SQL generation.

Alternatives:

Use a simplified toy schema.

Reason:

Text-to-SQL performance depends heavily on schema clarity,
relationships, and business semantics.

A realistic schema allows evaluation of:
- schema understanding
- business reasoning
- SQL generation
- validation

Tradeoff:

Higher initial design complexity.

Impact:

Future retrieval, generation, and evaluation components
operate on a realistic production-like environment.