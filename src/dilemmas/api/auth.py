"""API authentication middleware."""

import os
from fastapi import Header, HTTPException, status


async def verify_api_key(x_api_key: str = Header(..., description="API key for authentication")):
    """Verify API key from header.

    Args:
        x_api_key: API key from X-API-Key header

    Raises:
        HTTPException: If API key is invalid or missing

    Usage:
        @app.get("/protected", dependencies=[Depends(verify_api_key)])
        async def protected_endpoint():
            return {"message": "Authorized"}
    """
    expected_key = os.getenv("API_KEY")

    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API_KEY environment variable not configured on server"
        )

    if x_api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
