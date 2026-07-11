"""
Smoke test: configuration loading and defaults
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_config_imports():
    """Verify config module loads without errors"""
    import config
    assert hasattr(config, 'SERVER_PORT')
    assert hasattr(config, 'DEEPSEEK_BASE_URL')
    assert hasattr(config, 'KNOWLEDGE_DIR')
    assert isinstance(config.SERVER_PORT, int)
    assert config.SERVER_PORT > 0


def test_config_defaults():
    """Verify sensible defaults are set"""
    import config
    assert config.CHUNK_SIZE == 500
    assert config.CHUNK_OVERLAP == 50
    assert config.TOP_K_RETRIEVAL == 5
    assert config.DEEPSEEK_BASE_URL == "https://api.deepseek.com"
    assert config.DEEPSEEK_MODEL == "deepseek-chat"


def test_config_env_fallback():
    """Verify env var fallback behavior (defaults when not set)"""
    import config
    # When env vars are not set, should get default values
    assert config.KNOWLEDGE_DIR is not None
    assert config.CHROMA_PERSIST_DIR is not None
    assert "vectordb" in config.CHROMA_PERSIST_DIR
