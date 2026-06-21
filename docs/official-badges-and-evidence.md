# Official Badges And Evidence Policy

Primary research attribution: [ORCID 0009-0007-2904-0443](https://orcid.org/0009-0007-2904-0443).

This repository can mention external tools only at the evidence level that is actually verified. The goal is to attract sponsors without overstating affiliation.

## Current Evidence Status

| Organization | Evidence found | Public wording allowed | Wording locked until explicit approval |
|---|---|---|---|
| Datadog | Gmail contains an incoming message from `Datadog for Startups <startups@datadoghq.com>`, subject `Datadog Onboarding - Introduction to Professor Bits!`, dated 2025-10-20. It welcomes the team to the Datadog for Startups journey for the next 12 months and links a Startup Program Welcome Kit. The local stack also has a Datadog Agent integration path. | `Datadog for Startups onboarding active - Docker analytics integration in progress` | `Official Datadog partner`, `Sponsored by Datadog` unless sponsor language is separately approved |
| E2B | Gmail contains an incoming application update from `startups@e2b.dev`, subject `Application Update: E2B for Startups`, dated 2025-08-08. It says the E2B for Startups application was approved and includes E2B credits plus Pro Tier access. The email also says at least one E2B badge display is required where applicable. | `Accepted into E2B for Startups - sandbox smoke path in progress` | `Official E2B partner`, `Sponsored by E2B` unless sponsor language is separately approved |

## Safe Banner Set

Use these while the sponsor record is still being hardened:

```text
Accepted into E2B for Startups - sandbox smoke path in progress
Datadog for Startups onboarding active - Docker analytics integration in progress
ORCID-attributed research prototype: 0009-0007-2904-0443
```

## Promotion Rule

A stronger banner requires one of these:

- an explicit acceptance email from the program;
- a written approval from the organization;
- a public program page naming the project or author;
- a signed sponsor agreement.

Internal emails, drafts, sent messages, or self-written README text are not sufficient evidence for sponsor claims.

Program onboarding emails are sufficient for program/onboarding wording when they come directly from the vendor program address.

## E2B Badge

The official E2B for Startups email includes `01-Startups.png` and requests badge display where applicable. This repository stores that image at:

```text
assets/e2b-startups-badge.png
```

Use the image to satisfy the badge-display requirement while keeping the README language accurate.

## Source References

- E2B documentation describes isolated sandboxes for agents that execute code, process data, and run tools: <https://e2b.dev/docs>
- E2B coding-agent documentation describes isolated Linux environments with terminal, filesystem, and git: <https://e2b.dev/docs/use-cases/coding-agents>
- Datadog Docker Agent documentation covers container metrics/log collection and Docker Agent configuration: <https://docs.datadoghq.com/containers/docker/>
- Datadog Docker log documentation covers container log collection patterns: <https://docs.datadoghq.com/containers/docker/log/>
