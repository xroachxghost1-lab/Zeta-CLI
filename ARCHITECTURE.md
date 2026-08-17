# Zeta-CLI Architecture

Zeta-CLI is a persistent autonomous software-engineering agent built around the Inception Mercury API.

## Core Principles

1. API-native
2. Persistent
3. Resumable
4. Verification-driven
5. Progress-driven
6. Failure-aware
7. Context-aware
8. Tool-safe
9. Model-capability-aware
10. Designed for continuous operation

## System Architecture

```text
                         ZETA-CLI
                            |
                       SUPERVISOR
                            |
                       AGENT KERNEL
                            |
              +-------------+-------------+
              |             |             |
           CONTEXT        TOOLS       VERIFICATION
              |             |             |
              +-------------+-------------+
                            |
                      MODEL GATEWAY
                       /           \
                      /             \
                MERCURY 2      MERCURY EDIT 2
```

## Authoritative Lifecycle

BOOT
  |
  v
PLAN
  |
  v
EXECUTE <----------------------+
  |                            |
  v                            |
ASSESS                       RECOVER
  |                            ^
  +---- progress --------------+
  |
  +---- problem ----------------+
  |
  v
VERIFY
  |
  +---- FAIL ------------------+
  |
  +---- PASS --> COMPLETE

COMPLETE is terminal.

No model response, tool, or subsystem may independently declare a run
complete. Completion is controlled by the authoritative state machine and
requires successful independent verification.

## Persistent Run State

Every run has durable state containing:

- run ID
- goal
- creation timestamp
- update timestamp
- phase
- status
- current task
- plan
- iteration
- recovery count
- verification attempts
- context revision
- tool revision
- evidence
- checkpoints
- failures
- metrics
- completion state

The state store must provide:

- atomic writes
- crash recovery
- schema versioning
- migrations
- corruption detection
- checkpoint recovery
- explicit terminal states

## Supervisor

The supervisor provides:

- heartbeat
- watchdog
- API health monitoring
- rate-limit management
- retry management
- context monitoring
- persistence monitoring
- execution timeouts
- no-progress detection
- repeated-reasoning detection
- repeated-tool detection
- shutdown and recovery

The supervisor can interrupt an unhealthy agent loop.

The model cannot disable the supervisor.

## Agent Kernel

The kernel coordinates:

- planner
- executor
- assessor
- recovery manager
- verification coordinator

The kernel does not directly perform filesystem or shell operations.


## Model Gateway

The model gateway provides an authoritative abstraction over Inception.

### Mercury 2

Mercury 2 is the primary reasoning and agent model.

Responsibilities include:

- planning
- reasoning
- tool selection
- debugging
- verification reasoning
- structured decisions
- tool calling
- structured outputs
- streaming

### Mercury Edit 2

Mercury Edit 2 is a specialized editing service.

Responsibilities include:

- FIM
- autocomplete
- Next Edit
- precision code editing

Mercury Edit 2 is not treated as interchangeable with Mercury 2.

## Model Routing

The routing layer discovers available models and capabilities rather than
assuming the server never changes.

Example routing:

| Task | Model |
|---|---|
| Planning | Mercury 2 |
| Reasoning | Mercury 2 |
| Tool selection | Mercury 2 |
| Debugging | Mercury 2 |
| Verification reasoning | Mercury 2 |
| Structured decisions | Mercury 2 |
| FIM | Mercury Edit 2 |
| Next Edit | Mercury Edit 2 |

## Reasoning Policy

Mercury 2 reasoning effort is represented by:

- instant
- low
- medium
- high

Reasoning can escalate when necessary:

medium -> failure -> high

Maximum reasoning is not automatically used for every operation.

## API Reliability

Requests follow:

REQUEST
  |
  v
VALIDATE
  |
  v
BUDGET
  |
  v
RATE LIMITER
  |
  v
INCEPTION API
  |
  v
CLASSIFY RESPONSE

Errors are normalized into categories including:

- authentication
- rate limit
- timeout
- network
- bad request
- model unavailable
- context overflow
- server error
- tool error
- protocol error

Each category has a defined recovery policy.

## Circuit Breaker

HEALTHY
   |
 failures
   v
DEGRADED
   |
 retries
   v
CIRCUIT OPEN

When the API is unavailable, Zeta persists the run and waits safely rather
than destroying state.

When health returns, the circuit closes and the run resumes.


## Tool Architecture

Tools are isolated capabilities.

### Filesystem

- read
- write
- edit
- list
- search
- stat

### Shell

- execute
- background
- terminate
- inspect

### Project

- inspect
- detect language
- detect build system
- detect tests

### Testing

- pytest
- generic
- targeted

### Verification

- filesystem
- command
- artifact
- acceptance

Every tool invocation produces a structured ToolExecution record containing:

- ID
- name
- arguments
- start time
- finish time
- timeout
- attempt
- status
- stdout
- stderr
- result
- fingerprint

## Tool Safety

Every tool receives:

- timeout
- maximum output limit
- working directory
- environment policy
- cancellation token
- attempt number

Shell execution must support cancellation.

## Progress Engine

Progress is represented by a structured progress record.

Tracked dimensions include:

- files changed
- files created
- files deleted
- tests changed
- tests passed
- tests failed
- task state changed
- tool result changed
- verification state changed
- strategy changed
- objective distance

No progress triggers watchdog evaluation and potential recovery.

## Watchdog

The watchdog detects:

- repeated tool calls
- identical tool results
- repeated reasoning
- unchanged workspace
- failed recovery
- stalled iterations
- excessive API retries
- context pressure
- verification loops

Possible watchdog actions include:

- request strategy change
- change tool
- change reasoning mode
- re-inspect workspace
- reduce context
- recover
- re-plan
- escalate
- safely stop and checkpoint


## Verification

Verification is an independent subsystem.

Components:

- evidence collector
- filesystem verifier
- command verifier
- test verifier
- artifact verifier
- acceptance verifier
- completion policy

The model saying:

VERIFIED: PASS

does not constitute verification.

Only independent verification evidence can transition:

VERIFY -> COMPLETE

## Evidence

Evidence records contain:

- evidence ID
- type
- source
- timestamp
- command/tool
- input
- output
- fingerprint
- validity
- metadata

Examples:

- test passed
- file exists
- file contains expected symbol
- command returned exit code 0
- artifact generated
- acceptance criterion satisfied

## Verification Failure

Verification failures follow:

VERIFY
  |
  v
Failure Classifier
  |
  v
Recovery Plan
  |
  v
EXECUTE
  |
  v
ASSESS
  |
  v
VERIFY

Every verification attempt is persisted.

## Completion Policy

Completion requires all applicable conditions to be satisfied:

1. execution completed
2. required artifacts exist
3. required tests pass
4. acceptance criteria are satisfied
5. independent verification succeeds
6. completion state is persisted

A model-generated completion claim is never sufficient evidence.


## Context Engine

Context is tracked explicitly:

- system instructions
- goal
- active plan
- current task
- relevant files
- relevant tool results
- verification evidence
- recovery history
- memory
- compacted history

The context manager tracks:

- model context limit
- reserved output budget
- system prompt
- tool definitions
- recent messages
- important historical messages
- task state
- verification evidence

Context compaction is deliberate and structured.

Arbitrary message deletion is prohibited.

## Memory

Session history and durable memory are separate.

Session = what happened during this run.

Memory = durable knowledge worth retaining.

Memory records contain:

- ID
- content
- category
- source
- creation timestamp
- update timestamp
- confidence
- relevance

Memory must not silently replace authoritative run state.

## Mercury Edit 2 Integration

Mercury Edit 2 is implemented as a dedicated editor service.

EditEngine
  |
  +-- FileContext
  +-- CursorContext
  +-- RecentSnippets
  +-- EditHistory
  +-- DiffBuilder
  +-- MercuryEditClient

The Next Edit integration preserves the API's required context structure,
including recent snippets, current file context, editable region, and
edit history.

FIM/autocomplete requests are handled separately from autonomous agent
reasoning.

## Workspace Intelligence

Workspace inspection is independent from model reasoning.

The workspace subsystem provides:

- project inspection
- language detection
- build-system detection
- test detection
- filesystem snapshots
- file metadata
- change detection

Workspace snapshots may be used by the progress engine and verification
system.


## Crash Recovery

Critical invariant:

Every meaningful state transition is persisted before the next irreversible
operation.

Typical sequence:

checkpoint
   |
persist
   |
execute tool
   |
persist result
   |
advance state

After a Termux interruption:

restart
   |
load checkpoint
   |
identify unfinished operation
   |
recover safely
   |
resume

An interrupted tool invocation must never corrupt the authoritative run state.

## Recovery Manager

Recovery is a first-class subsystem.

It classifies failures and selects a recovery strategy.

Possible strategies include:

- retry
- backoff
- alternate tool
- alternate model capability
- reasoning escalation
- context reduction
- workspace reinspection
- task replanning
- verification retry
- checkpoint and wait
- safe termination

Recovery attempts are bounded and persisted.

## Session Management

A session contains:

- run identity
- event history
- checkpoints
- current state
- context revisions
- tool revisions
- recovery history
- verification history

A resumed session must reconstruct state from persisted data rather than
depending on in-memory objects from the previous process.

## Atomic State Transitions

State transitions follow:

VALIDATE
  |
CREATE EVENT
  |
PERSIST EVENT
  |
UPDATE STATE
  |
PERSIST STATE
  |
CONTINUE

The state store must avoid partially written authoritative state.

## Shutdown

Graceful shutdown follows:

Ctrl-C
  |
STOP REQUESTED
  |
cancel active model/tool operation
  |
persist checkpoint
  |
persist context
  |
persist metrics
  |
STOPPED

A stopped run can later be resumed:

zeta resume <run-id>

## Metrics

Long-running runs track:

- iterations
- model calls
- tool calls
- tool failures
- verification attempts
- recoveries
- no-progress events
- context compactions
- API retries
- API errors
- elapsed time
- token estimates
- cost estimates

Metrics are persisted so a process restart does not erase operational history.

## Non-Stop Runtime

Zeta is designed for extremely long-running operation.

The runtime must tolerate:

- API outages
- rate limits
- temporary network failures
- tool failures
- verification failures
- context growth
- repeated strategies
- Termux interruption
- process restart

The system must checkpoint before shutdown and resume from authoritative
state afterward.


## CLI

Planned commands:

zeta run "build X"
zeta resume <run-id>
zeta status
zeta runs
zeta stop <run-id>
zeta verify <run-id>
zeta models
zeta config
zeta memory
zeta doctor

Foreground interactive mode:

zeta

## Doctor

zeta doctor will diagnose:

- Python
- filesystem permissions
- workspace
- API key configuration
- API connectivity
- Inception models
- tool availability
- pytest
- shell
- storage
- state directory
- configuration

## Security

Secrets must never be persisted in run state.

Never persist:

- API keys
- authorization headers
- access tokens
- refresh tokens
- secret environment variables

Logs must redact credentials and sensitive authorization material.

Configuration should support environment variables and secure local
configuration without embedding credentials in source code.

## Testing Strategy

Tests are organized into:

tests/
  unit/
  integration/
  e2e/
  fixtures/

Unit tests cover isolated components.

Integration tests cover subsystem boundaries.

End-to-end tests cover complete agent workflows.

Fixtures provide deterministic test environments and simulated API/tool
responses.

## Stress Testing

The stress suite must cover:

- long-running execution
- crash recovery
- repeated tool calls
- repeated results
- context growth
- API failures
- rate limits
- tool failures
- verification failures
- recovery loops
- process interruption
- resume-after-crash
- 1000+ iteration runs
- memory stability

## Architectural Invariants

The following invariants must always hold:

1. The model does not own application lifecycle.
2. The supervisor cannot be disabled by the model.
3. The kernel does not directly execute tools.
4. Tool execution is bounded and cancellable.
5. Completion requires independent verification.
6. Authoritative state is persisted before irreversible operations.
7. Session history is separate from durable memory.
8. Mercury 2 and Mercury Edit 2 are separate capability paths.
9. Context management is explicit.
10. Recovery is persisted.
11. Secrets are never stored in run state.
12. A crashed process must be recoverable.
13. A completed run cannot silently return to active execution.
14. No-progress detection must be independent of model self-reporting.
15. The system must never rely on a single model response as proof of
    completion.

## Final Architecture Rule

Zeta will not recreate the old monolithic engine.

The kernel should remain small:

Supervisor
    |
Kernel
    |
Phase transition
    |
Subsystem
    |
Event
    |
State persistence

Responsibilities belong to dedicated subsystems.

The architecture is intentionally designed before implementation so that
the system can evolve without turning the execution engine into a monolith.

