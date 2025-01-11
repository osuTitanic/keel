
from fastapi import HTTPException, APIRouter, Request, Form
from starlette.authentication import requires

from app.common.constants.regexes import DISCORD_USERNAME, URL
from app.models import UserModel, ErrorResponse
from app.security import require_login
from app.common.database import users

import re

router = APIRouter(
    responses={403: {'model': ErrorResponse}},
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
    interests: str = Form(None),
    location: str = Form(None),
    website: str = Form(None),
    discord: str = Form(None),
    twitter: str = Form(None)
) -> UserModel:
    if interests != None and len(interests) > 30:
        raise HTTPException(
            status_code=400,
            detail='Please keep your interests short!'
        )

    if location != None and len(location) > 30:
        raise HTTPException(
            status_code=400,
            detail='Please keep your location short!'
        )

    if twitter != None and len(twitter) > 64:
        raise HTTPException(
            status_code=400,
            detail='Please type in a valid twitter handle or url!'
        )

    if website != None and len(website) > 64:
        raise HTTPException(
            status_code=400,
            detail='Please keep your website url short!'
        )

    if website != None and not URL.match(website):
        raise HTTPException(
            status_code=400,
            detail='Please type in a valid website url!'
        )

    if discord != None and not DISCORD_USERNAME.match(discord.removeprefix('@')):
        raise HTTPException(
            status_code=400,
            detail='Invalid discord username. Please try again!'
        )

    updates = {
        'interests': interests,
        'location': location,
        'website': website,
        'discord': discord.removeprefix('@') if discord else None,
        'twitter': f'https://twitter.com/{twitter_handle(twitter)}' if twitter else None
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
