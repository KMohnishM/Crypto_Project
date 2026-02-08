"""
JWT Authentication Client for Service-to-Service Communication
Lightweight client without Flask dependencies - for non-Flask services
"""

import os
import jwt
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# Configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-jwt-secret-change-in-production-use-256-bit-key')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24


def generate_service_token(service_name: str) -> str:
    """
    Generate JWT token for a service.
    
    Args:
        service_name: Name of the service requesting authentication
        
    Returns:
        JWT token string
    """
    payload = {
        'service': service_name,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


class ServiceAuthClient:
    """
    HTTP client that automatically includes JWT authentication in requests.
    For use in non-Flask services that need to make authenticated requests.
    """
    
    def __init__(self, service_name: str):
        """
        Initialize authenticated client.
        
        Args:
            service_name: Name of this service for JWT claims
        """
        self.service_name = service_name
        self.token = generate_service_token(service_name)
        self.headers = {
            'Authorization': f'Bearer {self.token}'
        }
    
    def _merge_headers(self, custom_headers: Optional[Dict] = None) -> Dict:
        """Merge custom headers with authentication header."""
        headers = self.headers.copy()
        if custom_headers:
            headers.update(custom_headers)
        return headers
    
    def get(self, url: str, headers: Optional[Dict] = None, **kwargs) -> requests.Response:
        """Make authenticated GET request."""
        return requests.get(url, headers=self._merge_headers(headers), **kwargs)
    
    def post(self, url: str, headers: Optional[Dict] = None, **kwargs) -> requests.Response:
        """Make authenticated POST request."""
        return requests.post(url, headers=self._merge_headers(headers), **kwargs)
    
    def put(self, url: str, headers: Optional[Dict] = None, **kwargs) -> requests.Response:
        """Make authenticated PUT request."""
        return requests.put(url, headers=self._merge_headers(headers), **kwargs)
    
    def delete(self, url: str, headers: Optional[Dict] = None, **kwargs) -> requests.Response:
        """Make authenticated DELETE request."""
        return requests.delete(url, headers=self._merge_headers(headers), **kwargs)
