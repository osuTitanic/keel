
from fastapi import HTTPException, APIRouter, Request
from redis.asyncio import Redis

from app.security import require_login, password_authentication
from app.models import ErrorResponse, DataExportRequest
from app.utils import requires
from app.common.database import (
    comments,
    messages,
    clients,
    groups,
    logins,
    names
)

router = APIRouter(
    responses={
        403: {'model': ErrorResponse, 'description': 'Forbidden'},
        401: {'model': ErrorResponse, 'description': 'Authentication failure'},
    },
    dependencies=[require_login]
)

@router.post("/export")
@requires("users.authenticated")
def data_export(request: Request, data: DataExportRequest) -> dict:
    # TODO: Rate-limit data exports to once a day
    # TODO: reCAPTCHA integration

    if not password_authentication(data.password, request.user.bcrypt):
        raise HTTPException(status_code=401, detail="Authentication failure")

    name_history = names.fetch_all(
        request.user.id,
        request.state.db
    )
    user_groups = groups.fetch_user_groups(
        request.user.id,
        include_hidden=True,
        session=request.state.db
    )

    user_logins = logins.fetch_all(
        request.user.id,
        session=request.state.db
    )
    user_clients = clients.fetch_all(
        request.user.id,
        session=request.state.db
    )
    hardware_adapters = set()
    hardware_unique_id = set()
    hardware_disk_signature = set()

    for client in user_clients:
        hardware_adapters.add(client.adapters)
        hardware_unique_id.add(client.unique_id)
        hardware_disk_signature.add(client.disk_signature)

    pms = messages.fetch_dms_all(
        request.user.id,
        session=request.state.db
    )
    beatmap_comments = comments.fetch_all_by_user(
        request.user.id,
        session=request.state.db
    )

    return {
        "id": request.user.id,
        "username": request.user.name,
        "safe_name": request.user.safe_name,
        "email": request.user.email,
        "country": request.user.country,
        "irc_token": request.user.irc_token,
        "created_at": request.user.created_at,
        "latest_activity": request.user.latest_activity,
        "discord_id": request.user.discord_id,
        "is_bot": request.user.is_bot,
        "restricted": request.user.restricted,
        "activated": request.user.activated,
        "silence_end": request.user.silence_end,
        "avatar_hash": request.user.avatar_hash,
        "avatar_last_update": request.user.avatar_last_update,
        "friendonly_dms": request.user.friendonly_dms,
        "profile": {
            "preferred_mode": request.user.preferred_mode,
            "preferred_ranking": request.user.preferred_ranking,
            "playstyle": request.user.playstyle,
            "userpage": request.user.userpage,
            "signature": request.user.signature,
            "title": request.user.title,
            "banner": request.user.banner,
            "website": request.user.website,
            "discord": request.user.discord,
            "twitter": request.user.twitter,
            "location": request.user.location,
            "interests": request.user.interests,
            "badges": [
                {
                    "id": badge.id,
                    "created": badge.created,
                    "badge_icon": badge.badge_icon,
                    "badge_url": badge.badge_url,
                    "badge_description": badge.badge_description
                }
                for badge in request.user.badges
            ],
            "name_history": [
                {
                    "name": name.name,
                    "reserved": name.reserved,
                    "changed_at": name.changed_at
                }
                for name in name_history
            ],
            "groups": [
                {
                    "id": group.id,
                    "name": group.name,
                    "short_name": group.short_name,
                    "description": group.description,
                    "color": group.color
                }
                for group in user_groups
            ],
            "activity": [
                {
                    "id": activity.id,
                    "time": activity.time,
                    "mode": activity.mode,
                    "type": activity.type,
                    "data": activity.data,
                    "hidden": activity.hidden
                }
                for activity in request.user.activity
            ],
            "relationships": [
                {
                    "target_id": rel.target_id,
                    "status": "friend" if rel.status == 0 else "blocked"
                }
                for rel in request.user.relationships
            ]
        },
        "ranking": {
            "stats": [
                {
                    "mode": stats.mode,
                    "rank": stats.rank,
                    "peak_rank": stats.peak_rank,
                    "tscore": stats.tscore,
                    "rscore": stats.rscore,
                    "pp": stats.pp,
                    "ppv1": stats.ppv1,
                    "playcount": stats.playcount,
                    "playtime": stats.playtime,
                    "acc": stats.acc,
                    "max_combo": stats.max_combo,
                    "total_hits": stats.total_hits,
                    "replay_views": stats.replay_views,
                    "xh_count": stats.xh_count,
                    "x_count": stats.x_count,
                    "sh_count": stats.sh_count,
                    "s_count": stats.s_count,
                    "a_count": stats.a_count,
                    "b_count": stats.b_count,
                    "c_count": stats.c_count,
                    "d_count": stats.d_count
                }
                for stats in request.user.stats
            ],
            "plays": [
                {
                    "beatmap_id": play.beatmap_id,
                    "beatmap_file": play.beatmap_file,
                    "set_id": play.set_id,
                    "count": play.count
                }
                for play in request.user.plays
            ],
            "scores": [
                {
                    "id": score.id,
                    "user_id": score.user_id,
                    "beatmap_id": score.beatmap_id,
                    "submitted_at": score.submitted_at,
                    "checksum": score.checksum,
                    "mode": score.mode,
                    "client_version": score.client_version,
                    "client_string": score.client_string,
                    "client_hash": score.client_hash,
                    "pp": score.pp,
                    "ppv1": score.ppv1,
                    "acc": score.acc,
                    "total_score": score.total_score,
                    "max_combo": score.max_combo,
                    "mods": score.mods,
                    "perfect": score.perfect,
                    "count_300": score.n300,
                    "count_100": score.n100,
                    "count_50": score.n50,
                    "count_miss": score.nMiss,
                    "count_geki": score.nGeki,
                    "count_katu": score.nKatu,
                    "grade": score.grade,
                    "status_pp": score.status_pp,
                    "status_score": score.status_score,
                    "pinned": score.pinned,
                    "hidden": score.hidden,
                    "failtime": score.failtime,
                    "replay_md5": score.replay_md5,
                    "replay_views": score.replay_views
                }
                for score in request.user.scores
            ],
            "achievements": [
                {
                    "name": achievement.name,
                    "category": achievement.category,
                    "unlocked_at": achievement.unlocked_at
                }
                for achievement in request.user.achievements
            ],
            "benchmarks": [
                {
                    "id": benchmark.id,
                    "created_at": benchmark.created_at,
                    "smoothness": benchmark.smoothness,
                    "framerate": benchmark.framerate,
                    "score": benchmark.score,
                    "grade": benchmark.grade,
                    "client": benchmark.client,
                    "hardware": benchmark.hardware
                }
                for benchmark in request.user.benchmarks
            ],
            "matches": [
                {
                    "id": match.id,
                    "name": match.name,
                    "created_at": match.created_at,
                    "ended_at": match.ended_at
                }
                for match in request.user.matches
            ]
        },
        "beatmaps": {
            "uploads": [
                {
                    "id": set.id,
                    "title": set.title,
                    "title_unicode": set.title_unicode,
                    "artist": set.artist,
                    "artist_unicode": set.artist_unicode,
                    "source": set.source,
                    "source_unicode": set.source_unicode,
                    "creator": set.creator,
                    "display_title": set.display_title,
                    "description": set.description,
                    "tags": set.tags,
                    "status": set.status,
                    "has_video": set.has_video,
                    "has_storyboard": set.has_storyboard,
                    "server": set.server,
                    "download_server": set.download_server,
                    "topic_id": set.topic_id,
                    "creator_id": set.creator_id,
                    "available": set.available,
                    "enhanced": set.enhanced,
                    "explicit": set.explicit,
                    "created_at": set.created_at,
                    "approved_at": set.approved_at,
                    "approved_by": set.approved_by,
                    "last_update": set.last_update,
                    "total_playcount": set.total_playcount,
                    "max_diff": set.max_diff,
                    "rating_average": set.rating_average,
                    "rating_count": set.rating_count,
                    "favourite_count": set.favourite_count,
                    "osz_filesize": set.osz_filesize,
                    "osz_filesize_novideo": set.osz_filesize_novideo,
                    "language_id": set.language_id,
                    "genre_id": set.genre_id,
                    "offset": set.offset
                }
                for set in request.user.created_beatmapsets
            ],
            "favourites": [
                {
                    "set_id": fav.set_id,
                    "created_at": fav.created_at
                }
                for fav in request.user.favourites
            ],
            "ratings": [
                {
                    "beatmap_checksum": rating.map_checksum,
                    "set_id": rating.set_id,
                    "rating": rating.rating
                }
                for rating in request.user.ratings
            ],
            "comments": [
                {
                    "id": comment.id,
                    "target_id": comment.target_id,
                    "target_type": comment.target_type,
                    "comment": comment.comment,
                    "format": comment.format,
                    "color": comment.color,
                    "mode": comment.mode,
                    "time": comment.time
                }
                for comment in beatmap_comments
            ],
            "collaborations": [
                {
                    "beatmap_id": collab.beatmap_id,
                    "is_beatmap_author": collab.is_beatmap_author,
                    "allow_resource_updates": collab.allow_resource_updates,
                    "created_at": collab.created_at
                }
                for collab in request.user.collaborations
            ],
            "nominations": [
                {
                    "set_id": nomination.set_id,
                    "time": nomination.time
                }
                for nomination in request.user.nominations
            ]
        },
        "historical": {
            "ranking": [
                {
                    "time": entry.time,
                    "mode": entry.mode,
                    "rscore": entry.rscore,
                    "pp": entry.pp,
                    "ppv1": entry.ppv1,
                    "global_rank": entry.global_rank,
                    "country_rank": entry.country_rank,
                    "score_rank": entry.score_rank,
                    "ppv1_rank": entry.ppv1_rank
                }
                for entry in request.user.rank_history
            ],
            "plays": [
                {
                    "mode": entry.mode,
                    "year": entry.year,
                    "month": entry.month,
                    "plays": entry.plays,
                    "created_at": entry.created_at
                }
                for entry in request.user.play_history
            ],
            "replays": [
                {
                    "mode": entry.mode,
                    "year": entry.year,
                    "month": entry.month,
                    "views": entry.replay_views,
                    "created_at": entry.created_at
                }
                for entry in request.user.replay_history
            ]
        },
        "sensitive": {
            "logins": [
                {
                    "time": login.time,
                    "ip": login.ip,
                    "version": login.version
                }
                for login in user_logins
            ],
            "hardware_info": {
                "adapters": list(hardware_adapters),
                "unique_ids": list(hardware_unique_id),
                "disk_signatures": list(hardware_disk_signature)
            },
            "private_messages": [
                {
                    "id": pm.id,
                    "sender_id": pm.sender_id,
                    "target_id": pm.target_id,
                    "message": pm.message,
                    "time": pm.time,
                    "read": pm.read
                }
                for pm in pms
            ],
            "screenshots": [
                {
                    "id": screenshot.id,
                    "created_at": screenshot.created_at,
                    "hidden": screenshot.hidden
                }
                for screenshot in request.user.screenshots
            ],
            "notifications": [
                {
                    "id": notification.id,
                    "type": notification.type,
                    "header": notification.header,
                    "content": notification.content,
                    "link": notification.link,
                    "read": notification.read,
                    "time": notification.time
                }
                for notification in request.user.notifications
            ]
        },
        "forum": {
            "posts": [
                {
                    "id": post.id,
                    "topic_id": post.topic_id,
                    "forum_id": post.forum_id,
                    "icon_id": post.icon_id,
                    "content": post.content,
                    "created_at": post.created_at,
                    "edit_time": post.edit_time,
                    "edit_count": post.edit_count,
                    "edit_locked": post.edit_locked,
                    "hidden": post.hidden,
                    "draft": post.draft,
                    "deleted": post.deleted
                }
                for post in request.user.created_posts
            ],
            "topics": [
                {
                    "id": topic.id,
                    "forum_id": topic.forum_id,
                    "title": topic.title,
                    "created_at": topic.created_at,
                    "status_text": topic.status_text,
                    "last_post_at": topic.last_post_at,
                    "locked_at": topic.locked_at,
                    "views": topic.views,
                    "post_count": topic.post_count,
                    "icon_id": topic.icon_id,
                    "announcement": topic.announcement,
                    "hidden": topic.hidden,
                    "pinned": topic.pinned
                }
                for topic in request.user.created_topics
            ],
            "subscriptions": [
                subscription.topic_id
                for subscription in request.user.subscribed_topics
            ],
            "bookmarks": [
                bookmark.topic_id
                for bookmark in request.user.bookmarked_topics
            ]
        }
    }
