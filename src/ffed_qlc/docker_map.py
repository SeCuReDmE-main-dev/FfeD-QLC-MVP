from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StudycaseBlock:
    name: str
    block_id: str
    cpai_url: str
    private_network: str
    persistent_volume: str


DEFAULT_STUDYCASE_BLOCKS: tuple[StudycaseBlock, ...] = (
    StudycaseBlock(
        name="quasicrystal",
        block_id="block-quasicrystal",
        cpai_url="http://localhost:33168",
        private_network="studycase-quasicrystal-private",
        persistent_volume="studycase-cpai-quasicrystal-data",
    ),
    StudycaseBlock(
        name="neutrosophique",
        block_id="block-neutrosophique",
        cpai_url="http://localhost:33268",
        private_network="studycase-neutrosophique-private",
        persistent_volume="studycase-cpai-neutrosophique-data",
    ),
    StudycaseBlock(
        name="fnp-qnn",
        block_id="block-fnp-qnn",
        cpai_url="http://localhost:33368",
        private_network="studycase-fnp-qnn-private",
        persistent_volume="studycase-cpai-fnp-qnn-data",
    ),
)

