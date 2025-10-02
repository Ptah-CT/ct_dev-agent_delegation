"""HTTP Client wrapper for consistent request handling."""

from typing import Any, Dict, Optional
import httpx

from .constants import DEFAULT_HTTP_TIMEOUT, OPENCODE_API_BASE_URL


class HTTPClientWrapper:
    """Wrapper for HTTP requests with consistent error handling and timeouts."""
    
    def __init__(self, base_url: str = OPENCODE_API_BASE_URL, timeout: float = DEFAULT_HTTP_TIMEOUT):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
    
    async def make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request with consistent error handling."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers)
                elif method.upper() == "POST":
                    response = await client.post(url, json=data, headers=headers)
                elif method.upper() == "PUT":
                    response = await client.put(url, json=data, headers=headers)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                return response.json()
                
        except httpx.TimeoutException:
            raise Exception(f"Request timeout after {self.timeout}s")
        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP error {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            raise Exception(f"Request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error: {str(e)}")
    
    async def get(self, endpoint: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Make GET request."""
        return await self.make_request("GET", endpoint, headers=headers)
    
    async def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Make POST request."""
        return await self.make_request("POST", endpoint, data=data, headers=headers)
    
    async def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Make PUT request."""
        return await self.make_request("PUT", endpoint, data=data, headers=headers)
    
    async def delete(self, endpoint: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Make DELETE request."""
        return await self.make_request("DELETE", endpoint, headers=headers)


# Global instance for OpenCode API
opencode_client = HTTPClientWrapper()
