from defect_engine.loader import load_bridge_dataset


def test_loader():

    records = load_bridge_dataset(
        "datasets/bridge_digital_twin_dataset.csv"
    )

    assert len(records) > 0

    print("✓ Loader passed")