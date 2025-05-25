
from fastapi import HTTPException, APIRouter, Request
from app.models import UserModel, ErrorResponse, ProfileUpdateModel
from app.common.constants.regexes import DISCORD_USERNAME, URL
from app.security import require_login
from app.common.database import users
from app.utils import requires

import re

router = APIRouter(
    responses={403: {'model': ErrorResponse, 'description': 'Authentication failure'}},
    dependencies=[require_login]
)

@router.get("/profile", response_model=UserModel)
@requires("users.authenticated")
def profile(request: Request) -> UserModel:
    """Get the authenticated user's profile"""
    return UserModel.model_validate(
        request.user,
        from_attributes=True
    )

@router.post("/profile", response_model=UserModel)
@requires("users.profile.update")
def profile_update(
    request: Request,
    update: ProfileUpdateModel
) -> UserModel:
    """Update the authenticated user's public profile"""
    if not validate_update_request(update):
        raise HTTPException(
            status_code=400,
            detail='Invalid update request'
        )

    if update.twitter:
        handle = update.twitter_handle(update.twitter)
        update.twitter = f'https://twitter.com/{handle}'

    if update.discord:
        update.discord = update.discord.removeprefix('@')

    users.update(
        request.user.id,
        {
            'interests': update.interests,
            'location': update.location,
            'website': update.website,
            'discord': update.discord,
            'twitter': update.twitter
        },
        request.state.db
    )

    return UserModel.model_validate(
        users.fetch_by_id(request.user.id, session=request.state.db),
        from_attributes=True
    )

def validate_update_request(update: ProfileUpdateModel) -> bool:
    if update.interests != None and len(update.interests) > 30:
        raise HTTPException(
            status_code=400,
            detail='Please keep your interests short!'
        )

    if update.location != None and len(update.location) > 30:
        raise HTTPException(
            status_code=400,
            detail='Please keep your location short!'
        )

    if update.twitter != None and len(update.twitter) > 64:
        raise HTTPException(
            status_code=400,
            detail='Please type in a valid twitter handle or url!'
        )

    if update.website != None and len(update.website) > 64:
        raise HTTPException(
            status_code=400,
            detail='Please keep your website url short!'
        )

    if update.website != None and not URL.match(update.website):
        raise HTTPException(
            status_code=400,
            detail='Please type in a valid website url!'
        )

    if update.discord != None and not DISCORD_USERNAME.match(update.discord):
        raise HTTPException(
            status_code=400,
            detail='Invalid discord username. Please try again!'
        )
    
    return True

def twitter_handle(url: str) -> str:
    url_match = re.search(r'https?://(www.)?(twitter|x)\.com/(@\w+|\w+)', url)

    if url_match:
        return url_match.group(3)

    if not url.startswith('@'):
        url = f'@{url}'

    return url
