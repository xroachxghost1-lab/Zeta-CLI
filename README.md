# Zeta-CLI

Persistent autonomous coding agent for Termux powered by Inception Mercury.

## Purpose

Zeta-CLI is designed as a long-running autonomous software-engineering
system rather than a one-shot chatbot.

The architecture separates:

- model reasoning
- orchestration
- tools
- workspace management
- verification
- persistence
- context
- memory
- recovery
- watchdog supervision

## Primary Models

### Mercury 2

Used for:

- reasoning
- planning
- tool selection
- debugging
- verification reasoning
- structured decisions
- tool calling
- structured outputs
- streaming

### Mercury Edit 2

Used as the specialized editing subsystem for:

- FIM
- autocomplete
- Next Edit
- precision code editing

## Core Properties

Zeta-CLI is designed to be:

- persistent
- resumable
- verification-driven
- failure-aware
- context-aware
- tool-safe
- progress-driven
- capable of long-running operation

## Requirements

- Python 3.10+
- Termux/Linux
- Rust toolchain when native dependencies require compilation
- Inception API access

## API Configuration

Set the API key through the environment:

    export INCEPTION_API_KEY="..."

Never commit API keys or other secrets.

## Installation

From the project directory:

    python -m pip install -e .

## Development

Run the test suite:

    python -m pytest -q

## Architecture

See:

    ARCHITECTURE.md

## Roadmap

See:

    ROADMAP.md

## Current Development Rule

Zeta-CLI is being built from a clean architecture.

The legacy `~/mozeta` project is not a source of implementation code for
this project.

The execution engine will not become a monolithic subsystem.

Implementation proceeds in controlled layers with tests before major
integration.

## Planned CLI

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

Interactive mode:

    zeta

## Completion Philosophy

Zeta-CLI does not consider work complete because the model claims success.

Completion requires independently collected evidence and successful
verification.

## Long-Running Operation

The runtime is designed to survive:

- API outages
- rate limits
- network failures
- tool failures
- verification failures
- context growth
- repeated strategies
- process interruption
- Termux shutdown

Persistent state and checkpoints allow interrupted runs to resume.

## Security

Secrets must never be written to:

- source files
- run state
- session history
- logs
- checkpoints
- committed configuration

Logs must redact credentials and authorization material.
