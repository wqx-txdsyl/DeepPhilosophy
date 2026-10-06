"""Keep historical release snapshots explicit, separate from current behavior."""
import pytest


def pytest_addoption(parser):
    parser.addoption("--historical-snapshots", action="store_true", default=False,
                     help="Run explicitly marked old-release byte-freeze assertions as well.")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--historical-snapshots"):
        return
    historical = pytest.mark.skip(reason=(
        "Historical release byte freeze, not a current behavior check. "
        "Run with --historical-snapshots -m historical_snapshot to replay it."))
    for item in items:
        if item.get_closest_marker("historical_snapshot"):
            item.add_marker(historical)
