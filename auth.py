from fastapi import Header, HTTPException, status
import os
import secrets

def generate_token():
    return secrets.token_hex(32)  # Random secure token

API_TOKEN = os.getenv("API_TOKEN")
if not API_TOKEN:
    API_TOKEN = generate_token()
    print(f"--- AUTO-GENERATED API_TOKEN: {API_TOKEN} ---")

def verify_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing"
        )

    try:
        scheme, token = authorization.split()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization format"
        )

    if scheme.lower() != "bearer" or token != API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token"
        )
