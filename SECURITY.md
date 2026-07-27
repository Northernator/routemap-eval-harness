# Security Policy

## Supported versions

Security fixes target the latest release and current `main`. Older tags and unreleased forks are not
guaranteed to receive fixes.

## Report a vulnerability

Use GitHub's private vulnerability reporting for this repository:

`Security` → `Advisories` → `Report a vulnerability`

Do not open a public issue with exploit details, credentials, private prompts, or affected user data. If private
vulnerability reporting is unavailable, open a minimal public issue asking maintainers to establish a private
contact channel; include no sensitive or reproducible vulnerability detail in that issue.

Include, where safe:

- affected commit/tag and component;
- impact and preconditions;
- minimal reproduction using synthetic data;
- whether credentials, external providers, or generated audit/run logs are involved; and
- suggested mitigation, if known.

Maintainers aim to acknowledge a complete report within seven days, assess severity and affected versions,
and coordinate a fix and disclosure timeline. Response times are best-effort for this volunteer project.

## Safe research expectations

- Test only systems and accounts you own or are authorized to assess.
- Use synthetic prompts and credentials with no production privileges.
- Do not attack model providers, package registries, or other third-party services.
- Do not publish secrets or sensitive run/audit output.
- Stop testing if it risks data loss, service disruption, or unauthorized access.

## Security boundaries

RouteMap is a research and evaluation harness, not a security boundary or correctness certificate. Its
one-sided checks can rule out some outputs but cannot prove all accepted outputs safe or correct. Optional
model adapters send configured prompts to their selected provider and may create cost or privacy exposure.
The Python-code lane parses model output and must never execute it.
