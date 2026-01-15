# mypy: ignore-errors
from typing import Any, Dict

from drf_spectacular.extensions import OpenApiAuthenticationExtension


class CustomSimpleJWTScheme(OpenApiAuthenticationExtension):
    target_class = "apps.core.authentication.ActiveUserJWTAuthentication"
    name = "BearerAuth"

    def get_security_definition(self, auto_schema) -> Dict[str, Any]:
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
