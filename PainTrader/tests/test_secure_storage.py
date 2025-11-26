import pytest
import keyring
from unittest.mock import patch, MagicMock
from core.secure_storage import SecureStorage

@pytest.fixture
def secure_storage():
    return SecureStorage()

def test_save_success(secure_storage):
    """Test successful save operation."""
    with patch('keyring.set_password') as mock_set:
        secure_storage.save("test_key", "test_value")
        mock_set.assert_called_once_with("PainTrader", "test_key", "test_value")

def test_save_failure(secure_storage):
    """Test save failure raises exception."""
    with patch('keyring.set_password', side_effect=Exception("Keyring error")):
        with pytest.raises(Exception, match="Keyring error"):
            secure_storage.save("test_key", "test_value")

def test_get_success(secure_storage):
    """Test successful retrieval."""
    with patch('keyring.get_password', return_value="test_value") as mock_get:
        val = secure_storage.get("test_key")
        assert val == "test_value"
        mock_get.assert_called_once_with("PainTrader", "test_key")

def test_get_not_found(secure_storage):
    """Test retrieval when key not found."""
    with patch('keyring.get_password', return_value=None):
        val = secure_storage.get("non_existent_key")
        assert val is None

def test_get_failure(secure_storage):
    """Test retrieval failure returns None (graceful degradation)."""
    with patch('keyring.get_password', side_effect=Exception("Keyring error")):
        val = secure_storage.get("test_key")
        assert val is None

def test_delete_success(secure_storage):
    """Test successful deletion."""
    with patch('keyring.delete_password') as mock_delete:
        secure_storage.delete("test_key")
        mock_delete.assert_called_once_with("PainTrader", "test_key")

def test_delete_failure(secure_storage):
    """Test deletion failure (should log error but not raise)."""
    with patch('keyring.delete_password', side_effect=Exception("Keyring error")):
        # Should not raise
        secure_storage.delete("test_key")
