import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from data.kiwoom_rest_client import KiwoomRestClient

@pytest.fixture
def client():
    client = KiwoomRestClient()
    # Disable mock mode for unit tests to test real logic (with mocks)
    client.is_mock_server = False 
    client.offline_mode = False
    client.base_url = "https://api.kiwoom.com"
    return client

@pytest.mark.asyncio
async def test_get_token_success(client):
    """Test successful token issuance."""
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
        "access_token": "test_token",
        "expires_in": 3600
    })
    mock_response.__aenter__.return_value = mock_response
    mock_response.__aexit__.return_value = None
    
    # Mock key_manager
    with patch('data.key_manager.key_manager.get_active_key') as mock_get_key, \
         patch('aiohttp.ClientSession.post', return_value=mock_response) as mock_post:
        
        mock_get_key.return_value = {
            "app_key": "app_key",
            "secret_key": "secret_key",
            "type": "REAL"
        }
        
        token = await client.get_token()
        assert token == "test_token"
        assert client.access_token == "test_token"

@pytest.mark.asyncio
async def test_request_success(client):
    """Test successful API request."""
    client.access_token = "valid_token"
    
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"result": "ok"})
    mock_response.__aenter__.return_value = mock_response
    mock_response.__aexit__.return_value = None
    
    with patch('aiohttp.ClientSession.request', return_value=mock_response) as mock_req, \
         patch('data.rate_limiter.RateLimiter.acquire', new_callable=AsyncMock):
        
        result = await client.request("GET", "/test/endpoint")
        assert result == {"result": "ok"}
        
        # Verify headers
        args, kwargs = mock_req.call_args
        assert kwargs['headers']['Authorization'] == "Bearer valid_token"

@pytest.mark.asyncio
async def test_request_401_retry(client):
    """Test token refresh and retry on 401."""
    client.access_token = "expired_token"
    
    # First response 401
    mock_response_401 = MagicMock()
    mock_response_401.status = 401
    mock_response_401.text = AsyncMock(return_value="Unauthorized")
    mock_response_401.__aenter__.return_value = mock_response_401
    mock_response_401.__aexit__.return_value = None
    
    # Second response 200
    mock_response_200 = MagicMock()
    mock_response_200.status = 200
    mock_response_200.json = AsyncMock(return_value={"result": "success"})
    mock_response_200.__aenter__.return_value = mock_response_200
    mock_response_200.__aexit__.return_value = None
    
    # Mock get_token to return new token
    client.get_token = AsyncMock(return_value="new_token")
    
    with patch('aiohttp.ClientSession.request', side_effect=[mock_response_401, mock_response_200]) as mock_req, \
         patch('data.rate_limiter.RateLimiter.acquire', new_callable=AsyncMock):
        
        result = await client.request("GET", "/test/endpoint")
        
        assert result == {"result": "success"}
        assert client.get_token.called
        assert mock_req.call_count == 2
        
        # Check headers of second call
        args, kwargs = mock_req.call_args_list[1]
        assert kwargs['headers']['Authorization'] == "Bearer new_token"

@pytest.mark.asyncio
async def test_request_rate_limiting(client):
    """Verify rate limiter is acquired."""
    client.access_token = "token"
    
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={})
    mock_response.__aenter__.return_value = mock_response
    mock_response.__aexit__.return_value = None
    
    with patch('aiohttp.ClientSession.request', return_value=mock_response), \
         patch('data.rate_limiter.RateLimiter.acquire', new_callable=AsyncMock) as mock_acquire:
        
        await client.request("GET", "/test")
        mock_acquire.assert_called_once()

@pytest.mark.asyncio
async def test_get_ohlcv(client):
    # Mock Response
    mock_response = {
        "output": [
            {"date": "20230101", "open": "60000", "high": "61000", "low": "59000", "close": "60500", "volume": "100000"}
        ]
    }
    
    with patch.object(client, 'request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response
        
        result = await client.get_ohlcv("005930", "day", "20230101")
        
        assert result == mock_response
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert args[0] == "POST"
        assert "/api/dostk/ohlcv_day" in args[1]
        assert kwargs['data']['stk_cd'] == "005930"
        assert kwargs['api_id'] == "opt10081"

@pytest.mark.asyncio
async def test_get_code_list(client):
    # Mock Response
    mock_response = ["005930", "000660"]
    
    with patch.object(client, 'request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response
        
        result = await client.get_code_list("0")
        
        assert result == mock_response
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert kwargs['api_id'] == "GetCodeListByMarket"

@pytest.mark.asyncio
async def test_get_account_balance(client):
    # Mock Response
    mock_response = {
        "output": {
            "single": [{"deposit": "10000000"}],
            "multi": []
        }
    }
    
    with patch.object(client, 'request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response
        
        result = await client.get_account_balance()
        
        assert result == mock_response
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert kwargs['api_id'] == "opw00018"
