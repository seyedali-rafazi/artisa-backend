"""Unit and schema tests for Newsletter functionality."""

import sys
import unittest
from datetime import datetime
from pathlib import Path
from bson import ObjectId
from pydantic import ValidationError

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from models.newsletter import NewsletterSubscriber
from schemas.newsletter import (
    NewsletterSubscribeRequest,
    NewsletterSubscriberResponse,
    PaginatedNewsletterSubscribersResponse,
)
from api.v1.newsletter import serialize_subscriber


class TestNewsletterSchemas(unittest.TestCase):
    """Test validation and serialization of Newsletter schemas."""

    def test_newsletter_subscribe_valid_email(self):
        """Valid email is trimmed and lowercased."""
        req = NewsletterSubscribeRequest(email="  ARTIST.FAN@EXAMPLE.COM  ")
        self.assertEqual(req.email, "artist.fan@example.com")

    def test_newsletter_subscribe_invalid_email(self):
        """Invalid email formats raise ValidationError."""
        invalid_emails = [
            "notanemail",
            "@missinguser.com",
            "user@.com",
            "user@domain",
            "",
            "   ",
        ]
        for bad_email in invalid_emails:
            with self.subTest(bad_email=bad_email):
                with self.assertRaises(ValidationError):
                    NewsletterSubscribeRequest(email=bad_email)

    def test_serialize_subscriber(self):
        """serialize_subscriber converts Beanie document into clean response dictionary."""
        from unittest.mock import MagicMock
        mock_sub = MagicMock()
        mock_sub.id = ObjectId()
        mock_sub.email = "collector@artisa.ir"
        mock_sub.is_active = True
        mock_sub.created_at = datetime.utcnow()
        mock_sub.updated_at = datetime.utcnow()

        serialized = serialize_subscriber(mock_sub)
        self.assertEqual(serialized.id, str(mock_sub.id))
        self.assertEqual(serialized.email, "collector@artisa.ir")
        self.assertTrue(serialized.is_active)

    def test_paginated_response_schema(self):
        """Paginated response properly holds items and active count."""
        res = PaginatedNewsletterSubscribersResponse(
            items=[
                NewsletterSubscriberResponse(
                    id="65f888888888888888888888",
                    email="vip@artisa.ir",
                    is_active=True,
                )
            ],
            total=1,
            page=1,
            limit=10,
            total_pages=1,
            active_count=1,
        )
        self.assertEqual(len(res.items), 1)
        self.assertEqual(res.total, 1)
        self.assertEqual(res.active_count, 1)


if __name__ == "__main__":
    unittest.main()
