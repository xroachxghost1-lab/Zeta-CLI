# Zeta-CLI Development Roadmap

## Phase 0 — Clean Foundation

- [ ] Project skeleton
- [ ] Packaging
- [ ] CLI entrypoint
- [ ] Configuration
- [ ] Logging
- [ ] Error hierarchy
- [ ] Architecture specification

## Phase 1 — Inception API Layer

- [ ] Official inceptionai SDK
- [ ] Mercury 2 client
- [ ] Mercury Edit 2 client
- [ ] Chat completions
- [x] Streaming
- [ ] Diffusion streaming
- [ ] Reasoning effort
- [ ] Tool calling
- [ ] Structured outputs
- [ ] FIM
- [ ] Next Edit
- [ ] Model discovery
- [ ] API capability discovery
- [ ] Rate-limit handling
- [ ] Retry/backoff
- [ ] API error normalization
- [ ] Circuit breaker
- [ ] API health monitoring

## Phase 1 — Completed Implementation Notes

### Streaming

Implemented the Inception streaming adapter in `src/zeta_cli/api/inception.py`.

- Exposes `InceptionProvider.stream()`
- Uses the Inception SDK streaming chat-completions interface
- Converts SDK chunks into `StreamEvent` objects
- Preserves text deltas
- Preserves finish reasons
- Preserves model information
- Preserves reasoning summaries and reasoning status
- Preserves tool-call deltas
- Normalizes connection/API failures through the existing API error hierarchy
- Exposes streaming through `APIClient.stream()`

### Verification

Targeted provider and API-client tests pass:

- `tests/unit/test_inception_provider.py`
- `tests/unit/test_api_client.py`
- Result: **29 passed**

## Phase 2 — Tool System

- [ ] Tool registry
- [ ] Tool schemas
- [ ] Dispatcher
- [ ] Timeout handling
- [ ] Cancellation
- [ ] Retry policy
- [ ] Safety policy
- [ ] Tool result normalization
- [ ] Tool fingerprinting
- [ ] Tool history

## Phase 3 — Agent Core

- [x] Planner
- [x] Executor
- [ ] Assessor
- [ ] Decision engine
- [ ] Authoritative phase machine
- [ ] Goal tracking
- [ ] Task tracking
- [ ] Progress tracking
- [ ] Recovery coordination

## Phase 4 — Persistence

- [ ] Run IDs
- [ ] Session storage
- [ ] Event storage
- [ ] Checkpoints
- [ ] Atomic writes
- [ ] Crash recovery
- [ ] State migrations
- [ ] Corruption detection
- [ ] Resume
- [ ] COMPLETE protection

## Phase 5 — Context Engine

- [ ] Token budgeting
- [ ] Context accounting
- [ ] Semantic compaction
- [ ] Priority messages
- [ ] Tool-result compression
- [ ] Historical summaries
- [ ] Context recovery
- [ ] Context revision tracking

## Phase 6 — Verification

- [ ] Verification policies
- [ ] Evidence collection
- [ ] Filesystem verification
- [ ] Test verification
- [ ] Artifact verification
- [ ] Command verification
- [ ] Acceptance verification
- [ ] Independent verification
- [ ] Verification retry limits
- [ ] False completion prevention
- [ ] Completion policy

## Phase 7 — Watchdog

- [ ] Repeated calls
- [ ] Repeated results
- [ ] Repeated reasoning
- [ ] No workspace progress
- [ ] Stall detection
- [ ] Recovery budgets
- [ ] Strategy switching
- [ ] Context pressure detection
- [ ] Safe checkpointing
- [ ] Supervisor heartbeat

## Phase 8 — Memory

- [ ] Persistent memory
- [ ] Task memory
- [ ] Workspace memory
- [ ] Learned patterns
- [ ] Memory retrieval
- [ ] Memory compaction
- [ ] Memory relevance
- [ ] Memory confidence
- [ ] Memory safety

## Phase 9 — Mercury Edit

- [ ] FIM
- [ ] Next Edit
- [ ] Edit context builder
- [ ] Cursor awareness
- [ ] Recent snippets
- [ ] Diff history
- [ ] Edit validation

## Phase 10 — Non-Stop Runtime

- [ ] Long-run tests
- [ ] Crash injection
- [ ] API failure injection
- [ ] Rate-limit simulation
- [ ] Tool failure simulation
- [ ] Context exhaustion simulation
- [ ] Verification failure simulation
- [ ] Resume-after-crash tests
- [ ] 1000+ iteration tests
- [ ] Memory stability tests
- [ ] Long-duration resource monitoring

## Phase 11 — Production Hardening

- [ ] Secure secret handling
- [ ] Log redaction
- [ ] Configuration validation
- [ ] Resource limits
- [ ] Graceful shutdown
- [ ] Signal handling
- [ ] Health monitoring
- [ ] Diagnostics
- [ ] Recovery reports
- [ ] Performance benchmarks
- [ ] Documentation
- [ ] Release validation

## Completion Standard

A roadmap phase is not considered complete because code exists.

A phase is complete only when:

1. implementation exists
2. targeted tests exist
3. tests pass
4. integration behavior is verified where applicable
5. failure behavior is tested
6. documentation reflects the implementation
7. the roadmap item is explicitly checked

