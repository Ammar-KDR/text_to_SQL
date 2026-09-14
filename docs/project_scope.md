# Project Scope

## Project Overview

This project builds a production-oriented Text-to-SQL interface.

The system allows users to ask business questions using natural language and converts them into SQL queries that are safely executed against a PostgreSQL database.

The system focuses on reliability, safety, and explainability rather than only SQL generation.

---

# Goals

The main goals are:

- Convert natural language questions into SQL queries
- Ground SQL generation using database schema information
- Include business context when interpreting questions
- Prevent unsafe database operations
- Detect incorrect SQL answers
- Measure system reliability through evaluation

---

# Included Features

## Schema Retrieval

The system will:

- inspect database structure
- retrieve relevant tables and columns
- provide relationships between entities
- provide schema context to the LLM


---

## Business Context Retrieval

The system will support:

- business definitions
- terminology explanations
- company-specific rules

Examples:

- Revenue definitions
- Customer categories
- Business metrics


---

## SQL Generation

The system will:

- receive natural language questions
- generate SQL queries
- provide explanation of generated SQL
- provide confidence information


---

## SQL Validation

The system will validate:

- SQL syntax
- referenced tables and columns
- query safety
- query intent alignment


---

## Safe Execution

The system will include:

- read-only database access
- query limits
- execution logging
- result capture


---

## Hallucination Detection

The system will check:

- whether SQL answers the intended question
- whether results are plausible
- whether multiple approaches agree


---

## Evaluation Framework

The system will include:

- golden query dataset
- automated evaluation
- reliability metrics
- regression tracking


---

## Application Layer

The final system will expose:

- FastAPI backend
- Streamlit interface
- Docker deployment


---

# Excluded Features

## Agents

Not included.

Reason:

The project focuses on a controlled pipeline architecture.

Agent-based systems are reserved for a different project.

---

## Memory Systems

Not included.

Reason:

Persistent memory is unnecessary for this problem.

---

## Complex Frontend

Not included.

Reason:

The focus is AI engineering and system reliability, not frontend development.

---

## Enterprise Authentication

Not included.

Reason:

Authentication systems are outside the scope of this project.

---

## Distributed Systems

Not included.

Reason:

The goal is a production-style architecture, not large-scale infrastructure engineering.

---

# Success Criteria

The project is successful when:

- A user can ask business questions in natural language
- The system generates valid SQL
- Unsafe queries are blocked
- Incorrect interpretations are detected
- Results include confidence information
- The system can be evaluated objectively
