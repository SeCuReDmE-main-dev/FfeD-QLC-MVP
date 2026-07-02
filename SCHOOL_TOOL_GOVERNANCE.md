# School Tool Governance Standard

FfeD-QLC-MVP is part of the SecuredMe open-source school-tool suite. It is
currently pre-alpha / in development.

Official classroom use is maintained for students, teachers, schools, and
supervised young-adult learning. The supported AI-assisted routes are
Codex/OpenAI and Antigravity/Gemini only. Ollama Cloud, generic uncensored local
AI, and unknown agent routes are not supported as official classroom providers.

This repository uses the Secured Educational Cybersecurity License 2.0 (SECL-2.0). The local metadata
reference is LicenseRef-SECL-2.0. The license is custom to SecuredMe and is not
currently OSI-approved or listed in the SPDX License List.

The repository is provided for defensive education, fraud-awareness, simulation, and supervised cyber training. Outputs are review support
only unless a qualified human authority independently validates and accepts
them. The project does not create autonomous scientific, safety, legal,
clinical, regulatory, enforcement, or disciplinary authority.

Users may fork the code under the repository license, but the maintainer only
supports the reviewed official version. Private modified copies, broken forks,
unsupported provider routes, and local adaptations are the responsibility of the
person or organization maintaining those copies.

## Development Stability Gate

External PRs are not evaluated for merge before this official school tool is
stable and fully functional for classroom use. Until that gate is lifted,
outside contributors should open issues or build local forks, adapters, or
plugins; maintainers may still push internal stabilization commits.

## School Authentication And Secret Boundary

Official classroom use must not require raw `.env` files, API keys, tokens, or
local model secrets from students or teachers. Student and teacher workflows
must use Codex/OpenAI or Antigravity/Gemini through browser WebAuth,
fingerprinted session approval, and encrypted local session records when
authentication is needed.

The reason for excluding generic local AI routes from official school mode is
student and teacher safety: education accounts, provider-side account controls,
browser login, and governed AI refusal behavior are safer than unguided local
model endpoints for classroom tools.
