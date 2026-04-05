from fastapi import APIRouter, Depends, Request
from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute

from src.dependencies import get_current_user, require_admin

router = APIRouter()


@router.get("/openapi.json")
async def get_playground_openapi(
    request: Request, current_user=Depends(get_current_user)
):
    """
    Get the OpenAPI schema for the playground.
    Excludes Auth, API Keys, and Admin-only routes.
    """
    filtered_routes = []
    excluded_tags = {"Auth", "API Keys", "Feedback"}
    
    # Define (path, method) pairs to exclude
    excluded_endpoints = {
        ("/api/users", "GET"),
        ("/api/users/signup", "POST"),
        ("/api/users/profile-picture", "POST"),
    }


    for route in request.app.routes:
        if isinstance(route, APIRoute):
            # 1. Filter by specific endpoints
            method = list(route.methods)[0] if route.methods else "GET"
            if (route.path, method) in excluded_endpoints:
                continue

            # 2. Filter by tags
            if any(tag in excluded_tags for tag in (route.tags or [])):
                continue

            # 3. Filter by require_admin dependency
            is_admin_only = False
            
            # Check route level dependencies
            for dep in route.dependencies:
                if dep.dependency == require_admin:
                    is_admin_only = True
                    break
            
            # Check function signature dependencies (if any)
            if not is_admin_only and hasattr(route, "dependant"):
                for dep in route.dependant.dependencies:
                    if dep.call == require_admin:
                        is_admin_only = True
                        break

            
            if is_admin_only:
                continue

            filtered_routes.append(route)


    return get_openapi(
        title="MyPage48 Public API Playground",
        version=request.app.version,
        routes=filtered_routes,
    )


