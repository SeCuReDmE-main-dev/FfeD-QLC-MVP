# QLC Drive Research Digest

Status: Drive-sourced mechanism digest before implementation.

This digest turns the Drive research around `FfeD-CrYptE` and `FfeD-QLC`
into implementation guardrails, creative seeds, and function contracts. These
documents are not mathematical proof, product claims, or UI labels. They are a
mechanism map for the next code pass.

## Drive Sources Used

| ID | Drive document | Role in this digest |
|---|---|---|
| D01 | `FfeD CrypTe Protocol: Quasicrystal Lattice Cryptography (QLC)` | Core five-stage QLC concept, generative key, 4D lattice mapping. |
| D02 | `FfeD Quasicrystal Lattice Cryptography (QLC): A Foundational White Paper on Protocol Mechanics, Tandem Operation, and Security Assurance` | Detailed mechanism: CubicParticle schema, YOLO/ReaAaS-n tandem, Z-value, phason strain, threat model. |
| D03 | `Rapport Exhaustif - Trois Passes Wiring QLC Gateway FNP-QNN - 2026-06-24` | Existing implementation contract: workflow bundle, gateway submission, redacted metadata, tests, FQLC1 boundary. |
| D04 | Older duplicate `FfeD CrypTe Protocol: Quasicrystal Lattice Cryptography (QLC)` | Secondary confirmation of the same five-stage conceptual mechanism. |

## Non-Negotiable Interpretation

- The Drive docs define mechanism seeds, not validated cryptographic security.
- Public wording remains `research`, `prototype`, or `pre-alpha` unless an
  external cryptographic review proves more.
- No implementation may claim certified quantum resistance, proven security, or
  operational suitability for critical infrastructure.
- `FQLC1` remains unchanged until a separate explicit cryptography pass.
- Raw media, OCR text, secrets, keys, tokens, and raw particle payloads are not
  exported.
- The source graph remains a provenance/audit surface, not the math itself.

## Mechanism Extracted From Drive

The repeated QLC mechanism is a five-stage transformation:

1. `Particulate Instantiation`: source data becomes normalized particles.
2. `Granular ECC Imbuement`: every particle gets independent cryptographic
   protection or a safe metadata/fingerprint stand-in during prototype mode.
3. `Quasicrystal Lattice Mapping`: particles are assigned to a deterministic
   aperiodic lattice.
4. `FfeD CrypTe Key Generation`: the key is a generative recipe, not a plain
   password string.
5. `Compression And Finalization`: the stored object is inert without the
   generative recipe and allowed reconstruction context.

This maps to functions, not UI tabs:

```text
asset -> instantiate_particles -> protect_particles
      -> generate_lattice_coordinates -> build_key_manifest
      -> finalize_redacted_bundle
```

## Function Contracts To Implement

### `instantiate_particles(asset_descriptor)`

Purpose: convert any supported input into deterministic particle descriptors.

Required output fields:

- `particle_id`
- `source_index`
- `payload_shape`
- `state_wxyz`
- `metadata_fingerprint`
- `source_hash`

Allowed prototype behavior:

- store payload fingerprints and shape metadata;
- avoid exporting raw payload values;
- preserve deterministic order.

### `map_image_particle(pixel)`

Source idea: image pixels become CubicParticles.

Implementation seed:

```text
w = normalized_red
x = normalized_green
y = normalized_blue
z = normalized_alpha_or_1
```

Guardrail: this mapping defines variables. Mentioning `CubicParticle` is not
enough.

### `map_audio_particle(frame)`

Source idea: audio is windowed, transformed, then mapped.

Implementation seed:

```text
frame -> FFT bins -> dominant_frequency, phase, magnitude, energy
state_wxyz = normalized(feature_vector[0:4])
```

Guardrail: audio support can be scaffolded as a contract first, but must not
pretend to be complete without tests and sample fixtures.

### `map_text_particle(node)`

Source idea: structured text becomes semantic units.

Implementation seed:

```text
document -> AST/paragraph units -> stable node path -> embedding/hash features
state_wxyz = deterministic compact numeric projection
```

Guardrail: raw text is not exported; only fingerprints, node paths, and compact
numeric features are allowed.

### `protect_particles(particles, key_policy)`

Purpose: preserve the Drive concept of per-particle protection without touching
`FQLC1` blindly.

Prototype output:

- `particle_protection_fingerprint`
- `key_schedule_fingerprint`
- `curve_profile`
- `key_material_exported=false`

Production gate:

- constant-time primitives and side-channel assumptions must be documented;
- no homegrown crypto replaces reviewed primitives.

### `build_semantic_pressure(roi_map)`

Source idea: YOLO feeds sensitivity into lattice generation.

Implementation seed:

```text
ROI confidence + class sensitivity -> semantic_pressure in [0, 1]
```

Guardrail: YOLO/CPAI is metadata-only unless the user explicitly runs training
or detection. The lattice math must still work without YOLO.

### `translate_pressure_to_lattice_params(semantic_pressure)`

Source idea: ReaAaS-n translates semantic meaning into lattice parameters.

Implementation seed:

```text
lattice_density_multiplier = 1 + pressure
phason_strain_factor = bounded_pressure_curve(pressure)
z_value_modifier = pressure * configured_z_span
```

Guardrail: this is a numeric function. It is not a class-name switch alone.

### `calculate_z_value(w, x, y, z, phi, z_modifier)`

Source idea from Drive:

```text
Z = (y * (w + x) - y * z) + z^3 + phi^5 + z_modifier
```

Implementation guardrails:

- input variables must be normalized and bounded;
- output must be clamped or scaled before it affects geometry;
- `Z` is local interaction pressure, not a security proof.

### `apply_phason_strain_gradient(tile_or_particle, pressure_field)`

Source idea: avoid sharp boundaries between high and low complexity zones.

Implementation seed:

```text
local_pressure = smooth_neighbors(pressure_field, radius)
strain = gradient(local_pressure)
geometry_offset = bounded(strain * phason_scale)
```

Guardrail: this must be smooth and bounded so the generated lattice stays
valid.

### `build_cryPTe_key_manifest(lattice_config)`

Source idea: the key is a generative recipe.

Allowed fields:

- `lattice_seed_fingerprint`
- `rotation_vector_profile`
- `projection_slice_profile`
- `key_schedule_fingerprint`
- `source_hash`
- `roi_map_fingerprint`

Forbidden fields:

- raw private keys;
- raw tokens;
- raw media;
- raw OCR or text payload.

### `build_qlc_workflow_bundle(...)`

Existing wiring source: the bundle must stay metadata-only and compatible with
the prior `qlc-wiring-contract.v2` direction.

Required bundle profile:

- schema: `ffed.qlc.protection_workflow_bundle.v1`
- contract version: `qlc-wiring-contract.v2`
- gateway submission: `ffed.qlc.gateway_submission.v1`
- runtime context: `ffed.qlc.runtime_normalized_context.v1`
- redaction verdict: `metadata_only_pass` or `review`

## Penrose Workbench Adaptation

The Drive docs speak in terms of a 4D quasicrystal substrate. The current
workbench should start with a testable 2D Penrose lattice model and keep a clean
bridge toward higher-dimensional projection.

Implementation path:

1. Generate valid thin/thick rhombi by inflation and optional cut-and-project.
2. Map particles or particle summaries onto accepted tile coordinates.
3. Apply semantic pressure and plithogenic friction as bounded perturbation,
   admission, or classification signals.
4. Measure `D_f` and `D_f_hat` on the accepted patch.
5. Export only the redacted template and provenance fingerprints.

Preserve hierarchy:

```text
I -> I_system^S -> D_f -> dF -> i_fractal
```

Do not collapse `dF` into generic indeterminacy.

## Creative Seeds Worth Preserving

- Treat the key as a recipe for reconstructing a mathematical universe.
- Let source data shape local geometry through bounded numeric functions.
- Use semantic pressure to increase local lattice complexity, not to replace
  the lattice math.
- Use phason-like gradients to avoid brittle complexity cliffs.
- Use provenance fingerprints as audit anchors.
- Keep CeLeBrUm/Cerebrum/Gateway as orchestration and runtime boundaries, not
  as hidden sources of truth.
- Make the UI show diagnostics and controls for functions, not raw source URLs.

## Research Questions Before Heavy Crypto Work

1. What exact normalization maps arbitrary payloads to `w, x, y, z`?
2. What exact bounds keep `Z` useful without corrupting Penrose geometry?
3. Which parts are prototype fingerprints versus actual cryptographic material?
4. How does a 2D Penrose patch map cleanly toward a 4D projection profile?
5. What compression model is measurable in the MVP without overclaiming?
6. How do we test side-channel assumptions without pretending certification?
7. How should semantic pressure influence `D_f_hat` without turning measurement
   into a truth claim?

## Implementation Consequence

The next code pass should implement math-first modules:

- `particles.py`
- `semantic_pressure.py`
- `z_value.py`
- `lattice_parameters.py`
- `qlc_manifest.py`
- `workflow_bundle.py`

The UI comes after these functions exist. Buttons should call real functions:

- `Instantiate Particles`
- `Build Penrose Lattice`
- `Apply Plithogenic Gate`
- `Measure D_f`
- `Export Redacted Template`

Source documents and URLs stay in docs/provenance. The running app consumes the
compiled function contracts.
