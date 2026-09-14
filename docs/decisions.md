# Architecture Decision Records

## Decision 1: Use PostgreSQL as the Database Engine

### Decision

Use PostgreSQL instead of SQLite.

### Reason

The goal is to simulate a realistic enterprise database environment.

PostgreSQL provides:

- real SQL behavior
- relational constraints
- realistic query planning
- production-like execution patterns

### Alternatives Considered

SQLite

### Tradeoff

SQLite would be simpler to set up, but it does not represent the database environment commonly used in production systems.

### Impact

The system will be designed around PostgreSQL from the beginning.

---

## Decision 2: Provider-Independent LLM Interface

### Decision

Create an abstraction layer between the application and the LLM provider.

### Reason

The system should not depend on a single model provider.

The application should be able to switch between:

- local models
- OpenAI models
- other compatible providers

without rewriting the core pipeline.

### Alternatives Considered

Directly calling one provider SDK everywhere.

### Tradeoff

The abstraction adds initial complexity.

### Impact

LLM calls will go through a unified interface.

---

## Decision 3: No Agent Architecture

### Decision

Do not use autonomous agents.

### Reason

The problem can be solved with a controlled pipeline.

The goal is:

- predictable execution
- validation
- safety
- explainability

Agents introduce unnecessary complexity.

### Alternatives Considered

Agent-based orchestration.

### Tradeoff

Agents may provide flexibility, but they reduce predictability.

### Impact

The system will use explicit pipeline stages.

---

## Decision 4: Separate Database Knowledge and Business Knowledge

### Decision

Treat schema information and business definitions as separate context sources.

### Reason

Knowing the database structure is not enough.

Example:

The database may contain:

orders.total_amount
payments.amount
refunds.amount


but the company decides:


Revenue = successful payments - refunds


The LLM needs both technical and business context.

### Tradeoff

Requires additional retrieval logic.

### Impact

The system can answer business questions more accurately.

---

## Decision 5: Validation Before Execution

### Decision

Never execute generated SQL directly.

### Reason

LLM-generated SQL can:

- access incorrect tables
- generate unsafe operations
- answer the wrong question

Validation is required before database execution.

### Impact

All queries pass through safety and verification layers.
