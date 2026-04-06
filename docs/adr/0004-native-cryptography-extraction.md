# 4. Use Native Python Cryptography for mTLS Storage

Date: 2026-04-06

## Status

Accepted

## Context

Migasfree Connect requires an underlying mTLS trust relationship to communicate with Migasfree Manager and Relay Servers. The original mechanism to bootstrap this trust relied on extracting `cert.pem`, `key.pem`, and `ca.pem` from a `.p12` bundle by spawning subprocesses running the `openssl` CLI binary.

While `openssl` is broadly available, relying on an external system binary introduced severe risks:

1. **Platform Discrepancies:** Variations in `openssl` versions between Linux environments and Windows can cause unexpected extraction failures.
2. **Security & Injection Risk:** Even though inputs were safely piped via `subprocess.run(..., input=password)`, communicating highly sensitive Private Keys via shell STDIO pipelines violates best practices for AppSec defense in depth.

## Decision

We have removed the dependency on the `openssl` binary and implemented native extraction using the Python `cryptography` library (`cryptography.hazmat.primitives.serialization.pkcs12`).

The application now reads the raw P12 binary data and parses it entirely within the application's memory space, persisting the final PEM output directly to the local filesystem.

## Consequences

* **Positive:** Enhanced Security Posture (Zero command execution risks linked to credential extraction).
* **Positive:** Complete cross-platform consistency. The application is isolated from the host OS's OpenSSL version.
* **Positive:** Allows reliable Mocking during test execution, improving QA robustness.
* **Negative:** Adds a new heavyweight compiled binary dependency (`cryptography>=3.0`), slightly increasing package size.
