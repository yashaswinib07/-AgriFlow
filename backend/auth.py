import hashlib
import hmac
import os
import json
import base64
import time
import sqlite3
from typing import Optional, Dict, Any
from fastapi import Header, HTTPException, Depends, status
from database import get_db

# Secret key for HMAC token signing
SECRET_KEY = os.getenv("AGRIFLOW_SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError("AGRIFLOW_SECRET_KEY is not configured")
TOKEN_EXPIRY_SECONDS = 7 * 24 * 60 * 60  # 7 days


def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256 with a unique random salt."""
    salt = os.urandom(16).hex()
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()
    return f"{salt}${key}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against the stored salt$hash string."""
    try:
        salt, expected_hash = hashed_password.split("$")
        computed_hash = hashlib.pbkdf2_hmac(
            'sha256',
            plain_password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()
        return hmac.compare_digest(computed_hash, expected_hash)
    except Exception:
        return False


def create_access_token(payload: Dict[str, Any]) -> str:
    """Create a tamper-proof signed token with expiration timestamp."""
    token_data = payload.copy()
    token_data["exp"] = int(time.time()) + TOKEN_EXPIRY_SECONDS
    raw_json = json.dumps(token_data, separators=(',', ':')).encode('utf-8')
    encoded_payload = base64.urlsafe_b64encode(raw_json).decode('utf-8')
    
    # Calculate HMAC-SHA256 signature
    signature = hmac.new(
        SECRET_KEY.encode('utf-8'),
        encoded_payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return f"{encoded_payload}.{signature}"


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify token validity and signature."""
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        encoded_payload, signature = parts
        
        # Verify signature
        expected_sig = hmac.new(
            SECRET_KEY.encode('utf-8'),
            encoded_payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            return None
        
        # Decode payload
        raw_json = base64.urlsafe_b64decode(encoded_payload.encode('utf-8')).decode('utf-8')
        data = json.loads(raw_json)
        
        # Check expiration
        if data.get("exp", 0) < int(time.time()):
            return None
        return data
    except Exception:
        return None


def get_current_user_payload(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Extract and validate the authorization token from the request header."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is missing",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = authorization
    if token.startswith("Bearer "):
        token = token[7:].strip()
        
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return payload


def get_current_farmer(
    payload: Dict[str, Any] = Depends(get_current_user_payload),
    conn: sqlite3.Connection = Depends(get_db)
) -> dict:
    """Dependency ensuring request is from an authenticated farmer."""
    if payload.get("role") != "farmer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to registered farmers"
        )
    row = conn.execute("SELECT * FROM farmers WHERE id = ?", (payload.get("sub"),)).fetchone()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farmer account not found"
        )
    return dict(row)


def get_current_buyer(
    payload: Dict[str, Any] = Depends(get_current_user_payload),
    conn: sqlite3.Connection = Depends(get_db)
) -> dict:
    """Dependency ensuring request is from an authenticated buyer."""
    if payload.get("role") != "buyer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to registered buyers"
        )
    row = conn.execute("SELECT * FROM buyers WHERE id = ?", (payload.get("sub"),)).fetchone()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Buyer account not found"
        )
    return dict(row)
