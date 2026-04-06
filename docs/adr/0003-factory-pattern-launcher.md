# 3. Use Factory Pattern for Protocol Launchers

Date: 2026-04-06

## Status

Accepted

## Context

The Migasfree Connect application originally managed protocol execution (e.g., SSH, VNC, RDP) using a monolithic `execute_client` function containing a large `if/elif` chain. This approach tightly coupled the specific protocol parameters and connection logic to the main tunneling execution path. As new protocols are introduced, this monolithic function would grow in complexity, increasing the risk of regressions and making it harder to test individual protocols in isolation.

## Decision

We have refactored the `launcher.py` module to use the Factory Pattern. We created an abstract base class (`BaseLauncher`) and individual concrete classes for each protocol (`SshLauncher`, `VncLauncher`, `RdpLauncher`). A central registry (`LauncherFactory`) resolves the appropriate launcher based on the requested protocol service.

This approach adheres to the Open/Closed Principle: new protocols can be added by creating a new launcher class and registering it with the factory, without modifying existing system logic.

## Consequences

* **Positive:** Greatly improved testability. Each protocol class can be tested independently. Test coverage for the module increased from 70% to 95%.
* **Positive:** The main flow remains clean and uncoupled from specific client binaries or protocol nuances.
* **Positive:** Easy extensibility for new or proprietary remote protocols.
* **Negative:** Adds slight boilerplate (defining class hierarchies instead of procedural `if` blocks) which is a minor trade-off for maintainability.
