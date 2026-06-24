# FNP-QNN Gateway Mesh Proof

Status: integration plan and payload contract.

## Objective

QLC MVP must prove the utility of the FNP-QNN quantum/neutrosophic simulator by
feeding it real QLC container metadata, CodeProject.AI YOLO perception metadata,
and CPAI mesh routing metadata through CeLeBrUm.

Terminology is strict:

- `CeLeBrUm` is the MVP orchestrator/router. It receives YOLO-derived metadata,
  applies bounded interpretation/admissibility pressure, and submits sanitized
  observations onward.
- `Cerebrum` is the FNP-QNN runtime/memory surface exposed as
  `POST /cerebrum/runtime/run`.
- The older design-language role `ReaAaS-n` is not the public MVP execution
  route for this proof. In this repo, its place in the YOLO loop is remapped to
  CeLeBrUm.

The proof route is:

```text
FfeD-QLC-MVP
  -> fnpqnn_gateway_MVP
  -> CodeProject.AI Server / YOLO mesh
  -> CeLeBrUm orchestration
  -> FNP-QNN-MVP POST /cerebrum/runtime/run
  -> LVFM + QNN + Hydra-EM-GPCN profiles
```

## Implemented QLC Side

`ffed_qlc.mesh_proof` builds a simulator-ready JSON payload:

- QLC container SHA-256 and structural score;
- optional YOLO detections as `vision` memories;
- a CeLeBrUm ROI/semantic map derived from YOLO metadata only;
- a Semantic Complexity Map that translates high-confidence ROI labels into
  bounded lattice-density, phason-strain, and Z-value policy parameters;
- CPAI mesh context with route, node count, load, and forwarding metadata;
- explicit `CeLeBrUm` versus `Cerebrum` provenance markers;
- simulator flags for LVFM/QNN plus plithogenic, topology, neutro-algebra, and
  Hydra-EM-GPCN layers.

Generate a proof payload:

```powershell
ffed-qlc mesh-proof `
  --input .\plain.fqlc `
  --source-id asset-001 `
  --output .\qlc-runtime.json `
  --proof-mode simulator_supports_qlc_complexity `
  --plan-output .\qlc-gateway-plan.json `
  --codeproject-url http://localhost:32168 `
  --known-server ai-node-01
```

Pack an image or file and emit the proof in one step:

```powershell
ffed-qlc yolo-pack `
  --input .\image.png `
  --output .\image.fqlc `
  --source-id image-001 `
  --proof-output .\image-runtime.json `
  --detections-json .\yolo-detections.json `
  --proof-mode qlc_protects_simulator_mvp `
  --plan-output .\image-gateway-plan.json
```

The detections file may be a list or a CodeProject-style object containing
`predictions`, `detections`, or `regions`. The CLI stores only metadata in the
runtime proof; it does not embed image bytes.

Post it to the simulator once the FNP-QNN API is running:

```powershell
Invoke-RestMethod `
  -Method Post `
  -ContentType application/json `
  -InFile .\qlc-runtime.json `
  -Uri http://localhost:8000/cerebrum/runtime/run
```

## Reciprocal MVP Proof Loop

This integration is a reciprocal proof loop between two MVPs.

`--proof-mode simulator_supports_qlc_complexity` proves the FNP-QNN MVP side:
the simulator can support, measure, route, and interpret a complex protocol like
QLC.

- LVFM turns QLC and YOLO metadata into graph memory;
- QNN smoke creates a feature vector and backend prediction trace;
- CeLeBrUm makes YOLO useful as bounded perception without letting YOLO become
  the decision engine;
- CPAI mesh metadata shows whether the event should process local or become a
  forward candidate;
- Hydra-EM-GPCN adds the quasicrystal/GPCN chamber profile;
- p114/plugin hooks can add admissibility and tension metadata without leaking
  the original payload.

`--proof-mode qlc_protects_simulator_mvp` proves the QLC MVP side: QLC protects
simulator inputs, outputs, runtime snapshots, YOLO-derived events, and mesh
handoffs with authenticated manifests and metadata-only audit records.

Use `--proof-mode qlc_protects_simulator_mvp` when the QLC container represents a
simulator input, output, runtime snapshot, YOLO-derived event, or mesh handoff.
The generated payload records:

- `FNP-QNN-MVP` / `Cerebrum` as the protected surface;
- QLC as the protection layer for simulator artifacts;
- tamper/authentication guarantees;
- metadata-only handoff rules for YOLO and mesh signals;
- a public-safe claim boundary: protocol-validity surface, not production
  certification.

This proves why QLC should exist: complex simulator workflows create valuable
intermediate artifacts, routing decisions, and perception-derived metadata. QLC
adds authenticated containment, replayable manifests, and leak-resistant audit
records around those artifacts before they move through CeLeBrUm, gateway, or
FNP-QNN routes.

## Boundaries

- YOLO is perception metadata only.
- Semantic complexity is policy pressure only; it is not a cryptographic root.
- CeLeBrUm is the orchestration concept for the MVP proof.
- Cerebrum is the simulator runtime/memory endpoint, not the orchestrator.
- QLC container bytes are not embedded in the simulator payload.
- The simulator is alpha-local research, not a production security oracle.
- The gateway is a handoff surface; it does not absorb CodeProject.AI or FNP-QNN.
