# Security Policy

## Reporting a vulnerability

Please do not publish exploitable security issues in a public issue. Use GitHub's private vulnerability reporting feature when it is available for this repository.

This project executes commands supplied by task definitions. Those commands are trusted input. The evaluator's temporary working directory prevents accidental task-state sharing, but it is **not** an operating-system security sandbox.

For untrusted workloads, run the evaluator inside an appropriately restricted container or other sandbox and apply resource, filesystem, and network controls outside this application.
