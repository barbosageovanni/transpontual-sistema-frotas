# backend_fastapi/app/core/exceptions.py
"""
Exceções customizadas
"""
from typing import Any, Dict, Optional

class TranspontualException(Exception):
    """Exceção base do sistema"""
    def __init__(
        self,
        message: str,
        code: str = "GENERIC_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(TranspontualException):
    """Erro de validação"""
    def __init__(self, message: str, field: str = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details={"field": field} if field else {}
        )

class NotFoundError(TranspontualException):
    """Recurso não encontrado"""
    def __init__(self, resource: str, resource_id: Any = None):
        message = f"{resource} não encontrado"
        if resource_id:
            message += f" (ID: {resource_id})"
        
        super().__init__(
            message=message,
            code="NOT_FOUND",
            details={"resource": resource, "id": resource_id}
        )

class BusinessRuleError(TranspontualException):
    """Violação de regra de negócio"""
    def __init__(self, message: str, rule: str = None):
        super().__init__(
            message=message,
            code="BUSINESS_RULE_VIOLATION",
            details={"rule": rule} if rule else {}
        )
