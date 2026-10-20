
from fastapi import APIRouter, HTTPException, Request, status

from app.common.database import matches
from app.common.helpers import permissions
from app.models import ErrorResponse
from app.models.multiplayer import *
from app.security import require_login
from app.utils import requires

router = APIRouter(
    dependencies=[require_login],
    responses={
        404: {"model": ErrorResponse, "description": "Match not found"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        409: {"model": ErrorResponse, "description": "Match is no longer active"},
    },
)

@requires("users.authenticated")
def submit_multiplayer_event(
    id: int,
    request: Request,
    event_type: MultiplayerEventType,
    data: BaseModel | None = None,
) -> MultiplayerManagementResponse:
    match = matches.fetch_by_id(id, request.state.db)

    if match is None:
        raise HTTPException(404, "The requested match could not be found")

    can_force_manage = permissions.has_permission(
        "bancho.matches.manage",
        request.user.id
    )

    if match.creator_id != request.user.id and not can_force_manage:
        raise HTTPException(403, "Insufficient permissions")

    if match.ended_at is not None:
        raise HTTPException(409, "The requested match is no longer active")

    request.state.events.submit(
        "multiplayer",
        match_id=match.id,
        event_type=event_type.value,
        data=data.model_dump(mode="json", exclude_none=True) if data else {},
    )
    request.state.logger.info(
        f"'{request.user.name}' submitted multiplayer action "
        f"'{event_type.value}' for match {match.id}"
    )

    return MultiplayerManagementResponse(
        match_id=match.id,
        event_type=event_type,
    )

@router.post(
    "/{id}/start",
    response_model=MultiplayerManagementResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def start_match(
    id: int,
    request: Request,
    data: MultiplayerStartData,
) -> MultiplayerManagementResponse:
    return submit_multiplayer_event(
        id,
        request,
        MultiplayerEventType.Start,
        data
    )

@router.delete(
    "/{id}/start",
    response_model=MultiplayerManagementResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def cancel_match_start(
    id: int,
    request: Request,
) -> MultiplayerManagementResponse:
    return submit_multiplayer_event(
        id,
        request,
        MultiplayerEventType.CancelStart
    )

@router.post(
    "/{id}/countdown",
    response_model=MultiplayerManagementResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def start_match_countdown(
    id: int,
    request: Request,
    data: MultiplayerCountdownData,
) -> MultiplayerManagementResponse:
    return submit_multiplayer_event(
        id,
        request,
        MultiplayerEventType.Countdown,
        data
    )

@router.delete(
    "/{id}/countdown",
    response_model=MultiplayerManagementResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def cancel_match_countdown(
    id: int,
    request: Request,
) -> MultiplayerManagementResponse:
    return submit_multiplayer_event(
        id,
        request,
        MultiplayerEventType.CancelCountdown
    )

@router.post(
    "/{id}/close",
    response_model=MultiplayerManagementResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def close_match(
    id: int,
    request: Request,
) -> MultiplayerManagementResponse:
    return submit_multiplayer_event(
        id,
        request,
        MultiplayerEventType.Close
    )

@router.post(
    "/{id}/abort",
    response_model=MultiplayerManagementResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def abort_match(
    id: int,
    request: Request,
) -> MultiplayerManagementResponse:
    return submit_multiplayer_event(
        id,
        request,
        MultiplayerEventType.Abort
    )

@router.put(
    "/{id}/beatmap",
    response_model=MultiplayerManagementResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def set_match_beatmap(
    id: int,
    request: Request,
    data: MultiplayerBeatmapData,
) -> MultiplayerManagementResponse:
    return submit_multiplayer_event(
        id,
        request,
        MultiplayerEventType.SetBeatmap,
        data
    )

@router.put(
    "/{id}/mods",
    response_model=MultiplayerManagementResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def set_match_mods(
    id: int,
    request: Request,
    data: MultiplayerModsData,
) -> MultiplayerManagementResponse:
    return submit_multiplayer_event(
        id,
        request,
        MultiplayerEventType.SetMods,
        data
    )

@router.put(
    "/{id}/freemod",
    response_model=MultiplayerManagementResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def set_match_freemod(
    id: int,
    request: Request,
    data: MultiplayerFreemodData,
) -> MultiplayerManagementResponse:
    return submit_multiplayer_event(
        id,
        request,
        MultiplayerEventType.SetFreemod,
        data
    )

@router.put(
    "/{id}/host",
    response_model=MultiplayerManagementResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def set_match_host(
    id: int,
    request: Request,
    data: MultiplayerUserData,
) -> MultiplayerManagementResponse:
    return submit_multiplayer_event(
        id,
        request,
        MultiplayerEventType.SetHost,
        data
    )

@router.delete(
    "/{id}/host",
    response_model=MultiplayerManagementResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def clear_match_host(
    id: int,
    request: Request
) -> MultiplayerManagementResponse:
    return submit_multiplayer_event(
        id,
        request,
        MultiplayerEventType.ClearHost
    )

@router.post(
    "/{id}/invitation",
    response_model=MultiplayerManagementResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def invite_match_player(
    id: int,
    request: Request,
    data: MultiplayerUserData,
) -> MultiplayerManagementResponse:
    return submit_multiplayer_event(
        id,
        request,
        MultiplayerEventType.InvitePlayer,
        data
    )

@router.post(
    "/{id}/player",
    response_model=MultiplayerManagementResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def force_invite_match_player(
    id: int,
    request: Request,
    data: MultiplayerUserData,
) -> MultiplayerManagementResponse:
    return submit_multiplayer_event(
        id,
        request,
        MultiplayerEventType.ForceInvitePlayer,
        data,
    )

@router.post(
    "/{id}/lock",
    response_model=MultiplayerManagementResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def lock_match_slots(
    id: int,
    request: Request,
) -> MultiplayerManagementResponse:
    return submit_multiplayer_event(
        id,
        request,
        MultiplayerEventType.LockSlots
    )

@router.post(
    "/{id}/unlock",
    response_model=MultiplayerManagementResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def unlock_match_slots(
    id: int,
    request: Request,
) -> MultiplayerManagementResponse:
    return submit_multiplayer_event(
        id,
        request,
        MultiplayerEventType.UnlockSlots
    )

@router.delete(
    "/{id}/player",
    response_model=MultiplayerManagementResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def kick_match_player(
    id: int,
    request: Request,
    data: MultiplayerUserData,
) -> MultiplayerManagementResponse:
    return submit_multiplayer_event(
        id,
        request,
        MultiplayerEventType.KickPlayer,
        data
    )

@router.post(
    "/{id}/ban",
    response_model=MultiplayerManagementResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def ban_match_player(
    id: int,
    request: Request,
    data: MultiplayerUserData,
) -> MultiplayerManagementResponse:
    return submit_multiplayer_event(
        id,
        request,
        MultiplayerEventType.BanPlayer,
        data
    )

@router.delete(
    "/{id}/ban",
    response_model=MultiplayerManagementResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def unban_match_player(
    id: int,
    request: Request,
    data: MultiplayerUserData,
) -> MultiplayerManagementResponse:
    return submit_multiplayer_event(
        id,
        request,
        MultiplayerEventType.UnbanPlayer,
        data
    )

@router.put(
    "/{id}/name",
    response_model=MultiplayerManagementResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def set_match_name(
    id: int,
    request: Request,
    data: MultiplayerNameData,
) -> MultiplayerManagementResponse:
    return submit_multiplayer_event(
        id,
        request,
        MultiplayerEventType.SetName,
        data
    )

@router.put(
    "/{id}/password",
    response_model=MultiplayerManagementResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def set_match_password(
    id: int,
    request: Request,
    data: MultiplayerPasswordData,
) -> MultiplayerManagementResponse:
    return submit_multiplayer_event(
        id,
        request,
        MultiplayerEventType.SetPassword,
        data
    )

@router.patch(
    "/{id}/settings",
    response_model=MultiplayerManagementResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def set_match_settings(
    id: int,
    request: Request,
    data: MultiplayerSettingsData,
) -> MultiplayerManagementResponse:
    return submit_multiplayer_event(
        id,
        request,
        MultiplayerEventType.SetSettings,
        data
    )

@router.put(
    "/{id}/slots",
    response_model=MultiplayerManagementResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def set_match_slot_size(
    id: int,
    request: Request,
    data: MultiplayerSlotSizeData,
) -> MultiplayerManagementResponse:
    return submit_multiplayer_event(
        id,
        request,
        MultiplayerEventType.SetSlotSize,
        data
    )

@router.put(
    "/{id}/player/slot",
    response_model=MultiplayerManagementResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def move_match_player(
    id: int,
    request: Request,
    data: MultiplayerMovePlayerData,
) -> MultiplayerManagementResponse:
    return submit_multiplayer_event(
        id,
        request,
        MultiplayerEventType.MovePlayer,
        data
    )

@router.put(
    "/{id}/player/team",
    response_model=MultiplayerManagementResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def set_match_team(
    id: int,
    request: Request,
    data: MultiplayerTeamData,
) -> MultiplayerManagementResponse:
    return submit_multiplayer_event(
        id,
        request,
        MultiplayerEventType.SetTeam,
        data
    )

@router.post(
    "/{id}/referee",
    response_model=MultiplayerManagementResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def add_match_referee(
    id: int,
    request: Request,
    data: MultiplayerUserData,
) -> MultiplayerManagementResponse:
    return submit_multiplayer_event(
        id,
        request,
        MultiplayerEventType.AddReferee,
        data
    )

@router.delete(
    "/{id}/referee",
    response_model=MultiplayerManagementResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def remove_match_referee(
    id: int,
    request: Request,
    data: MultiplayerUserData,
) -> MultiplayerManagementResponse:
    return submit_multiplayer_event(
        id,
        request,
        MultiplayerEventType.RemoveReferee,
        data
    )
