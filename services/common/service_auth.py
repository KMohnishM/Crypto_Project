"""
JWT-based Service-to-Service Authentication
Protects internal API endpoints (Backend ↔ ML Service)
"""

import jwt
import datetime
import os
from functools import wraps
from flask import request, jsonify

# Service secret key (should be in environment variable in production)
SECRET_KEY = os.getenv('JWT_SECRET_KEY', os.getenv('SERVICE_SECRET_KEY', 'dev-secret-change-in-production'))
ALGORITHM = 'HS256'
TOKEN_EXPIRY_HOURS = int(os.getenv('JWT_EXPIRY_HOURS', '24'))


def generate_service_token(service_name: str, expiry_hours: int = TOKEN_EXPIRY_HOURS) -> str:
    """
    Generate JWT token for service-to-service authentication
    
    Args:
        service_name: Identifier of the calling service (e.g., 'main_host', 'web_dashboard')
        expiry_hours: Token validity period in hours
    
    Returns:
        JWT token string
    
    Example:
        token = generate_service_token('main_host')
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.post(ML_SERVICE_URL, json=data, headers=headers)
    """
    payload = {
        'service': service_name,
        'iat': datetime.datetime.utcnow(),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=expiry_hours)
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


def verify_service_token(token: str) -> dict:
    """
    Verify and decode JWT token
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded payload dictionary
    
    Raises:
        jwt.ExpiredSignatureError: Token has expired
        jwt.InvalidTokenError: Token is invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")


def require_service_auth(f):
    """
    Flask decorator to protect endpoints with JWT authentication
    
    Usage:
        @app.route("/predict", methods=["POST"])
        @require_service_auth
        def predict():
            service_name = request.service_name
            # ... endpoint logic
    
    The decorator adds 'service_name' to the request object
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({
                'error': 'No authorization token provided',
                'message': 'Include Authorization: Bearer <token> header'
            }), 401
        
        # Extract token (format: "Bearer <token>")
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({
                'error': 'Invalid authorization header',
                'message': 'Format: Authorization: Bearer <token>'
            }), 401
        
        token = parts[1]
        
        # Verify token
        try:
            payload = verify_service_token(token)
            request.service_name = payload['service']
            request.token_payload = payload
            request.authenticated = True  # Mark request as authenticated
            
        except ValueError as e:
            return jsonify({
                'error': 'Authentication failed',
                'message': str(e)
            }), 401
        
        return f(*args, **kwargs)
    
    return decorated


def optional_service_auth(f):
    """
    Flask decorator for optional authentication
    If token present and valid, adds service_name to request
    If token absent or invalid, continues without authentication
    
    Useful for endpoints that work in both authenticated and unauthenticated modes
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            try:
                parts = auth_header.split()
                if len(parts) == 2 and parts[0].lower() == 'bearer':
                    payload = verify_service_token(parts[1])
                    request.service_name = payload['service']
                    request.authenticated = True
                else:
                    request.authenticated = False
            except:
                request.authenticated = False
        else:
            request.authenticated = False
        
        return f(*args, **kwargs)
    
    return decorated


class ServiceAuthClient:
    """
    Client helper for making authenticated requests to other services
    
    Usage:
        client = ServiceAuthClient('main_host')
        response = client.post('http://ml_service:6000/predict', json=data)
    """
    
    def __init__(self, service_name: str):
        """
        Initialize authenticated client
        
        Args:
            service_name: Name of this service (e.g., 'main_host')
        """
        self.service_name = service_name
        self.token = generate_service_token(service_name)
    
    def get_headers(self) -> dict:
        """Get authentication headers"""
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
    
    def refresh_token(self):
        """Refresh the JWT token"""
        self.token = generate_service_token(self.service_name)
    
    def post(self, url: str, json: dict, **kwargs):
        """Make authenticated POST request"""
        import requests
        headers = self.get_headers()
        return requests.post(url, json=json, headers=headers, **kwargs)
    
    def get(self, url: str, **kwargs):
        """Make authenticated GET request"""
        import requests
        headers = self.get_headers()
        return requests.get(url, headers=headers, **kwargs)


# Example usage and testing
if __name__ == "__main__":
    print("🧪 Testing Service Authentication...")
    
    # Generate token
    token = generate_service_token('main_host')
    print(f"Generated token: {token[:50]}...")
    
    # Verify token
    try:
        payload = verify_service_token(token)
        print(f"✅ Token verified: {payload}")
    except ValueError as e:
        print(f"❌ Verification failed: {e}")
    
    # Test expired token
    import time
    old_expiry = TOKEN_EXPIRY_HOURS
    TOKEN_EXPIRY_HOURS = -1  # Make it expire immediately
    expired_token = generate_service_token('test')
    TOKEN_EXPIRY_HOURS = old_expiry
    
    time.sleep(1)
    try:
        verify_service_token(expired_token)
        print("❌ Expired token should have failed")
    except ValueError as e:
        print(f"✅ Expired token rejected: {e}")
    
    # Test client
    client = ServiceAuthClient('test_service')
    headers = client.get_headers()
    print(f"✅ Client headers: {headers}")
    
    print("\n✅ All service auth tests passed!")
