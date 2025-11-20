"""
Pytest configuration and fixtures

This file is automatically loaded by pytest
"""

import pytest
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def sample_url():
    """Sample URL for testing"""
    return "https://www.olx.kz/test"


@pytest.fixture
def sample_query():
    """Sample search query"""
    return "test query"


@pytest.fixture
def sample_chat_id():
    """Sample Telegram chat ID for testing"""
    return 123456789

