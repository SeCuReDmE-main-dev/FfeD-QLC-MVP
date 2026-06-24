# Privacy-Safe Audit Orb

Status: public-safe ProGuarD concept extraction.

The original ProGuarD orb concept is implemented here only as a privacy-safe
audit record. It does not collect passwords, raw secrets, full desktop captures,
or private user content.

Allowed in the MVP:

- event labels and sources;
- timestamps;
- secret manager references;
- deterministic fingerprints;
- Fibonacci audit tags;
- differential-privacy metadata for bounded aggregates.

Rejected in the MVP:

- raw passwords;
- raw API keys or tokens;
- employee surveillance payloads;
- arbitrary browsing history capture;
- secret relocation into random files.

CLI:

```powershell
ffed-qlc audit-orb `
  --orb-id worker-orb-001 `
  --events-json .\events.json `
  --output .\audit-orb.json
```

The output is suitable for simulator or governance handoff because it contains
metadata and fingerprints only.
