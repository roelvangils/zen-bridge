"""
Cookies API endpoints - Manage browser cookies.

This module provides HTTP API endpoints for cookie management:
- GET /api/cookies - List all cookies for the current page
- GET /api/cookies/{name} - Get a specific cookie by name
- POST /api/cookies - Set a cookie with various options
- DELETE /api/cookies/{name} - Delete a specific cookie
- DELETE /api/cookies - Clear all cookies
"""

from __future__ import annotations

import json
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from inspekt.app.api.dependencies import get_bridge_client
from inspekt.app.api.models import CommandResponse
from inspekt.services.bridge_executor import get_executor
from inspekt.services.script_loader import ScriptLoader

router = APIRouter()


# Request Models
class SetCookieRequest(BaseModel):
    """Request model for setting cookies."""

    name: str = Field(..., description="Cookie name")
    value: str = Field(..., description="Cookie value")
    max_age: int | None = Field(None, description="Max age in seconds")
    expires: str | None = Field(
        None, description="Expiration date (e.g., 'Wed, 21 Oct 2025 07:28:00 GMT')"
    )
    path: str = Field("/", description="Cookie path")
    domain: str | None = Field(None, description="Cookie domain")
    secure: bool = Field(False, description="Secure flag (HTTPS only)")
    same_site: Literal["Strict", "Lax", "None"] | None = Field(None, description="SameSite attribute")


# Response Models
class CookiesListResponse(BaseModel):
    """Response model for listing cookies."""

    ok: bool = Field(..., description="Whether the command executed successfully")
    result: dict[str, Any] | None = Field(None, description="Cookies data")
    error: str | None = Field(None, description="Error message if ok=False")


class CookieGetResponse(BaseModel):
    """Response model for getting a specific cookie."""

    ok: bool = Field(..., description="Whether the command executed successfully")
    result: dict[str, Any] | None = Field(None, description="Cookie data")
    error: str | None = Field(None, description="Error message if ok=False")


# Helper Function
def _execute_cookie_action(
    action: str,
    cookie_name: str = "",
    cookie_value: str = "",
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Helper function to execute cookie actions."""
    executor = get_executor()
    loader = ScriptLoader()

    # Load the cookies script
    try:
        script = loader.load_script_sync("cookies.js")
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"Script not found: {str(e)}")

    # Replace placeholders
    options_json = json.dumps(options if options else {})
    code = script.replace("ACTION_PLACEHOLDER", action)
    code = code.replace("NAME_PLACEHOLDER", cookie_name)
    code = code.replace("VALUE_PLACEHOLDER", cookie_value)
    code = code.replace("OPTIONS_PLACEHOLDER", options_json)

    result = executor.execute(code, timeout=60.0)

    if not result.get("ok"):
        raise HTTPException(status_code=500, detail=result.get("error"))

    response = result.get("result", {})

    if response.get("error"):
        raise HTTPException(status_code=400, detail=response.get("error"))

    return response


# Endpoints
@router.get("", response_model=CookiesListResponse)
@router.get("/", response_model=CookiesListResponse)
async def list_cookies():
    """
    List all cookies for the current page.

    Mirrors 'zen cookies list --json' CLI command.

    Returns:
        Dictionary of cookie names and values, plus total count.

    Example response:
    ```json
    {
        "ok": true,
        "result": {
            "cookies": {
                "session_id": "abc123",
                "user_pref": "dark"
            },
            "count": 2
        }
    }
    ```
    """
    try:
        response = _execute_cookie_action("list")
        return {
            "ok": True,
            "result": response,
            "error": None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{name}", response_model=CookieGetResponse)
async def get_cookie(name: str):
    """
    Get the value of a specific cookie.

    Mirrors 'zen cookies get <name> --json' CLI command.

    Args:
        name: Cookie name to retrieve

    Returns:
        Cookie name, value, and whether it exists.

    Example response:
    ```json
    {
        "ok": true,
        "result": {
            "name": "session_id",
            "value": "abc123",
            "exists": true
        }
    }
    ```
    """
    try:
        response = _execute_cookie_action("get", cookie_name=name)

        # If cookie doesn't exist, return 404
        if not response.get("exists"):
            raise HTTPException(status_code=404, detail=f"Cookie not found: {name}")

        return {
            "ok": True,
            "result": response,
            "error": None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=CommandResponse)
@router.post("/", response_model=CommandResponse)
async def set_cookie(request: SetCookieRequest):
    """
    Set a cookie with various options.

    Mirrors 'zen cookies set' CLI command.

    Examples:
        - Basic cookie: `{"name": "session_id", "value": "abc123"}`
        - With max age: `{"name": "token", "value": "xyz", "max_age": 3600}`
        - With options: `{"name": "user_pref", "value": "dark", "path": "/", "secure": true}`
        - SameSite: `{"name": "tracking", "value": "123", "same_site": "Lax"}`

    Cookie options:
        - max_age: Lifetime in seconds
        - expires: Expiration date string
        - path: Cookie path (default: "/")
        - domain: Cookie domain
        - secure: HTTPS only
        - same_site: "Strict", "Lax", or "None"
    """
    try:
        options: dict[str, Any] = {"path": request.path}

        if request.max_age is not None:
            options["maxAge"] = request.max_age
        if request.expires:
            options["expires"] = request.expires
        if request.domain:
            options["domain"] = request.domain
        if request.secure:
            options["secure"] = True
        if request.same_site:
            options["sameSite"] = request.same_site

        response = _execute_cookie_action(
            "set", cookie_name=request.name, cookie_value=request.value, options=options
        )

        return {
            "ok": True,
            "result": response,
            "error": None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{name}", response_model=CommandResponse)
async def delete_cookie(name: str):
    """
    Delete a specific cookie.

    Mirrors 'zen cookies delete <name>' CLI command.

    Args:
        name: Cookie name to delete

    Example:
        DELETE /api/cookies/session_id

    Returns:
        Confirmation of deletion.
    """
    try:
        response = _execute_cookie_action("delete", cookie_name=name)

        return {
            "ok": True,
            "result": response,
            "error": None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("", response_model=CommandResponse)
@router.delete("/", response_model=CommandResponse)
async def clear_cookies():
    """
    Clear all cookies for the current page.

    Mirrors 'zen cookies clear' CLI command.

    Deletes all cookies associated with the current domain.

    Returns:
        Number of cookies deleted.

    Example response:
    ```json
    {
        "ok": true,
        "result": {
            "deleted": 5
        }
    }
    ```
    """
    try:
        response = _execute_cookie_action("clear")

        return {
            "ok": True,
            "result": response,
            "error": None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
