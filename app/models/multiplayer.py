
from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime
from enum import StrEnum

from app.common.constants import (
    MatchScoringTypes,
    MatchTeamTypes,
    GameMode,
    SlotTeam
)

from .user import UserModel


class MatchEventModel(BaseModel):
    time: datetime
    type: int
    data: dict

class MatchModel(BaseModel):
    id: int
    name: str
    created_at: datetime
    ended_at: datetime | None
    creator: UserModel
    events: list[MatchEventModel]

class MultiplayerEventType(StrEnum):
    Start = "start"
    CancelStart = "cancel_start"
    Countdown = "countdown"
    CancelCountdown = "cancel_countdown"
    Close = "close"
    Abort = "abort"
    SetBeatmap = "set_beatmap"
    SetMods = "set_mods"
    SetFreemod = "set_freemod"
    SetHost = "set_host"
    ClearHost = "clear_host"
    InvitePlayer = "invite_player"
    ForceInvitePlayer = "force_invite_player"
    LockSlots = "lock_slots"
    UnlockSlots = "unlock_slots"
    KickPlayer = "kick_player"
    BanPlayer = "ban_player"
    UnbanPlayer = "unban_player"
    SetName = "set_name"
    SetSettings = "set_settings"
    SetSlotSize = "set_slot_size"
    MovePlayer = "move_player"
    SetTeam = "set_team"
    SetPassword = "set_password"
    AddReferee = "add_referee"
    RemoveReferee = "remove_referee"

class MultiplayerManagementResponse(BaseModel):
    accepted: bool = True
    match_id: int
    event_type: MultiplayerEventType

class MultiplayerStartData(BaseModel):
    duration: int | None = Field(default=None, ge=0, le=60 * 5)
    force: bool = False

class MultiplayerCountdownData(BaseModel):
    duration: int = Field(ge=0, le=60 * 15)

class MultiplayerBeatmapData(BaseModel):
    beatmap_id: int = Field(gt=0)
    mode: GameMode | None = None

class MultiplayerModsData(BaseModel):
    mods: int = Field(ge=0, le=0xFFFFFFFF)
    freemod: bool | None = None

class MultiplayerFreemodData(BaseModel):
    enabled: bool

class MultiplayerUserData(BaseModel):
    user_id: int = Field(gt=0)

class MultiplayerNameData(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def name_validator(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("name cannot be empty")
        return value

class MultiplayerSettingsData(BaseModel):
    team_type: MatchTeamTypes
    scoring_type: MatchScoringTypes | None = None
    slot_size: int | None = Field(default=None, ge=1, le=16)

class MultiplayerSlotSizeData(BaseModel):
    slot_size: int = Field(ge=1, le=16)

class MultiplayerMovePlayerData(MultiplayerUserData):
    slot_id: int = Field(ge=1, le=16)

class MultiplayerTeamData(MultiplayerUserData):
    team: SlotTeam

class MultiplayerPasswordData(BaseModel):
    password: str
