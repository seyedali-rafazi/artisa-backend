"""Unit and schema tests for Contact Messages functionality."""

import sys
import unittest
from datetime import datetime
from pathlib import Path
from bson import ObjectId
from pydantic import ValidationError

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from models.contact_message import ContactMessage
from schemas.contact_message import (
    ContactMessageCreate,
    ContactMessageResponse,
    ContactMessageStatusUpdate,
    PaginatedContactMessagesResponse,
)
from api.v1.contact_messages import serialize_contact_message


class TestContactMessageSchemas(unittest.TestCase):
    """Test validation and serialization of Contact Message schemas."""

    def test_contact_message_create_success(self):
        """Valid payload creates ContactMessageCreate schema successfully."""
        req = ContactMessageCreate(
            name="   سارا رضایی   ",
            email="  SARA.REZAEI@GMAIL.COM  ",
            message="   سلام، می‌خواستم درباره نحوه ارسال سفارش به شیراز سوال کنم.   ",
        )
        self.assertEqual(req.name, "سارا رضایی")
        self.assertEqual(req.email, "sara.rezaei@gmail.com")
        self.assertEqual(req.message, "سلام، می‌خواستم درباره نحوه ارسال سفارش به شیراز سوال کنم.")

    def test_contact_message_invalid_email(self):
        """Invalid email formats raise ValidationError."""
        invalid_emails = [
            "plainaddress",
            "@missingusername.com",
            "username@.com",
            "username@com",
            "",
        ]
        for bad_email in invalid_emails:
            with self.subTest(bad_email=bad_email):
                with self.assertRaises(ValidationError):
                    ContactMessageCreate(
                        name="علی کریمی",
                        email=bad_email,
                        message="سلام و وقت بخیر خدمت تیم پشتیبانی",
                    )

    def test_contact_message_name_too_short(self):
        """Name shorter than 2 characters raises ValidationError."""
        with self.assertRaises(ValidationError):
            ContactMessageCreate(
                name="a",
                email="user@example.com",
                message="سلام و خسته نباشید",
            )

        with self.assertRaises(ValidationError):
            ContactMessageCreate(
                name="   ",
                email="user@example.com",
                message="سلام و خسته نباشید",
            )

    def test_contact_message_message_too_short(self):
        """Message shorter than 5 characters raises ValidationError."""
        with self.assertRaises(ValidationError):
            ContactMessageCreate(
                name="کاربر محترم",
                email="user@example.com",
                message="سلام",
            )

    def test_status_update_validation(self):
        """Status update accepts 'unread' and 'read', but rejects invalid status."""
        valid_unread = ContactMessageStatusUpdate(status="unread")
        self.assertEqual(valid_unread.status, "unread")

        valid_read = ContactMessageStatusUpdate(status="read")
        self.assertEqual(valid_read.status, "read")

        with self.assertRaises(ValidationError):
            ContactMessageStatusUpdate(status="archived")

        with self.assertRaises(ValidationError):
            ContactMessageStatusUpdate(status="pending")

    def test_serialize_contact_message(self):
        """serialize_contact_message converts Beanie document into clean response dictionary."""
        from unittest.mock import MagicMock
        mock_msg = MagicMock()
        mock_msg.id = ObjectId()
        mock_msg.name = "مهرداد نادری"
        mock_msg.email = "mehrdad@example.com"
        mock_msg.message = "درخواست خرید عمده برای گالری تهران"
        mock_msg.status = "unread"
        mock_msg.created_at = datetime.utcnow()
        mock_msg.updated_at = datetime.utcnow()

        serialized = serialize_contact_message(mock_msg)
        self.assertEqual(serialized.id, str(mock_msg.id))
        self.assertEqual(serialized.name, "مهرداد نادری")
        self.assertEqual(serialized.email, "mehrdad@example.com")
        self.assertEqual(serialized.message, "درخواست خرید عمده برای گالری تهران")
        self.assertEqual(serialized.status, "unread")

    def test_paginated_response_schema(self):
        """Paginated response properly holds list of items and meta counters."""
        res = PaginatedContactMessagesResponse(
            items=[
                ContactMessageResponse(
                    id="65f123456789abcdef012345",
                    name="تست",
                    email="test@example.com",
                    message="پیام آزمایشی برای تست سیستم",
                    status="unread",
                )
            ],
            total=1,
            page=1,
            limit=10,
            total_pages=1,
            unread_count=1,
        )
        self.assertEqual(len(res.items), 1)
        self.assertEqual(res.total, 1)
        self.assertEqual(res.unread_count, 1)


if __name__ == "__main__":
    unittest.main()
