# Eval Report — all

- cases: 9
- passed: 9
- avg score: 0.9683

## Cases

- **nl2sql-001** (nl2sql): score=1.0 passed=True
  - sql_execution: True (got=[[2]] expected=[[2]])
  - judge: 1.0 — offline heuristic judge
- **nl2sql-002** (nl2sql): score=1.0 passed=True
  - sql_execution: True (got=[[1, 'Alice', '2024-01-05'], [2, 'Bob', '2024-01-10'], [3, 'Carol', '2024-02-01'], [4, 'Dave', '2024-02-15']] expected=[[1, 'Alice', '2024-01-05'], [2, 'Bob', '2024-01-10'], [3, 'Carol', '2024-02-01'], [4, 'Dave', '2024-02-15']])
  - judge: 1.0 — offline heuristic judge
- **nl2sql-003** (nl2sql): score=1.0 passed=True
  - sql_execution: True (got=[[19.5]] expected=[[19.5]])
  - judge: 1.0 — offline heuristic judge
- **nl2sql-004** (nl2sql): score=1.0 passed=True
  - sql_execution: True (got=[[4]] expected=[[4]])
  - judge: 1.0 — offline heuristic judge
- **metric-001** (metric): score=1.0 passed=True
  - metric_exact: True (got=2.0 expected=2.0)
  - judge: 1.0 — offline heuristic judge
- **metric-002** (metric): score=1.0 passed=True
  - metric_exact: True (got=123.5 expected=123.5)
  - judge: 1.0 — offline heuristic judge
- **metric-003** (metric): score=1.0 passed=True
  - metric_exact: True (got=30.875 expected=30.875)
  - judge: 1.0 — offline heuristic judge
- **doc-001** (doc): score=1.0 passed=True
  - doc_overlap: True (overlap=1.00)
  - judge: 1.0 — offline heuristic judge
- **doc-002** (doc): score=0.7143 passed=True
  - doc_overlap: True (overlap=0.71)
  - judge: 0.7142857142857143 — offline heuristic judge