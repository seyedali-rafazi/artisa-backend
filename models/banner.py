"""Banner Document Model for Hero Slider."""

from beanie import Document


class Banner(Document):
    """Hero Slider Banner model."""

    title: str
    subtitle: str
    badge: str = ""
    buttonText: str = ""
    image: str
    link: str = "/"
    order: int = 0

    class Settings:
        name = "banners"
