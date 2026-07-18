## Testing scope and limitations
- Automated suite (60 tests) covers pipeline logic, agents, orchestration,
  integration adapters, API contracts, reporting, and failure modes.
- SingleR (3rd annotation method) integrates via rpy2/R and requires a configured
  R + Bioconductor environment. It is verified manually (see MANUAL_TESTING.md) and
  excluded from CI, which cannot provision the R toolchain reliably. When R is
  unavailable, the pipeline degrades gracefully to 2-method consensus (FR-08).
- Performance validated observationally (see below), not via automated load tests.