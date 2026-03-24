import pytest
from unittest.mock import patch, MagicMock
import numpy as np


def test_find_duplicates_needs_two_texts():
    from app.core.store import find_duplicates
    with patch("app.core.store._embed") as mock_embed:
        mock_embed.return_value = np.array([[1.0, 0.0], [0.0, 1.0]], dtype="float32")
        result = find_duplicates(["hello", "world"], threshold=0.5)
        assert isinstance(result, list)


def test_find_duplicates_identical():
    from app.core.store import find_duplicates
    with patch("app.core.store._embed") as mock_embed:
        # Identical vectors → similarity = 1.0
        mock_embed.return_value = np.array([[1.0, 0.0], [1.0, 0.0]], dtype="float32")
        result = find_duplicates(["same text", "same text"], threshold=0.9)
        assert len(result) == 1
        assert result[0]["similarity"] == pytest.approx(1.0, abs=0.01)


def test_clear_index():
    from app.core.store import clear_index, get_stats
    clear_index()
    stats = get_stats()
    assert stats["total_documents"] == 0
    assert stats["index_size"] == 0
