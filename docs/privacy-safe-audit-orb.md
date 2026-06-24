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

## ECN Privacy-Safe Handoff Packet

`ffed_qlc.ecn_handoff` turns a privacy-safe audit orb into
`ffed.qlc.ecn_handoff_packet.v1`.

Allowed in the ECN packet:

- `audit_nonce` and `orb_id`;
- event and label fingerprints;
- event counters;
- Fibonacci audit tags;
- urgency;
- logical destination.

Rejected before handoff:

- raw browsing history;
- screenshots;
- passwords, tokens, private keys, API keys;
- raw payloads;
- full activity dumps.

CLI:

```powershell
ffed-qlc ecn-handoff `
  --audit-orb-json .\audit-orb.json `
  --output .\ecn-packet.json `
  --urgency high `
  --destination ecn://celebrum
```

The packet is an ECN metadata handoff. It is not a secret-transfer channel and
does not make a production compliance claim.

## Route Decision Input

Passe 4 lets a privacy-safe audit orb and ECN packet feed
`ffed.qlc.celebrum_route_decision.v1`. The route decision carries only:

- audit nonce;
- ECN destination;
- guard verdict;
- admissibility flag;
- selected route action.

It still rejects raw activity, raw OCR, screenshots, browsing history, passwords,
tokens, API keys, and full dumps.
