# Chromium seccomp provenance

Source: Microsoft Playwright v1.64.1, `utils/docker/seccomp_profile.json`.

- [Upstream file](https://github.com/microsoft/playwright/blob/v1.64.1/utils/docker/seccomp_profile.json)
- Git blob SHA: `fddc05fb520affb145404e6f6f647ca96af8087d`.
- License: Apache-2.0; upstream license retained in [PLAYWRIGHT-LICENSE](PLAYWRIGHT-LICENSE).
- The upstream profile derives from Docker's default seccomp profile and adds namespace permissions for Chromium.
- Local modification: add `chroot` to the namespace sandbox allow rule, because all container capabilities are dropped before Chromium runs. Chromium requires this syscall inside its own user namespace. Do not replace this with privileged mode, SYS_ADMIN, an unconfined profile or a disabled Chromium sandbox.

Actual local hash, runtime results and limits: [dependency inventory](../docs/dependencies-m4.json), [M4a verification](../docs/m4-verification.md). This attribution does not constitute a security audit of the upstream or modified syscall profile.
