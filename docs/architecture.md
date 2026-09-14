# Text-to-SQL System Architecture

## Overview

This project builds a schema-aware Text-to-SQL system that converts natural language business questions into validated SQL queries.

The system is designed around the principle that SQL generation alone is insufficient.
The generated query must be grounded in database structure, validated for safety, and checked for correctness.

---

## High-Level Flow

User Question

↓

Business Context Retrieval
+
Schema Retrieval

↓

Context Construction

↓

LLM SQL Generation

↓

SQL Validation

↓

Safety Guardrails

↓

Read-only Database Execution

↓

Result Verification

↓

Confidence Score

---

## Components

### Schema Retrieval

Purpose:

Provide the LLM with relevant database knowledge.

Responsibilities:

- Retrieve relevant tables
- Retrieve columns
- Retrieve relationships
- Provide schema context


### Business Context Retrieval

Purpose:

Provide company-specific definitions.

Examples:

- Revenue definitions
- Customer segmentation rules
- Business terminology


### SQL Generation

Purpose:

Convert natural language questions into SQL.

Input:

- User question
- Schema context
- Business context


Output:

- SQL query
- Explanation
- Confidence estimate


### Validation Layer

Purpose:

Verify that generated SQL is safe and meaningful.

Responsibilities:

- Syntax validation
- Query inspection
- Safety checks


### Execution Layer

Purpose:

Execute validated queries safely.

Rules:

- Read-only access
- Limited results
- Audit logging