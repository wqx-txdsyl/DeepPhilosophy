"""
Smoke test: philosopher database loading and lookup
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_philosophers_loaded():
    """Verify philosophers.json loads correctly"""
    from db import PHILOSOPHERS, PHILOSOPHER_COUNT
    assert PHILOSOPHER_COUNT > 0
    assert PHILOSOPHER_COUNT == len(PHILOSOPHERS)
    # Spot-check a few well-known philosophers exist
    assert "柏拉图" in PHILOSOPHERS or any("柏拉图" in k for k in PHILOSOPHERS)


def test_lookup_hit():
    """Verify O(1) lookup finds a known philosopher"""
    from db import get_philosopher_info
    # Try with a few common names
    result = get_philosopher_info("柏拉图")
    if result is None:
        result = get_philosopher_info("孔子")
    if result is None:
        result = get_philosopher_info("亚里士多德")
    assert result is not None, "Could not find any of: 柏拉图, 孔子, 亚里士多德"
    assert "era" in result or "bio" in result


def test_lookup_miss():
    """Verify lookup returns None for nonexistent philosopher"""
    from db import get_philosopher_info
    result = get_philosopher_info("不存在的哲学家XYZ123")
    assert result is None


def test_aliases_loaded():
    """Verify name_aliases.json loads correctly"""
    from db import NAME_ALIASES
    assert isinstance(NAME_ALIASES, dict)
