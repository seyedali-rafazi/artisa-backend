"""Blog Router."""

from fastapi import APIRouter, status

from models.blog import Article
from schemas.blog import ArticleResponse
from schemas.response import success_response, error_response

router = APIRouter()


@router.get("/articles", summary="Get blog articles list")
async def list_articles():
    """Retrieve all blog articles."""
    articles = await Article.find_all().sort("-created_at").to_list()

    items = [
        ArticleResponse(
            id=a.articleId,
            title=a.title,
            desc=a.desc,
            content=a.content,
            date=a.date,
            author=a.author,
            image=a.image,
        ).model_dump()
        for a in articles
    ]

    return success_response(data=items, message="لیست مقالات بلاگ دریافت شد")


@router.get("/articles/{id}", summary="Get single blog article")
async def get_article(id: str):
    """Retrieve single blog article by articleId or mongo ID."""
    article = await Article.find_one(Article.articleId == id)
    if not article:
        try:
            from beanie import PydanticObjectId

            article = await Article.get(PydanticObjectId(id))
        except Exception:
            pass

    if not article:
        return error_response(
            message="مقاله یافت نشد", status_code=status.HTTP_404_NOT_FOUND
        )

    data = ArticleResponse(
        id=article.articleId,
        title=article.title,
        desc=article.desc,
        content=article.content,
        date=article.date,
        author=article.author,
        image=article.image,
    ).model_dump()

    return success_response(data=data, message="اطلاعات مقاله دریافت شد")
