"""
Storage API endpoints - Manage browser storage (localStorage and sessionStorage).

This module provides HTTP API endpoints for storage management:
- GET /api/storage?type=local|session|all - List all storage items
- GET /api/storage/{key}?type=local|session - Get a specific item by key
- POST /api/storage - Set a storage item
- DELETE /api/storage/{key}?type=local|session - Delete a specific item
- DELETE /api/storage?type=local|session|all - Clear all items
"""

from __future__ import annotations

import json
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from zen.app.api.models import CommandResponse
from zen.services.bridge_executor import get_executor
from zen.services.script_loader import ScriptLoader

router = APIRouter()


# Request Models
class SetStorageRequest(BaseModel):
    """Request model for setting storage items."""

    key: str = Field(..., description="Storage key")
    value: str = Field(..., description="Storage value")
    type: Literal["local", "session"] = Field("local", description="Storage type (default: local)")


# Response Models
class StorageListResponse(BaseModel):
    """Response model for listing storage items."""

    ok: bool = Field(..., description="Whether the command executed successfully")
    result: dict[str, Any] | None = Field(None, description="Storage data")
    error: str | None = Field(None, description="Error message if ok=False")


class StorageGetResponse(BaseModel):
    """Response model for getting a specific storage item."""

    ok: bool = Field(..., description="Whether the command executed successfully")
    result: dict[str, Any] | None = Field(None, description="Storage item data")
    error: str | None = Field(None, description="Error message if ok=False")


# Helper Function
def _execute_storage_action(
    storage_type: str,
    action: str,
    key: str = "",
    value: str = "",
) -> dict[str, Any]:
    """Helper function to execute storage actions."""
    executor = get_executor()
    loader = ScriptLoader()

    # Determine script name based on storage type
    script_name = "localStorage.js" if storage_type == "local" else "sessionStorage.js"

    # Load the storage script
    try:
        script = loader.load_script_sync(script_name)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"Script not found: {str(e)}")

    # Replace placeholders
    code = script.replace("ACTION_PLACEHOLDER", action)
    code = code.replace("KEY_PLACEHOLDER", key)
    code = code.replace("VALUE_PLACEHOLDER", value)

    result = executor.execute(code, timeout=60.0)

    if not result.get("ok"):
        raise HTTPException(status_code=500, detail=result.get("error"))

    response = result.get("result", {})

    if not response.get("ok"):
        raise HTTPException(status_code=400, detail=response.get("error"))

    return response


# Endpoints
@router.get("", response_model=StorageListResponse)
@router.get("/", response_model=StorageListResponse)
async def list_storage(
    type: Literal["local", "session", "all"] = Query("all", description="Storage type to list")
):
    """
    List all storage items.

    Mirrors 'inspekt storage list --json' CLI command.

    Query Parameters:
        type: Storage type - "local", "session", or "all" (default: all)

    Returns:
        Dictionary of storage keys and values, plus total count.

    Example responses:
    ```json
    // For type=local
    {
        "ok": true,
        "result": {
            "items": {
                "user_token": "abc123",
                "preferences": "{\"theme\":\"dark\"}"
            },
            "count": 2,
            "storageType": "localStorage"
        }
    }

    // For type=all
    {
        "ok": true,
        "result": {
            "localStorage": {...},
            "localStorageCount": 2,
            "sessionStorage": {...},
            "sessionStorageCount": 1
        }
    }
    ```
    """
    try:
        if type == "all":
            # List both types
            local_result = _execute_storage_action("local", "list")
            session_result = _execute_storage_action("session", "list")

            return {
                "ok": True,
                "result": {
                    "localStorage": local_result.get("items", {}),
                    "localStorageCount": local_result.get("count", 0),
                    "sessionStorage": session_result.get("items", {}),
                    "sessionStorageCount": session_result.get("count", 0),
                },
                "error": None,
            }
        else:
            response = _execute_storage_action(type, "list")
            return {
                "ok": True,
                "result": response,
                "error": None,
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{key}", response_model=StorageGetResponse)
async def get_storage(
    key: str,
    type: Literal["local", "session"] = Query("local", description="Storage type")
):
    """
    Get the value of a specific storage item.

    Mirrors 'inspekt storage get <key> --json' CLI command.

    Path Parameters:
        key: Storage key to retrieve

    Query Parameters:
        type: Storage type - "local" or "session" (default: local)

    Returns:
        Storage key, value, and whether it exists.

    Example response:
    ```json
    {
        "ok": true,
        "result": {
            "key": "user_token",
            "value": "abc123",
            "exists": true,
            "storageType": "localStorage"
        }
    }
    ```
    """
    try:
        response = _execute_storage_action(type, "get", key=key)

        # If item doesn't exist, return 404
        if not response.get("exists"):
            storage_name = "localStorage" if type == "local" else "sessionStorage"
            raise HTTPException(status_code=404, detail=f"Key not found in {storage_name}: {key}")

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
async def set_storage(request: SetStorageRequest):
    """
    Set a storage item.

    Mirrors 'inspekt storage set' CLI command.

    Request Body:
        key: Storage key
        value: Storage value
        type: Storage type - "local" or "session" (default: local)

    Examples:
        - Basic item: `{"key": "user_token", "value": "abc123"}`
        - Session storage: `{"key": "temp_data", "value": "xyz", "type": "session"}`
        - JSON value: `{"key": "preferences", "value": "{\"theme\":\"dark\"}", "type": "local"}`

    Returns:
        Confirmation of set operation.

    Example response:
    ```json
    {
        "ok": true,
        "result": {
            "key": "user_token",
            "value": "abc123",
            "storageType": "localStorage"
        }
    }
    ```
    """
    try:
        response = _execute_storage_action(
            request.type, "set", key=request.key, value=request.value
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


@router.delete("/{key}", response_model=CommandResponse)
async def delete_storage(
    key: str,
    type: Literal["local", "session"] = Query("local", description="Storage type")
):
    """
    Delete a specific storage item.

    Mirrors 'inspekt storage delete <key>' CLI command.

    Path Parameters:
        key: Storage key to delete

    Query Parameters:
        type: Storage type - "local" or "session" (default: local)

    Example:
        DELETE /api/storage/user_token?type=local

    Returns:
        Confirmation of deletion.

    Example response:
    ```json
    {
        "ok": true,
        "result": {
            "key": "user_token",
            "storageType": "localStorage"
        }
    }
    ```
    """
    try:
        response = _execute_storage_action(type, "delete", key=key)

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
async def clear_storage(
    type: Literal["local", "session", "all"] = Query("all", description="Storage type to clear")
):
    """
    Clear all storage items.

    Mirrors 'inspekt storage clear' CLI command.

    Query Parameters:
        type: Storage type - "local", "session", or "all" (default: all)

    Examples:
        - DELETE /api/storage?type=local
        - DELETE /api/storage?type=session
        - DELETE /api/storage?type=all

    Returns:
        Number of items deleted.

    Example responses:
    ```json
    // For type=local
    {
        "ok": true,
        "result": {
            "deleted": 5,
            "storageType": "localStorage"
        }
    }

    // For type=all
    {
        "ok": true,
        "result": {
            "localStorageDeleted": 5,
            "sessionStorageDeleted": 2
        }
    }
    ```
    """
    try:
        if type == "all":
            # Clear both types
            local_result = _execute_storage_action("local", "clear")
            session_result = _execute_storage_action("session", "clear")

            return {
                "ok": True,
                "result": {
                    "localStorageDeleted": local_result.get("deleted", 0),
                    "sessionStorageDeleted": session_result.get("deleted", 0),
                },
                "error": None,
            }
        else:
            response = _execute_storage_action(type, "clear")

            return {
                "ok": True,
                "result": response,
                "error": None,
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
