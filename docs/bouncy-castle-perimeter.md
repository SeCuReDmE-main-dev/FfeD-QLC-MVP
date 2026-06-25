# Bouncy Castle Perimeter

Status: optional local integrity provider.

FfeD-QLC can attach a Bouncy Castle perimeter signature to a workflow bundle
through a local `bcctl` executable. This is an outer receipt over public
metadata digests. It does not replace the `FQLC1` container, the QLC structural
transform, `ChaCha20-Poly1305`, or `scrypt`.

## Provider Setup

Configure the local tool with `FFED_BCCTL_PATH`, or put `bcctl` on `PATH`:

```powershell
$env:FFED_BCCTL_PATH = "path-to-local-bcctl-executable"
ffed-qlc bc-status
```

`bc-status` reports provider availability, version text, and algorithm names.
It intentionally reports only the path source (`FFED_BCCTL_PATH` or `PATH`) and
does not echo local filesystem paths.

## CLI Usage

Sign public digests directly:

```powershell
ffed-qlc bc-sign `
  --key-id perimeter-key `
  --context-digest <workflow-context-hex> `
  --artifact-digest <artifact-hex> `
  --output .\bc-signature.json
```

Verify a digest signature:

```powershell
ffed-qlc bc-verify `
  --key-id perimeter-key `
  --context-digest <workflow-context-hex> `
  --message-digest <artifact-hex> `
  --signature-digest <signature-hex> `
  --output .\bc-verification.json
```

Attach a perimeter receipt while building the workflow bundle:

```powershell
ffed-qlc protect-workflow `
  --input .\plain.fqlc `
  --source-id asset-001 `
  --output .\qlc-workflow.json `
  --bcctl-sign `
  --bcctl-key-id perimeter-key
```

Without `--bcctl-sign`, workflow output keeps the existing behavior and no
perimeter receipt is added.

## Receipt Shape

The workflow sidecar field is `perimeter_receipt`:

```json
{
  "schema": "ffed.qlc.bouncy_castle_perimeter_receipt.v1",
  "provider": "BouncyCastle",
  "tool": "bcctl",
  "algorithm": "Ed25519",
  "operation": "sign",
  "key_id": "perimeter-key",
  "context_digest": "<workflow-fingerprint>",
  "artifact_digest": "<container-sha256>",
  "signature_digest": "<sha256-of-signature>",
  "signature_b64": "<signature>",
  "raw_payload_embedded": false
}
```

The receipt is outside the core container format. Verification failure means the
perimeter receipt did not validate; it does not reinterpret or bypass QLC
container authentication.

## Public-Safe Boundary

The adapter passes only:

- key IDs;
- context digests;
- artifact/message digests;
- signature digests.

It never passes raw files, plaintext, passphrases, API keys, `.env` values,
private corpus text, screenshots, or raw simulator payloads. Error output is
sanitized before it reaches Python exceptions or CLI JSON.

## Failure Behavior

- `bc-status` is non-throwing when the provider is absent.
- `bc-sign`, `bc-verify`, and `protect-workflow --bcctl-sign` fail closed when
  the provider command fails, times out, or returns invalid JSON.
- Normal QLC commands continue to work when `bcctl` is unavailable.

## Source Basis

- Bouncy Castle C#/.NET downloads: https://www.bouncycastle.org/download/bouncy-castle-c/
- NuGet package: https://www.nuget.org/packages/BouncyCastle.Cryptography/2.6.2
- C# source mirror: https://github.com/bcgit/bc-csharp
