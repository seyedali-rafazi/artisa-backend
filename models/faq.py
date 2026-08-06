"""FAQ Document Model."""

from beanie import Document


class FAQ(Document):
    """FAQ model."""

    question: str
    answer: str
    order: int = 0

    class Settings:
        name = "faqs"
