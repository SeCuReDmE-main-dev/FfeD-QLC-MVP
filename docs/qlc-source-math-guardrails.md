# QLC Source Math Guardrails

Status: source-ingestion digest before implementation.

These 10 references are not UI items and not hardcoded product labels. They are
mathematical sources that compile into functions and guardrails for the QLC
lattice workbench.

## Non-Negotiable Boundary

- The implementation must not treat the source URLs as the feature.
- URLs belong in source metadata, docs, fixtures, or provenance records, not as
  front-end concepts.
- The runtime math must consume source-derived functions:
  `source -> source_function_profile -> lattice/gate/measurement`.
- Raw source bodies and raw T/F/I values are not exported.
- `FQLC1` remains unchanged.
- Security-certification and quantum-proof claims remain rejected.

## Canonical Penrose Variables

These variables are implementation contracts, not decorative names:

| Symbol | Meaning | Constraint |
|---|---|---|
| `phi` | golden ratio | `(1 + sqrt(5)) / 2` |
| `a` | common edge length | `a > 0`, default `1` |
| `thin` | Penrose thin rhombus | angles `[36, 144, 36, 144]` |
| `thick` | Penrose thick rhombus | angles `[72, 108, 72, 108]` |
| `V_t` | tile vertices | ordered 4-point polygon |
| `E_t` | tile edges | equal edge length within tolerance |
| `C_t` | tile centroid | mean of ordered vertices |
| `A_t` | tile area | `a^2 * sin(theta_min)` |
| `M_inf` | inflation count matrix | `[[2, 1], [1, 1]]` for `[thick, thin]` |
| `Omega` | measurement domain | bounding box of accepted tile centroids |
| `S` | box-counting scales | finite increasing scale list, default `[4, 8, 16]` |
| `D_f` | box-counting dimension | bounded by `[D_min, D_max]` |
| `D_f_hat` | normalized `D_f` | `(D_f - D_min) / (D_max - D_min)` clipped to `[0, 1]` |

## Source-To-Function Profiles

### S01: Plithogenic Set / Logic / Probability / Statistics

Mathematical import:

- elements have attributes;
- attributes have many values;
- each value has an appurtenance degree;
- contradiction/dissimilarity is measured against a dominant value;
- aggregation depends on contradiction.

Function profile:

```text
f_plithogenic_admission(x):
  Attr = source-defined attribute vector
  Val = candidate tile/source value vector
  Contr = dissimilarity(Val, dominant_value)
  C_phi = phi_weighted_contradiction(Contr)
  Adm = threshold(C_phi, provenance, claim_scope)
```

Implementation guardrail:

- `Contr` is not a string reason; it must be a numeric function.
- `Adm` is a result of thresholds over `Contr`, provenance, and claim boundary.

### S02: Plithogenic Graphs

Mathematical import:

- vertices and edges can be represented by `1 x n` row matrices;
- row-matrix components define edge relations;
- edge labels/weights may be crisp, fuzzy, intuitionistic, neutrosophic, real,
  complex, or multigraph values;
- two row vectors can produce edge multiplicity when components coincide.

Function profile:

```text
f_row_matrix_edge(u, v):
  shared = {i | row_u[i] == row_v[i]}
  edge_multiplicity = |shared|
  edge_label = row_mask(shared)
  edge_weight = aggregate_component_weight(shared)
```

Implementation guardrail:

- adjacency is reconstructed from tile/source function vectors, not just
  geometric distance.
- edge labels must survive export as metadata.

### S03: Plithogenic n-Super Hypergraph

Mathematical import:

- multi-attribute decision structures use hypergraph-like connectors;
- enveloping, super-enveloping, and dominant enveloping vertices organize
  decision flow;
- dominant vertices classify as input, intervene, or output.

Function profile:

```text
f_connector(tile_set):
  connector = hyperedge(tile_ids, source_function_ids)
  dominant_role = input | intervene | output
  connector_weight = aggregate_admissibility(tile_set)
```

Implementation guardrail:

- multi-tile relations must be modeled as connector/hyperedge metadata.
- source contribution is not only per-tile; it can be per-connector.

### S04: Symbolic Plithogenic Algebraic Structures

Mathematical import:

- operations are governed by prevalence order;
- absorbance law means a stronger component can absorb a weaker component;
- symbolic plithogenic components may be independent, dependent, or partially
  dependent.

Function profile:

```text
f_prevalence_resolve(a, b):
  if order(a) >= order(b): return a
  return b
```

Implementation guardrail:

- conflicting source functions must resolve by prevalence, not arbitrary order.
- this controls source-function composition during inflation and gate decisions.

### S05: Single-Valued Plithogenic Graph

Mathematical import:

- contradiction impacts decision making;
- multi-valued attribute data can be represented by plithogenic graph algebra;
- infimum and supremum are useful visualization/aggregation boundaries.

Function profile:

```text
f_inf_sup_gate(values):
  lower = inf(values)
  upper = sup(values)
  interval_width = upper - lower
  admission_score = 1 - normalized(interval_width)
```

Implementation guardrail:

- `accept/suspend/reject` must be reproducible from numerical bounds.
- high interval width increases friction.

### S06: Entanglement In Graph States

Mathematical import:

- graph states encode multipartite relationships through graph structure;
- useful descriptions can scale moderately with system size;
- graph topology is a carrier for state relationships.

Function profile:

```text
f_graph_state_carrier(G):
  carrier_size = |V| + |E|
  locality_class = local_topology_signature(G)
  state_weight = normalize(carrier_size, topology)
```

Implementation guardrail:

- quantum graph-state sources constrain topology metadata only.
- they do not certify cryptographic security.

### S07: Quantum Walks On Graphs

Mathematical import:

- quantum walks on finite graphs are unitary/reversible;
- they do not converge to a stationary distribution in the classical sense;
- spreading/confined behavior can be measured by mixing, filling, or dispersion
  style metrics.

Function profile:

```text
f_walk_dispersion(adjacency):
  transition_phase = phase_from_phi_basis(adjacency)
  dispersion = spread_measure(transition_phase)
  confinement = local_neighborhood_measure(adjacency)
```

Implementation guardrail:

- the lattice should expose dispersion/confinement diagnostics, not claim
  convergence.

### S08: Quantum Multigraph / Multihypergraph States

Mathematical import:

- multigraph and multihypergraph states are defined by operations on edges and
  hyperedges;
- dimensionality matters, especially prime/composite conditions.

Function profile:

```text
f_multihyperedge_operation(edge_or_hyperedge, d):
  if is_prime(d): use prime_dimension_rule
  else: mark subset_condition
  return operation_signature
```

Implementation guardrail:

- connector nodes must include dimension/profile metadata.
- hyperedge operations must be explicit and bounded.

### S09: Fusion-Based Graph State Optimization

Mathematical import:

- graph-state generation can be optimized by simplifying a target graph;
- a fusion network is built;
- an order of fusions is determined;
- success probability and resource overhead are evaluated.

Function profile:

```text
f_fusion_order(target_graph):
  simplified = simplify(target_graph)
  network = build_fusion_network(simplified)
  order = deterministic_fusion_order(network)
  overhead = resource_overhead(order)
```

Implementation guardrail:

- tile generation must expose deterministic build order.
- target count and complexity caps are part of the math, not UI preference.

### S10: Quantum Quasicrystal Patterns

Mathematical import:

- quasicrystal configurations can emerge in two-dimensional systems;
- interacting wave-vector or excitation-spectrum constraints stabilize
  non-periodic patterns;
- variational parameters and acceptance windows matter.

Function profile:

```text
f_cut_project_accept(candidate):
  projected = project_5d_to_2d(candidate, phi_basis)
  internal = project_5d_to_internal(candidate, phi_basis)
  accept = internal in acceptance_window
```

Implementation guardrail:

- cut-and-project must be an actual bounded profile:
  projection basis, seed shift, window, candidate cap, dedupe.
- `engine=cut_project` is not a label; it chooses this function path.

## Required Engine Contracts

### Inflation Engine

Input:

```text
InflationInput(
  initial_patch,
  source_function_profiles,
  target_tile_count,
  inflation_depth,
  edge_length,
  phi
)
```

Output:

```text
InflationOutput(
  tiles,
  adjacency,
  source_contribution,
  diagnostics,
  engine="inflation"
)
```

Rules:

- depth `0` returns the minimal initial patch.
- substitution matrix: `[[2, 1], [1, 1]]` over `[thick, thin]`.
- each tile must remain `thin` or `thick`.
- vertices are normalized and nearby vertices are merged by tolerance.
- adjacency is reconstructed after each inflation step.
- source-function profiles weight substitution choice, generation index, and
  source contribution.
- stop at `target_tile_count`.

### Cut-And-Project Engine

Input:

```text
CutProjectInput(
  source_function_profiles,
  target_tile_count,
  phi_basis,
  acceptance_window,
  seed_shift,
  candidate_cap
)
```

Output:

```text
CutProjectOutput(
  candidates,
  accepted_tiles,
  adjacency,
  projection_metadata,
  engine="cut_project"
)
```

Rules:

- build candidates from a bounded 5D integer grid.
- project to 2D and internal space using a phi-compatible basis.
- accept only candidates inside the source-weighted window.
- map accepted candidates into `thin`/`thick` rhombi.
- dedupe by edge signature.
- reconstruct adjacency and compare metadata against inflation output.

## Plithogenic Gate Contract

Local candidate T/F/I can be calculated but not exported.

```text
T_local = trust_weight * scaffold_match
F_local = contradiction_weight * geometry_or_source_violation
I_local = 1 - abs(T_local - F_local)
friction = I_to_friction(I_local, source_profile)
Contr = source_contradiction(source_profile, candidate)
C_phi = phi_weighted_contradiction(Contr)
Adm = threshold(admissibility_score)
```

Thresholds:

| State | Rule |
|---|---|
| `accept` | provenance present, geometry valid, score high |
| `suspend` | missing scale/method/provenance or medium score |
| `reject` | out of domain, invalid geometry, unsafe claim, low score |

Export policy:

- export `friction`, `Contr`, `C_phi`, `Adm`, `D_f`, `D_f_hat`, `dF`,
  `i_fractal`;
- do not export raw T/F/I vectors;
- include `audit_fingerprint`;
- include reason codes.

## D_f / D_f_hat Contract

```text
N(s) = occupied boxes of Omega at scale s
D_f = slope(log(N(s)), log(1/s))
D_f_hat = clamp((D_f - D_min) / (D_max - D_min), 0, 1)
```

Rules:

- `Omega` is the accepted patch domain.
- `S` must be non-empty and strictly increasing.
- `M` must name the measurement method.
- `D_max > D_min`.
- invalid bounds, missing scale, or missing method suspend the measurement.
- `D_f_hat` is a measurement, not truth or security proof.

## Implementation Consequence

The next code pass must implement:

1. `SourceFunctionProfile` compiler from the 10 fetched sources.
2. `InflationEngine` using source functions, not source labels.
3. `CutProjectEngine` using source functions, not source labels.
4. `PlithogenicAdmission` from numeric functions.
5. `D_f / D_f_hat` with explicit measurement metadata.
6. API endpoints that expose diagnostics and redacted exports.
7. Frontend panels that show math functions and diagnostics, not source URL
   lists.
