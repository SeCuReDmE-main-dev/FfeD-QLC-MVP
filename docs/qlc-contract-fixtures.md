# QLC Contract Fixtures

The `tests/fixtures/qlc_contract` files are the local interoperability contract for the second wiring pass.

- `qlc_workflow_image.json`: valid image workflow bundle.
- `qlc_workflow_document.json`: valid document workflow bundle.
- `qlc_workflow_video.json`: valid video workflow bundle.
- `qlc_workflow_forbidden_raw.json`: negative fixture that must be rejected.

These fixtures are metadata-only. They must not contain raw media, raw OCR, screenshots, passwords, tokens, API keys, private keys, browsing history, or full activity dumps.
