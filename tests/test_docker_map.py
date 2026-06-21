from ffed_qlc import DEFAULT_STUDYCASE_BLOCKS


def test_default_map_has_three_studycase_blocks() -> None:
    assert len(DEFAULT_STUDYCASE_BLOCKS) == 3


def test_block_ids_are_stable() -> None:
    ids = {block.block_id for block in DEFAULT_STUDYCASE_BLOCKS}

    assert ids == {"block-quasicrystal", "block-neutrosophique", "block-fnp-qnn"}

