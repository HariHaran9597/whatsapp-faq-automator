# backend/security.py

from fastapi import Depends, HTTPException, status, Header
from typing import Optional
from backend.config import settings
from backend.logging_config import get_logger

logger = get_logger(__name__)

async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    """
    Verify that the provided API key is valid.
    
    This dependency can be used on endpoints that require authentication.
    
    Args:
        x_api_key: The API key from the X-API-Key header
        
    Returns:
        The API key if valid
        
    Raises:
        HTTPException: If API key is missing or invalid
        
    Example:
        @app.post("/protected")
        async def protected_endpoint(api_key: str = Depends(verify_api_key)):
            return {"message": "This is protected"}
    """
    
    # If no API key is configured, disable authentication
    if not settings.API_KEY:
        logger.debug("API authentication is disabled (no API_KEY configured)")
        return "disabled"
    
    # If no API key provided in request
    if not x_api_key:
        logger.warning("Request to protected endpoint without API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Validate API key
    if x_api_key != settings.API_KEY:
        logger.warning(f"Request with invalid API key attempted")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )
    
    logger.debug("API key validated successfully")
    return x_api_key

async def optional_verify_api_key(x_api_key: Optional[str] = Header(None)) -> Optional[str]:
    """
    Optional API key verification. Used for endpoints where authentication is optional.
    
    If API_KEY is configured in environment, validates the provided key.
    Otherwise, allows access without a key.
    
    Args:
        x_api_key: The API key from the X-API-Key header
        
    Returns:
        The API key if provided and valid, None otherwise
        
    Raises:
        HTTPException: Only if API_KEY is configured and provided key is invalid
    """
    
    # If API authentication is disabled, allow access
    if not settings.API_KEY:
        return None
    
    # If API key is configured but none provided, that's OK (optional)
    if not x_api_key:
        return None
    
    # Validate the provided API key
    if x_api_key != settings.API_KEY:
        logger.warning("Request with invalid API key attempted (optional endpoint)")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )
    
    return x_api_key
