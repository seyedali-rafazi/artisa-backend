"""Audit Log Document Model."""

from datetime import datetime
from typing import Dict, Any, Optional
from beanie import Document, Indexed
from pydantic import Field


class AuditLog(Document):
    """Audit Log model for tracking sensitive admin actions."""

    user_id: Indexed(str)  # type: ignore
    user_email: Indexed(str)  # type: ignore
    user_role: str = "customer"
    action: Indexed(str)  # type: ignore e.g. "CREATE_PRODUCT", "UPDATE_ORDER", "CHANGE_ROLE"
    resource: str  # e.g. "product_65432", "user_9876", "order_ORD-1002"
    details: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "audit_logs"

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "6581f...",
                "user_email": "admin@example.com",
                "user_role": "admin",
                "action": "UPDATE_ORDER_STATUS",
                "resource": "order_ORD-10042",
                "details": {"previous_status": "pending", "new_status": "shipped"},
            }
        }
