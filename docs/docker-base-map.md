# Docker Base Map

This MVP maps a public-safe FfeD-QLC layer onto a local CodeProject.AI mesh.

## Default CPAI Blocks

| Block | Public role | URL | Docker network identifier | Persistent volume |
|---|---|---|---|---|
| Quasicrystal | primary QLC study-case block | `http://localhost:33168` | `block-quasicrystal` | `studycase-cpai-quasicrystal-data` |
| Neutrosophique | reference study-case block | `http://localhost:33268` | `block-neutrosophique` | `studycase-cpai-neutrosophique-data` |
| FNP-QNN | reference model/simulator block | `http://localhost:33368` | `block-fnp-qnn` | `studycase-cpai-fnp-qnn-data` |

## Public Boundary

The MVP only exposes a bounded software pattern:

```text
source -> provenance check -> trust score -> Adm decision
```

It does not publish private theory material, secrets, biological claims, clinical claims, or security certification claims.

## Portainer Labels

Use these labels to identify the Lego blocks in Portainer:

```text
studycase.block.id
studycase.block.title
studycase.volume.role
```

