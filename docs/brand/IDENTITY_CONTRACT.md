# FfeD-QLC Public Identity Contract

**Status:** implementation baseline — changes require explicit maintainer approval  
**Scope:** public repository, website, README, documentation, UI, presentations, and approved media exports  
**Public repository:** `SeCuReDmE-main-dev/FfeD-QLC-MVP`

This document prevents accidental redesign and repeated brand refactoring. Existing approved assets are the source of truth. New public surfaces must compose the identity from those assets instead of redrawing or replacing them.

## 1. Public coordinates

- **Primary name:** `FfeD-QLC`
- **Protocol meaning:** `Quasicrystal Lattice Cryptography`
- **Webspace:** `https://ffed-qlc.securedme.ca/`
- **Email:** `ffed-qlc@securedme.ca`
- **Public repository:** `https://github.com/SeCuReDmE-main-dev/FfeD-QLC-MVP`
- **Research attribution:** `ORCID 0009-0007-2904-0443`

The public product is a bounded admissibility and evidence-governance layer for AI and research workflows. Its documented operational sequence is:

```text
source or request
  -> provenance check
  -> secret-boundary check
  -> admissibility decision
  -> isolated execution
  -> observable event
```

The public decision language remains:

```text
accept | suspend | reject
```

## 2. Canonical source order

When assets disagree, use this order:

1. The primary mark currently referenced by the repository README:
   - `assets/Logo draft version/logo centre 1.png`
2. The full prepared lockup:
   - `assets/full logo versipon 1.png`
3. Existing approved 2D/vector variants in:
   - `assets/Logo draft version/`
4. Existing typography and logo-letter studies in:
   - `assets/font style schema/`
5. Guardian and storyboard assets declared in:
   - `assets/Mascotte/MANIFEST.json`
6. Current public product behavior and boundaries in:
   - `README.md`
   - `docs/investor-brief.md`
   - current tests and implementation

No generated replacement supersedes a higher-ranked source without explicit maintainer approval.

## 3. Locked primary logo rule

The existing official 2D mark is **locked**.

Do not:

- redraw its geometry;
- simplify or add internal elements;
- alter proportions;
- distort it through perspective;
- crop into it;
- replace it with a 3D variant as the default public mark;
- substitute a newly generated symbol;
- combine it with the FNP-QNN owl, the Synthia mark, or another project mark;
- recolor it outside the existing approved variant family.

Allowed operations:

- proportional scaling;
- placement on an approved background;
- export optimization without visual change;
- selection of an existing monochrome or color variant for accessibility;
- addition of transparent safety space;
- composition with an approved wordmark without changing the mark itself.

The logo must remain recognizable at 32 px and must retain adequate clear space.

## 4. Wordmark and typography rule

The variable under development is the **letter system**, not the locked logo.

All public wordmarks must derive from the existing files in:

```text
assets/font style schema/
```

Including:

```text
Font style 1.png
Font style 2.png
Font style 3.png
Font style 4.png
Font style 5.png
Font style 6.png
Logo style template 2d.png
Logo style template 2d v2.png
Logo style template 2d v3.png
Logo style template 2d v4.png
Logo style template 2d v5.png
```

Rules:

- Do not invent a new primary type treatment before reviewing these templates.
- Preserve the casing `FfeD-QLC`.
- Use `Protocol` or `Protocole` only as a secondary descriptor, never as a replacement for the product name.
- Do not stretch, condense, outline, bevel, or add effects that conflict with the selected existing template.
- The final primary wordmark variant must be documented by exact source filename after maintainer approval.

## 5. Brand architecture

### Primary brand

`FfeD-QLC`

### Product role

A bounded control layer before execution and publication:

- provenance;
- secret-boundary control;
- admissibility;
- isolation;
- observable evidence.

### Public behavioral vocabulary

- `accept`: evidence and scope satisfy the declared policy;
- `suspend`: context, provenance, or review is incomplete;
- `reject`: the request violates an explicit boundary or fails the declared rule.

`Suspend` is a normal governance state, not a failure and not an accusation.

## 6. Guardian system

### Primary public guardian: AEGIS

AEGIS is the primary public mascot direction: a calm quasicrystal pangolin representing layered, non-aggressive protection. Use the existing assets in:

```text
assets/Mascotte/AEGIS/
```

AEGIS explains the protection model to humans. The logo must appear as an active trust seal, not decorative artwork.

### Secondary internal avatar: TESS

TESS may represent the admissibility policy or internal decision engine. Use it inside decision, rule, or audit interfaces; do not give it equal prominence with AEGIS on the main public identity surface.

### Specialized guardians

- `VIGIL`: weak-signal inspection and detection;
- `OCTA`: distributed orchestration and network mapping;
- `AION`: continuity, archive, and long-horizon governance.

These guardians support specific contexts. They must not fragment the main landing-page identity or replace AEGIS as the dominant public guardian without explicit approval.

## 7. Non-negotiable guardian rules

- Protector, not warrior.
- Competent, not omniscient.
- Accessible, not childish.
- Explainable, not mysterious authority.
- Modular across icon, avatar, UI, documentation, animation, and print.
- No medical, military, police, government, or certification symbolism.
- Must remain readable in monochrome.
- Must remain visually distinct from the FNP-QNN owl mascot.
- The FfeD-QLC logo is carried as a vertical, undistorted active seal.
- No weapons, threatening teeth, attack posture, or claims of invulnerability.

## 8. Product-state visual system

Use the already defined behavioral states consistently:

| State | Meaning | Visual behavior | Color role |
|---|---|---|---|
| Rest | available and stable | calm posture, stable seal | blue |
| Inspection | evaluating evidence | aligned facets or scanning wave | cyan |
| Accept | policy satisfied | open posture | green / blue |
| Suspend | evidence or context incomplete | partially closed protection with visible review path | gold / violet |
| Reject | explicit boundary violation | fully closed boundary, no aggression | coral / red |
| Human review | decision delegated | attentive posture, pending seal | white / gold |
| Internal error | system problem, not user blame | neutral posture, muted signal | gray |

Do not use status colors decoratively in ways that weaken their operational meaning.

## 9. Voice and copy contract

FfeD-QLC communicates in this order:

```text
Observation -> policy or limitation -> decision -> next safe action
```

Required qualities:

- factual;
- calm;
- concise;
- traceable;
- non-accusatory;
- explicit about uncertainty;
- explicit about system boundaries.

Avoid:

- fear-based language;
- guilt or blame;
- claims that every attack can be predicted;
- using “quantum” as proof of superiority;
- calling `suspend` a failure;
- claims of certification, guaranteed security, or invulnerability.

## 10. Public positioning and claim boundary

Safe public positioning:

> FfeD-QLC is a public alpha prototype for authenticated artifact handling, provenance-aware admissibility, bounded workflow governance, isolated execution, and observable evidence in AI and research pipelines.

The public implementation may discuss documented mechanisms such as:

- a versioned FQLC container;
- reversible structural transformation;
- `scrypt` key derivation;
- authenticated encryption with ChaCha20-Poly1305;
- pack, unpack, and verify CLI paths;
- a minimal `accept | suspend | reject` gate;
- public-safe FNP-QNN payload generation;
- optional E2B and Datadog demonstration paths.

Do not claim:

- production security certification;
- a standardized post-quantum cryptosystem;
- conventional lattice-cryptography certification;
- complete end-to-end gateway proof unless directly tested and recorded;
- automatic enforcement by the gate where it is not wired into the execution path;
- actual YOLO/OCR/redaction execution when only metadata packaging exists;
- production secret management;
- medical, biological, clinical, or physical proof.

## 11. Website composition contract

The first public landing page must use the real asset library. It must not recreate the identity from scratch.

### Hero hierarchy

1. locked primary logo;
2. approved `FfeD-QLC` wordmark from the existing typography family;
3. bounded product description;
4. public coordinates;
5. AEGIS as the primary guardian;
6. the `accept | suspend | reject` system;
7. the provenance-to-observation workflow.

### Required public coordinates

```text
ffed-qlc.securedme.ca
ffed-qlc@securedme.ca
SeCuReDmE-main-dev/FfeD-QLC-MVP
```

### Asset handling

- Copy canonical assets into the website package; do not depend permanently on hotlinks.
- Preserve source aspect ratios.
- Use `object-fit: contain` for logos and guardians.
- Add transparent breathing room rather than cropping.
- Provide monochrome or text fallbacks.
- Do not load every mascot, storyboard, and logo variant above the fold.
- Use one primary mark, one wordmark, and one dominant guardian in the hero.

## 12. Identity separation within SeCuReDmE

FfeD-QLC is related to the SeCuReDmE ecosystem but retains a distinct identity.

- Do not merge it visually with Synthia.
- Do not reuse the FNP-QNN owl as its mascot.
- Do not replace AEGIS with a generic robot or cyber-warrior.
- Cross-project diagrams may show relationships, but each project keeps its own mark, palette roles, and behavioral language.

## 13. Change-control rule

Any proposed change to the primary logo, wordmark source, guardian hierarchy, public state colors, product name, or website hero must include:

1. exact current asset path;
2. exact proposed replacement path;
3. reason for change;
4. screenshots at desktop, mobile, and 32/64/128 px identity sizes;
5. accessibility and contrast check;
6. confirmation that the public product claims remain accurate;
7. explicit maintainer approval.

Without these seven items, preserve the current identity.

## 14. Implementation sequence

1. Verify the complete asset manifest and record missing files without replacing them.
2. Select the exact existing wordmark template with the maintainer.
3. Build a centralized web asset map using repository-relative canonical paths.
4. Compose the README banner and landing page from the locked mark, selected wordmark, and AEGIS.
5. Apply the product-state system to UI badges and guardian states.
6. Validate desktop, mobile, monochrome, and small-size rendering.
7. Package the static site for `ffed-qlc.securedme.ca`.
8. Deploy only after visual review and a backup of the existing cPanel document root.

This sequence is deliberately conservative. It protects the hundreds of hours already invested in the identity and prevents a deployed surface from forcing another full redesign.
