from ffed_qlc import derive_chunk_key_schedule, inspect_container, pack_bytes


def test_chunk_key_schedule_is_deterministic_for_manifest() -> None:
    manifest = {
        "source_sha256": "a" * 64,
        "lattice_seed_fingerprint": "seed-1",
        "projection_profile": {"projection_seed_fingerprint": "projection-1"},
    }

    first = derive_chunk_key_schedule(manifest, 3)
    second = derive_chunk_key_schedule(manifest, 3)

    assert first == second
    assert first["chunk_count"] == 3
    assert first["key_material_exposed"] is False
    assert all(chunk["key_material_exposed"] is False for chunk in first["chunks"])


def test_chunk_key_schedule_changes_when_manifest_changes() -> None:
    first = derive_chunk_key_schedule(
        {
            "source_sha256": "a" * 64,
            "lattice_seed_fingerprint": "seed-1",
            "projection_profile": {"projection_seed_fingerprint": "projection-1"},
        },
        1,
    )
    second = derive_chunk_key_schedule(
        {
            "source_sha256": "b" * 64,
            "lattice_seed_fingerprint": "seed-1",
            "projection_profile": {"projection_seed_fingerprint": "projection-1"},
        },
        1,
    )

    assert first["chunks"][0]["subkey_fingerprint"] != second["chunks"][0]["subkey_fingerprint"]


def test_container_manifest_includes_chunk_key_schedule() -> None:
    container = pack_bytes(b"qlc chunk schedule", "passphrase")
    manifest = inspect_container(container)["qlc_manifest"]

    assert manifest["chunk_key_schedule"]["schema"] == "ffed.qlc.granular_chunk_key_schedule.v1"
    assert manifest["chunk_key_schedule"]["chunks"][0]["key_material_exposed"] is False
    assert derive_chunk_key_schedule(container, 1) == manifest["chunk_key_schedule"]
