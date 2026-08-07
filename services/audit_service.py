"""Audit Service for logging administrative and security sensitive events."""

import logging
from typing import Dict, Any, Optional
from fastapi import Request
from models.user import User
from models.audit_log import AuditLog

logger = logging.getLogger(__name__)


class AuditLogService:
    """Service for recording audit logs."""

    @staticmethod
    async def log_action(
        user: User,
        action: str,
        resource: str,
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
    ) -> AuditLog:
        """Create and store an audit log entry."""
        ip_address = None
        user_agent = None

        if request:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")

        log_entry = AuditLog(
            user_id=str(user.id),
            user_email=user.email,
            user_role=user.normalized_role,
            action=action,
            resource=resource,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        try:
            await log_entry.insert()
            logger.info(
                f"[AUDIT] {user.email} ({user.normalized_role}) perform {action} on {resource}"
            )
        except Exception as e:
            logger.error(f"Failed to save audit log: {str(e)}")

        return log_entry
