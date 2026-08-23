from chronoplay.media.states import AssetState


def test_asset_state_values() -> None:
    assert AssetState.DISCOVERED.value == "discovered"
    assert AssetState.VALIDATING.value == "validating"
    assert AssetState.VALID.value == "valid"
    assert AssetState.INVALID.value == "invalid"
    assert AssetState.MISSING.value == "missing"
    assert AssetState.CORRUPT.value == "corrupt"
    assert AssetState.UNAVAILABLE.value == "unavailable"
