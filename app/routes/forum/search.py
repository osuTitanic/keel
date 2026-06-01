
from fastapi import HTTPException, APIRouter, Request, Query
from app.models import ForumSearchResponse, PostModel, TopicModel
from app.common.database.repositories import posts, topics

router = APIRouter()

@router.get("/search", response_model=ForumSearchResponse)
def search_forum(
    request: Request,
    query: str = Query(...),
    limit: int = Query(15, ge=1, le=30),
    offset: int = Query(0, ge=0)
) -> ForumSearchResponse:
    return ForumSearchResponse(
        query=query,
        topics=[
            TopicModel.model_validate(topic, from_attributes=True)
            for topic in topics.search(query, offset, limit, request.state.db)
        ],
        posts=[
            PostModel.model_validate(post, from_attributes=True)
            for post in posts.search(query, offset, limit, request.state.db)
        ]
    )
