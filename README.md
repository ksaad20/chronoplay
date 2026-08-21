# ChronoPlay

> **Deterministic, resilient, time-synchronized broadcast playout and channel automation.**

ChronoPlay is an open-source broadcast playout and channel automation platform designed to evolve from a deterministic scheduling engine into a complete, resilient, cross-platform broadcast-control system.

Its long-term objective is to provide the software layer required to operate automated television, streaming, digital signage, and other scheduled media channels with deterministic timing, fault recovery, observability, and programmable control.

---

## Vision

ChronoPlay is being engineered toward a maximalist channel-automation architecture:

```text
                         CHRONOPLAY
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
    Scheduling            Playout             Live Input
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
                       Channel Engine
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
       Primary            Backup            Emergency
       Content            Content             Source
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
                     Processing Pipeline
                             │
              ┌──────────────┼──────────────┐
              │              │              │
            Encode         Monitor        Record
              │              │              │
              └──────────────┼──────────────┘
                             │
                   Distribution Layer
                             │
             ┌───────────────┼───────────────┐
             │               │               │
            RTMP            SRT            Other
             │               │               │
             └───────────────┼───────────────┘
                             │
                    Broadcast / Streaming
```

The development roadmap deliberately progresses from a **small deterministic core** toward a complete channel automation platform.

---

# Version Roadmap

## v0.0.1 — Deterministic Scheduling Core

**Objective:** Establish the foundational Python package, CLI, scheduling primitives, and deterministic execution model.

### Required capabilities

* [ ] Installable Python package named `chronoplay`
* [ ] Python 3.10–3.13 support
* [ ] Cross-platform package architecture
* [ ] Command-line interface
* [ ] `chronoplay --help`
* [ ] `python -m chronoplay --help`
* [ ] Deterministic event scheduling
* [ ] Absolute-time scheduling
* [ ] Relative-time scheduling
* [ ] UTC-based internal time representation
* [ ] Explicit timezone handling
* [ ] ISO-8601 timestamp support
* [ ] Schedule validation
* [ ] Schedule serialization
* [ ] YAML configuration support
* [ ] Structured operational logging
* [ ] Deterministic execution ordering
* [ ] Graceful shutdown
* [ ] Basic error handling
* [ ] Unit-testable scheduling engine
* [ ] Public Python API
* [ ] Apache-2.0 licensing
* [ ] PyPI packaging
* [ ] Reproducible package builds

### Engineering requirements

* Python type annotations throughout public APIs
* Ruff linting
* Black formatting
* MyPy type checking
* Pytest test suite
* Coverage reporting
* Bandit security analysis
* Dependency auditing
* GitHub Actions CI
* OpenSSF Scorecard
* CodeQL
* Dependabot

### v0.0.1 acceptance criteria

* Package installs successfully from a built wheel
* CLI starts successfully
* `python -m chronoplay --help` succeeds
* Test suite passes
* Static analysis passes
* Security checks pass
* Package can be built without modifying source files
* Scheduling results are deterministic for identical inputs

---

# v0.0.2 — Media Asset Model

**Objective:** Introduce the media abstraction required for real playout.

### Capabilities

* [ ] Media asset abstraction
* [ ] File-based media sources
* [ ] Media metadata model
* [ ] Duration detection
* [ ] Codec metadata
* [ ] Container metadata
* [ ] Resolution metadata
* [ ] Frame-rate metadata
* [ ] Audio-channel metadata
* [ ] Asset validation
* [ ] Asset availability checks
* [ ] Media library abstraction
* [ ] Asset identifiers
* [ ] Media hashing
* [ ] Duplicate detection
* [ ] Missing-media detection
* [ ] Asset lifecycle states

### Reliability

* [ ] Invalid asset isolation
* [ ] Missing-file detection before playout
* [ ] Corrupt-media detection
* [ ] Preflight validation

---

# v0.0.3 — Playlist Engine

**Objective:** Convert schedules into executable playlists.

### Capabilities

* [ ] Playlist abstraction
* [ ] Ordered media events
* [ ] Event duration handling
* [ ] Start-time constraints
* [ ] End-time constraints
* [ ] Program blocks
* [ ] Interstitial events
* [ ] Fill events
* [ ] Fixed-duration slots
* [ ] Schedule conflict detection
* [ ] Playlist validation
* [ ] Playlist serialization
* [ ] Playlist deserialization

### Determinism

* [ ] Stable ordering
* [ ] Explicit tie-breaking
* [ ] Reproducible playlist generation
* [ ] Deterministic fallback selection

---

# v0.0.4 — Playout Engine

**Objective:** Execute media events in real time.

### Capabilities

* [ ] Playout state machine
* [ ] PREPARE state
* [ ] READY state
* [ ] PLAYING state
* [ ] PAUSED state
* [ ] STOPPED state
* [ ] FAILED state
* [ ] Transition validation
* [ ] Event lifecycle tracking
* [ ] Playback clock
* [ ] Remaining-time calculation
* [ ] Event completion detection
* [ ] Graceful event termination
* [ ] Playback failure handling

---

# v0.0.5 — FFmpeg Media Pipeline

**Objective:** Introduce real media processing.

### Capabilities

* [ ] FFmpeg integration
* [ ] Media decoding
* [ ] Audio processing
* [ ] Video processing
* [ ] Frame pipeline
* [ ] Timestamp propagation
* [ ] Process supervision
* [ ] FFmpeg failure detection
* [ ] Process restart
* [ ] Pipeline teardown
* [ ] Pipeline health monitoring

### Timing requirements

* [ ] Monotonic execution clock
* [ ] Presentation timestamp tracking
* [ ] Clock-drift detection
* [ ] Timestamp discontinuity detection
* [ ] Controlled recovery from timing faults

---

# v0.0.6 — Channel Engine

**Objective:** Introduce persistent automated channels.

### Capabilities

* [ ] Channel abstraction
* [ ] Channel configuration
* [ ] Channel lifecycle
* [ ] Channel start/stop
* [ ] Channel pause/resume
* [ ] Channel state persistence
* [ ] Multiple independent channels
* [ ] Per-channel schedules
* [ ] Per-channel media libraries
* [ ] Per-channel output configuration

---

# v0.0.7 — Fallback and Recovery

**Objective:** Prevent dead air and maintain continuous operation.

### Capabilities

* [ ] Primary-source monitoring
* [ ] Backup-source selection
* [ ] Emergency-source selection
* [ ] Automatic failover
* [ ] Automatic recovery
* [ ] Configurable recovery policies
* [ ] Failure classification
* [ ] Retry policies
* [ ] Exponential backoff
* [ ] Circuit-breaker behavior
* [ ] Dead-air detection
* [ ] Recovery event logging

### Operational principle

> **A recoverable failure should not become a channel outage.**

---

# v0.0.8 — Live Sources

**Objective:** Integrate external live media sources.

### Capabilities

* [ ] Live input abstraction
* [ ] RTMP input
* [ ] SRT input
* [ ] Network-source health monitoring
* [ ] Source timeout detection
* [ ] Live-source failover
* [ ] Source priority
* [ ] Emergency live insertion
* [ ] Return-to-schedule behavior

---

# v0.0.9 — Streaming Outputs

**Objective:** Provide programmable distribution outputs.

### Capabilities

* [ ] RTMP output
* [ ] SRT output
* [ ] Output lifecycle management
* [ ] Output health monitoring
* [ ] Connection retry
* [ ] Output failover
* [ ] Encoder supervision
* [ ] Bitrate configuration
* [ ] Resolution configuration
* [ ] Frame-rate configuration
* [ ] Audio configuration

---

# v0.1.0 — First Complete Channel Automation System

**Objective:** Deliver the first coherent end-to-end ChronoPlay platform.

### Required capabilities

* [ ] Schedule
* [ ] Validate
* [ ] Prepare
* [ ] Play
* [ ] Encode
* [ ] Monitor
* [ ] Recover
* [ ] Distribute

### Operational requirements

* [ ] Persistent channel state
* [ ] Crash recovery
* [ ] Automatic process recovery
* [ ] Structured logs
* [ ] Health checks
* [ ] Metrics
* [ ] Configuration validation
* [ ] Operational diagnostics
* [ ] CLI administration

---

# v0.2.x — Multi-Channel Architecture

### Capabilities

* [ ] Multiple simultaneous channels
* [ ] Channel isolation
* [ ] Shared media libraries
* [ ] Resource quotas
* [ ] Channel-specific policies
* [ ] Independent scheduling
* [ ] Channel health dashboard
* [ ] Centralized configuration
* [ ] Multi-channel monitoring

---

# v0.3.x — Web Control Plane

### Capabilities

* [ ] HTTP API
* [ ] Authentication
* [ ] Authorization
* [ ] Channel dashboard
* [ ] Schedule editor
* [ ] Playlist editor
* [ ] Media library interface
* [ ] Live channel status
* [ ] System health dashboard
* [ ] Event history
* [ ] Operational alerts

---

# v0.4.x — Distributed ChronoPlay

### Capabilities

* [ ] Controller/worker architecture
* [ ] Remote playout workers
* [ ] Worker registration
* [ ] Worker health monitoring
* [ ] Job assignment
* [ ] Distributed scheduling
* [ ] Worker failover
* [ ] State replication
* [ ] Distributed event coordination
* [ ] Network partition handling

---

# v0.5.x — Broadcast Operations Platform

### Capabilities

* [ ] Electronic program guide integration
* [ ] Traffic-system integration
* [ ] Commercial scheduling
* [ ] Advertising insertion
* [ ] Program metadata
* [ ] SCTE-35 support
* [ ] Emergency broadcast workflows
* [ ] Recording
* [ ] Time-shifted playback
* [ ] Archive management
* [ ] Content expiration policies

---

# v0.6.x — Observability and Operations

### Capabilities

* [ ] Prometheus metrics
* [ ] OpenTelemetry integration
* [ ] Distributed tracing
* [ ] Structured event telemetry
* [ ] Alerting
* [ ] SLA monitoring
* [ ] Dead-air alerts
* [ ] Encoder health alerts
* [ ] Storage alerts
* [ ] Network alerts
* [ ] Resource utilization monitoring

---

# v0.7.x — High Availability

### Capabilities

* [ ] Active/passive deployment
* [ ] Active/active deployment
* [ ] Redundant controllers
* [ ] Redundant playout workers
* [ ] Shared state
* [ ] Automatic leader election
* [ ] Automatic failover
* [ ] Recovery verification
* [ ] Split-brain protection
* [ ] Disaster recovery procedures

---

# v0.8.x — Enterprise Control

### Capabilities

* [ ] Role-based access control
* [ ] Multi-user administration
* [ ] Audit logging
* [ ] Organization management
* [ ] Tenant isolation
* [ ] API keys
* [ ] Service accounts
* [ ] Fine-grained permissions
* [ ] Configuration versioning
* [ ] Change approval workflows

---

# v0.9.x — Production Hardening

### Requirements

* [ ] Performance benchmarking
* [ ] Long-duration soak testing
* [ ] Fault-injection testing
* [ ] Network failure testing
* [ ] Storage failure testing
* [ ] Process-crash testing
* [ ] Clock-drift testing
* [ ] Recovery-time measurements
* [ ] Resource-leak detection
* [ ] Security penetration testing
* [ ] Upgrade/rollback testing
* [ ] Disaster-recovery testing

---

# v1.0.0 — Production Release

ChronoPlay 1.0 will represent the first release intended for production broadcast and automated streaming deployments.

### Release requirements

* [ ] Stable public API
* [ ] Stable configuration format
* [ ] Backward-compatibility policy
* [ ] Production documentation
* [ ] Deployment documentation
* [ ] Security policy
* [ ] Threat model
* [ ] Performance specifications
* [ ] Reliability specifications
* [ ] Disaster-recovery documentation
* [ ] Migration tooling
* [ ] Versioned release artifacts
* [ ] Reproducible builds
* [ ] Signed release artifacts
* [ ] SBOM generation
* [ ] Supply-chain security controls

---

# Long-Term Architecture

The final ChronoPlay architecture is intended to converge toward the following layers:

```text
┌──────────────────────────────────────────────────────┐
│                    CONTROL PLANE                     │
│ Web UI • CLI • API • Authentication • RBAC           │
├──────────────────────────────────────────────────────┤
│                  ORCHESTRATION                       │
│ Channels • Schedules • Jobs • Failover • HA          │
├──────────────────────────────────────────────────────┤
│                    PLAYOUT                            │
│ Playlist • Media • Live Input • Emergency Content    │
├──────────────────────────────────────────────────────┤
│                  MEDIA PIPELINE                       │
│ Decode • Process • Encode • Timestamp • Mux          │
├──────────────────────────────────────────────────────┤
│                   TRANSPORT                           │
│ RTMP • SRT • Network Sources • Distribution          │
├──────────────────────────────────────────────────────┤
│                  OBSERVABILITY                        │
│ Logs • Metrics • Traces • Alerts • Audit             │
├──────────────────────────────────────────────────────┤
│                 INFRASTRUCTURE                        │
│ Linux • Windows • macOS • Containers • ARM/x86       │
└──────────────────────────────────────────────────────┘
```

## Design Principles

* **Determinism:** identical inputs should produce reproducible scheduling decisions.
* **Resilience:** recoverable failures should trigger automated recovery.
* **Observability:** important operational decisions should be measurable and auditable.
* **Portability:** the core engine should remain cross-platform.
* **Modularity:** scheduling, playout, media processing, transport, and control should remain independently testable.
* **Fail-safe operation:** the system should prefer continued service over unnecessary interruption.
* **Explicit state:** channel and media state should be represented explicitly rather than inferred.
* **Security by default:** credentials, privileges, network interfaces, and dependencies should follow least-privilege principles.
* **Operational transparency:** failures and recovery actions should be visible to operators.
* **Incremental evolution:** every release should produce a usable engineering milestone rather than relying exclusively on a final product release.

## Current Release

**ChronoPlay v0.0.1 — Deterministic Scheduling Core**

ChronoPlay is currently in early alpha development. The roadmap above defines the intended progression from the scheduling foundation toward a complete broadcast automation and channel operations platform.

## License

ChronoPlay is released under the Apache License 2.0.
