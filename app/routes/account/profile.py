
from fastapi import HTTPException, APIRouter, Request
from starlette.authentication import requires

from app.models import UserModel, ErrorResponse, ProfileUpdateModel
from app.common.constants.regexes import DISCORD_USERNAME, URL
from app.security import require_login
from app.common.database import users

import re

router = APIRouter(
    responses={403: {'model': ErrorResponse, 'description': 'Authentication failure'}},
    dependencies=[require_login]
)

@router.get('/profile', response_model=UserModel)
@requires('authenticated')
def profile(request: Request) -> UserModel:
    return UserModel.model_validate(
        request.user,
        from_attributes=True
    )

@router.post('/profile', response_model=UserModel)
@requires(['authenticated', 'unrestricted', 'unsilenced', 'activated'])
def update_profile(
    request: Request,
    update: ProfileUpdateModel
) -> UserModel:
    if update.interests != None and len(update.interests) > 30:
        raise HTTPException(
            status_code=400,
            detail='Please keep your updates.interests short!'
        )

    if update.location != None and len(update.location) > 30:
        raise HTTPException(
            status_code=400,
            detail='Please keep your updates.location short!'
        )

    if update.twitter != None and len(update.twitter) > 64:
        raise HTTPException(
            status_code=400,
            detail='Please type in a valid updates.twitter handle or url!'
        )

    if update.website != None and len(update.website) > 64:
        raise HTTPException(
            status_code=400,
            detail='Please keep your updates.website url short!'
        )

    if update.website != None and not URL.match(update.website):
        raise HTTPException(
            status_code=400,
            detail='Please type in a valid updates.website url!'
        )

    if update.discord != None and not DISCORD_USERNAME.match(update.discord):
        raise HTTPException(
            status_code=400,
            detail='Invalid updates.discord username. Please try again!'
        )

    updates = {
        'interests': update.interests,
        'location': update.location,
        'website': update.website,
        'discord': update.discord.removeprefix('@') if update.discord else None,
        'twitter': f'https://updates.twitter.com/{update.twitter_handle(update.twitter)}' if update.twitter else None
    }

    users.update(
        request.user.id,
        updates,
        request.state.db
    )

    return UserModel.model_validate(
        users.fetch_by_id(request.user.id, session=request.state.db),
        from_attributes=True
    )

def twitter_handle(url: str) -> str:
    """Parse twitter handle from url and return it"""
    url_match = re.search(r'https?://(www.)?(twitter|x)\.com/(@\w+|\w+)', url)

    if url_match:
        return url_match.group(3)

    if not url.startswith('@'):
        url = f'@{url}'

    return url
