# QLC Plithogenic Fractal Admission Digest

Status: local PDF-sourced mechanism digest before implementation.

Source:

`C:\Users\jeans\Desktop\livre pdf\final version francaise\version francaise final\FractalNeutroGeometry_VERSION_FRANCAISE_FINALE.pdf`

This digest defines how the QLC workbench should pass from plithogenic
classification into fractal paths, then use an operational `T, dF, F` reading
to decide whether a Penrose tile is admissible for build, orb creation, and
redacted data envelope wrapping.

## Hard Boundary

- A rhombus name is not a rhombus definition.
- A single simple rhombus is not automatically fractal.
- `D_f` does not prove `I`.
- `D_f_hat` does not create `I_fractal`.
- `dF` is not generic indeterminacy.
- Raw `T/I/F`, raw data, raw keys, raw media, and raw OCR are not exported.
- The implementation must preserve:

```text
I -> I_system^S -> D_f -> dF -> i_fractal
```

In the QLC build, `dF` is the bounded operational bridge produced from
`D_f_hat` only when `I_system^S` authorizes the fractal interpretation.

## Extracted Book Rules

The PDF gives the following implementation rules:

1. A neutrosophic object is read as `{T, I, F}`, not as a forced true/false.
2. `I` must first become system-local: `I -> I_system^S`.
3. `D_f` measures multi-scale complexity, not universal indeterminacy.
4. `D_f_hat = (D_f - D_min) / (D_max - D_min)` makes the measure comparable
   only when `D_max > D_min`.
5. `I_fractal` may receive `D_f_hat` only when `Adm = true` and the source of
   `I_system^S` is measurable local fractal complexity.
6. If `Omega`, `S`, `M`, bounds, source, or stability are missing, suspend.
7. Plithogenic contradiction must not be confused with geometric fractality.
8. A construction is stronger when it can reject or suspend.

## QLC Translation

For QLC, a tile candidate becomes build-admissible only after four gates:

```text
tile_candidate
  -> geometry_gate
  -> plithogenic_classification_gate
  -> fractal_path_measurement_gate
  -> T_dF_F_admission_gate
```

The output is not "this tile is true forever". The output is:

```text
accept | suspend | reject
```

with reason codes and redacted fingerprints.

## Tile Domain Contract

Each tile candidate must declare:

```text
TileCandidate = {
  tile_id,
  tile_type,              # thin | thick
  vertices,               # four ordered points
  edges,                  # four equal-length edges within tolerance
  angles,                 # thin: 36/144, thick: 72/108
  centroid,
  generation_index,
  inflation_parent_ids,
  adjacency_ids,
  source_function_ids,
  omega_id,
  region_id,
  boundary_id
}
```

The tile is rejected before plithogenic or fractal logic if:

- type is not `thin` or `thick`;
- vertices are missing or unordered;
- edge lengths are not equal within tolerance;
- angles violate the selected Penrose type;
- adjacency creates an impossible overlap;
- source functions are missing.

## Plithogenic Classification Gate

The plithogenic gate gives the tile a classification vector:

```text
PlithogenicTileClass = {
  Attr,
  Val,
  Dom,
  Contr,
  C_phi,
  source_role,
  classification_fingerprint
}
```

Required interpretation:

- `Attr` is the active attribute family for the tile.
- `Val` is the tile value vector in that attribute family.
- `Dom` is the dominant value profile for the local scaffold.
- `Contr` is numeric contradiction or dissimilarity, not a text reason.
- `C_phi` is the phi-weighted contradiction profile.

For Penrose QLC, useful attributes are:

```text
Attr = {
  tile_type,
  angle_profile,
  edge_signature,
  adjacency_signature,
  inflation_lineage,
  source_function_profile,
  data_pressure_profile
}
```

The classification gate does not accept the tile by itself. It produces
structured evidence for the next gate.

## Fractal Path Gate

The book requires a carrier before `D_f` becomes meaningful. For QLC, the
carrier is not the isolated rhombus. The carrier is the local path or cluster
around that rhombus:

```text
FractalPath(tile) = {
  seed_tile,
  inflation_path,
  neighbor_shells,
  boundary_trace,
  accepted_cluster,
  scale_range_S,
  measurement_method_M
}
```

Allowed carriers:

- `fractal_boundary`: local boundary trace across accepted neighbor shells;
- `fractal_growth`: inflation lineage across generations;
- `fractal_projection`: declared cut-and-project trace;
- `fractal_cluster`: local patch around the tile centroid.

Rejected carriers:

- class name only;
- source URL only;
- visual irregularity without `S` and `M`;
- plithogenic contradiction alone;
- dynamic/chaotic behavior without a fractal measurement carrier.

## D_f And dF Gate

The measurement gate computes local complexity:

```text
D_f_tile = box_count(
  carrier = FractalPath(tile),
  Omega = patch_domain,
  S = scale_range,
  M = measurement_method
)
```

Then:

```text
D_f_hat_tile = (D_f_tile - D_min) / (D_max - D_min)
```

Required bounds:

```text
D_max > D_min
D_min <= D_f_tile <= D_max
0 <= D_f_hat_tile <= 1
```

Operational bridge:

```text
dF_tile = D_f_hat_tile
```

but only if:

```text
Adm_precheck = true
source(I_system^S(tile)) in {
  fractal_boundary,
  fractal_growth,
  fractal_projection,
  fractal_cluster
}
```

Otherwise:

```text
dF_tile = suspended
I_fractal_tile = suspended
```

## T, dF, F Admission Reading

The QLC tile admission uses `T, dF, F`, not raw universal `T/I/F`.

```text
T_tile = support_for_build(tile)
dF_tile = normalized_fractal_tension(tile)
F_tile = scaffold_violation(tile)
```

`T_tile` should increase when:

- geometry is valid;
- matching rules are satisfied;
- adjacency is coherent;
- source functions are present;
- plithogenic contradiction is low;
- `D_f` measurement is stable;
- carrier source is valid.

`dF_tile` should represent:

- local multi-scale tension;
- boundary complexity;
- inflation-growth complexity;
- projection complexity;
- not generic uncertainty.

`F_tile` should increase when:

- rhombus geometry is false;
- angle or edge constraints fail;
- tile overlaps invalidly;
- plithogenic contradiction is high;
- source function is missing;
- `D_f` is unstable or out of bounds;
- carrier source is not fractal;
- raw data or raw secret export is attempted.

## Admission Function

Recommended function:

```text
Adm_tile = admit_tile_for_build(T_tile, dF_tile, F_tile, preconditions)
```

Decision rules:

```text
reject if geometry_valid is false
reject if source_function_profile is missing
reject if raw_data_export_requested is true
reject if F_tile >= reject_threshold

suspend if Omega is missing
suspend if S is missing
suspend if M is missing
suspend if D_max <= D_min
suspend if D_f measurement is unstable
suspend if I_system^S cannot identify a fractal source
suspend if dF_tile is unavailable

accept if geometry_valid is true
accept if source_function_profile is present
accept if T_tile >= accept_threshold
accept if F_tile <= false_threshold
accept if dF_tile is within the configured build band
```

The `build band` is not "low is always good" or "high is always good". It is
the configured fractal tension range the patch wants for a stable orb:

```text
dF_min_build <= dF_tile <= dF_max_build
```

This lets the system reject flat/dead candidates and also reject unstable
over-complex candidates.

## From Admitted Tiles To Orbs

An orb is a redacted envelope around an accepted local lattice cluster. It is
not a mystical object and not a proof of security.

```text
Orb = {
  orb_id,
  orb_type,
  patch_fingerprint,
  accepted_tile_ids,
  rejected_tile_fingerprints,
  suspended_tile_fingerprints,
  T_dF_F_summary,
  D_f_profile,
  plithogenic_profile,
  source_function_profile,
  data_envelope_fingerprint,
  claim_boundary
}
```

Orb build rules:

- only accepted tiles can carry data references;
- suspended tiles may appear as boundary warnings;
- rejected tiles cannot carry data references;
- the orb exports fingerprints and summaries, not raw data.

## Data Envelope Wrapping

Data is wrapped through accepted tile/orb carriers:

```text
data_ref -> chunk_fingerprint -> admitted_tile -> orb_envelope
```

Allowed envelope fields:

- `chunk_id`
- `chunk_fingerprint`
- `tile_id`
- `orb_id`
- `lattice_fingerprint`
- `key_manifest_fingerprint`
- `source_profile_fingerprint`
- `redaction_policy`

Forbidden envelope fields:

- raw plaintext;
- raw OCR;
- raw media;
- raw private key;
- raw token;
- raw per-particle secret.

## Function List For Implementation

Implement in this order:

```text
validate_tile_geometry(tile)
classify_plithogenic_tile(tile, source_profiles)
build_fractal_path(tile, patch, carrier_type)
measure_local_df(fractal_path, Omega, S, M)
normalize_df(D_f, D_min, D_max)
resolve_i_system_source(tile, classification, df_profile)
compute_t_df_f(tile, classification, df_profile)
admit_tile_for_build(admission_profile)
build_orb_envelope(accepted_tiles, data_refs)
export_redacted_orb_template(orb)
```

## Pseudocode

```text
for tile in candidate_tiles:
  geometry = validate_tile_geometry(tile)
  if not geometry.valid:
    reject(tile, "invalid_penrose_geometry")
    continue

  plith = classify_plithogenic_tile(tile, source_profiles)
  if not plith.source_function_profile:
    reject(tile, "missing_source_function_profile")
    continue

  path = build_fractal_path(tile, patch, carrier_type)
  if not path.has_required(Omega, S, M):
    suspend(tile, "missing_fractal_measurement_context")
    continue

  df = measure_local_df(path, Omega, S, M)
  df_hat = normalize_df(df.value, D_min, D_max)
  if df_hat.suspended:
    suspend(tile, df_hat.reason)
    continue

  source = resolve_i_system_source(tile, plith, df)
  if source not in allowed_fractal_sources:
    suspend(tile, "i_system_source_not_fractal")
    continue

  profile = compute_t_df_f(tile, plith, df_hat)
  admission = admit_tile_for_build(profile)
  record(tile, admission)

orb = build_orb_envelope(accepted_tiles, data_refs)
return export_redacted_orb_template(orb)
```

## Tests Required

- accepts valid thin rhombus with valid carrier and bounded `dF`;
- accepts valid thick rhombus with valid carrier and bounded `dF`;
- rejects invalid rhombus angles;
- rejects unequal edge lengths;
- suspends missing `Omega`;
- suspends missing `S`;
- suspends missing `M`;
- suspends `D_max <= D_min`;
- suspends unstable `D_f`;
- suspends plithogenic contradiction when it is not geometric fractality;
- rejects missing source function profile;
- rejects raw data export;
- keeps raw `T/I/F` out of export;
- exports only orb/data envelope fingerprints.

## Implementation Consequence

The next code pass should not add more labels. It should implement the
admission mechanism:

```text
source functions + Penrose geometry + plithogenic classification
  -> fractal path carrier
  -> D_f
  -> D_f_hat
  -> dF when I_system^S permits
  -> T,dF,F admission
  -> accepted tiles
  -> orb envelope
  -> redacted data template
```

This is the bridge between the math and the build.
