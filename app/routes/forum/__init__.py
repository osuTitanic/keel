
from fastapi import APIRouter

from . import subscriptions
from . import bookmarks
from . import bbcode
from . import images
from . import topics
from . import forum
from . import posts

router = APIRouter()
router.include_router(subscriptions.router)
router.include_router(bookmarks.router)
router.include_router(bbcode.router)
router.include_router(images.router)
router.include_router(topics.router)
router.include_router(forum.router)
router.include_router(posts.router)
