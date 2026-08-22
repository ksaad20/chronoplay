### Demo User Manual

#### 1. Prepare a media file

Place a test media file such as `demo.mp4` in your working directory.

The file should be a media format supported by the configured FFmpeg installation.

#### 2. Run the ChronoPlay demo

```bash
chronoplay demo demo.mp4
```

You can also provide an absolute or relative path:

```bash
chronoplay demo /path/to/program.mp4
```

#### 3. What the demo demonstrates

The v0.0.1 demonstration exercises the core ChronoPlay workflow:

1. A media asset is created from the supplied file.
2. The media asset is assigned a duration.
3. A timezone-aware schedule event is created.
4. The event is inserted into the scheduler.
5. The scheduler provides the next scheduled event.
6. The playout engine starts.
7. The scheduled media event is passed to the playout engine.
8. The demonstration reports the event through the application logger.
9. The playout engine is stopped cleanly.

This demonstrates the fundamental **media → schedule → playout** pipeline without requiring a production broadcast channel.

#### 4. Check the CLI

To see available options:

```bash
chronoplay --help
```

For the demo command specifically:

```bash
chronoplay demo --help
```

To check the installed version:

```bash
chronoplay --version
```

#### 5. Demo scope in v0.0.1

The demo is intended as a **technical proof-of-concept for broadcast companies**, not yet as a production playout replacement.

The current demonstration validates the core scheduling and playout architecture. Production deployment still requires additional capabilities such as persistent schedules, channel configuration, operational monitoring, reliable FFmpeg process management, logging and alerting, and broadcast-specific redundancy.

A customer demonstration should therefore be presented as:

> **ChronoPlay v0.0.1 — Core Scheduling and Media Playout Demonstration**

rather than as a fully production-ready broadcast automation system.

