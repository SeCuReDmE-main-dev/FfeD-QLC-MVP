# YOLO-Style Image Secret Redaction

Primary research attribution: [ORCID 0009-0007-2904-0443](https://orcid.org/0009-0007-2904-0443).

This document defines a defensive image pipeline for screenshots, photos, whiteboards, dashboards, notebooks, and generated artifacts before they enter public GitHub, E2B sandboxes, or Datadog logs.

## Important Boundary

YOLO-style detection and blur are not encryption.

For real secrets, use solid redaction or removal. Blur and pixelation can still leak information if the region is small, repeated, or recoverable from context.

## Pipeline

```text
input image
  -> object detector
  -> OCR pass
  -> secret-pattern scanner
  -> entropy scanner
  -> redaction mask plan
  -> solid redact or heavy pixelate
  -> fingerprint original privately
  -> publish only redacted image
```

## Detection Layers

Use multiple detectors because YOLO alone does not reliably find text secrets.

| Layer | Purpose | Examples |
|---|---|---|
| Object detection | Finds likely sensitive objects or regions | screens, documents, ID cards, QR codes, wallets, terminals, dashboards |
| OCR | Extracts visible text | terminal output, notebook cells, API dashboards, code screenshots |
| Regex scanner | Flags known secret formats | API keys, tokens, private-key headers, JWTs, cloud credentials |
| Entropy scanner | Flags suspicious high-entropy strings | unknown keys, long random tokens, base64-like strings |
| Policy gate | Decides action | accept, suspend for review, reject publication |

## Redaction Policy

Use solid redaction for:

- private keys;
- API tokens;
- `.env` screenshots;
- QR codes;
- wallet seeds;
- credentials;
- session cookies;
- Datadog/E2B keys;
- raw OCR text containing secrets.

Use blur or pixelation only for lower-risk visual context:

- faces when consent is unknown;
- internal hostnames;
- file paths;
- UI panels that do not contain secrets.

## QLC Fit

The QLC layer should not store the raw image in public artifacts. It should store a bounded evidence record:

```text
image_id
original_private_hash
redacted_public_hash
mask_count
detector_versions
admissibility_decision
reason_codes
```

This lets the project prove that a redaction decision happened without exposing the secret material.

## Datadog And E2B Boundary

E2B can run the redaction pass inside an isolated sandbox. Datadog can receive metrics such as:

```text
ffed_qlc.redaction.images_scanned
ffed_qlc.redaction.secrets_detected
ffed_qlc.redaction.images_rejected
ffed_qlc.redaction.images_published
```

Never send the raw image, unredacted OCR text, or detected secret values as Datadog tags or logs.
