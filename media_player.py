"""Media player platform for simulated devices."""

from __future__ import annotations

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
    RepeatMode,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DEVICE_TYPE_MEDIA_PLAYER
from .coordinator import SimulatedDeviceCoordinator
from .entity import SimulatedEntity

_STATE_MAP = {
    "playing": MediaPlayerState.PLAYING,
    "paused": MediaPlayerState.PAUSED,
    "idle": MediaPlayerState.IDLE,
    "off": MediaPlayerState.OFF,
    "standby": MediaPlayerState.STANDBY,
}

_REPEAT_MAP = {
    "off": RepeatMode.OFF,
    "one": RepeatMode.ONE,
    "all": RepeatMode.ALL,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up simulated media player entities."""
    coordinator: SimulatedDeviceCoordinator = entry.runtime_data
    if coordinator.device_type != DEVICE_TYPE_MEDIA_PLAYER:
        return
    async_add_entities([SimulatedMediaPlayerEntity(coordinator)])


class SimulatedMediaPlayerEntity(SimulatedEntity, MediaPlayerEntity):
    """Simulated media player with full feature support."""

    _attr_icon = "mdi:television-play"
    _attr_supported_features = (
        MediaPlayerEntityFeature.PLAY
        | MediaPlayerEntityFeature.PAUSE
        | MediaPlayerEntityFeature.STOP
        | MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.VOLUME_STEP
        | MediaPlayerEntityFeature.SELECT_SOURCE
        | MediaPlayerEntityFeature.SELECT_SOUND_MODE
        | MediaPlayerEntityFeature.NEXT_TRACK
        | MediaPlayerEntityFeature.PREVIOUS_TRACK
        | MediaPlayerEntityFeature.SEEK
        | MediaPlayerEntityFeature.SHUFFLE_SET
        | MediaPlayerEntityFeature.REPEAT_SET
        | MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
    )

    def __init__(self, coordinator: SimulatedDeviceCoordinator) -> None:
        super().__init__(coordinator, "media_player", "Media Player")

    @property
    def state(self) -> MediaPlayerState:
        return _STATE_MAP.get(self.coordinator.data.get("state", "idle"), MediaPlayerState.IDLE)

    @property
    def volume_level(self) -> float | None:
        return self.coordinator.data.get("volume_level")

    @property
    def is_volume_muted(self) -> bool | None:
        return self.coordinator.data.get("is_volume_muted")

    @property
    def media_title(self) -> str | None:
        return self.coordinator.data.get("media_title")

    @property
    def media_artist(self) -> str | None:
        return self.coordinator.data.get("media_artist")

    @property
    def media_album_name(self) -> str | None:
        return self.coordinator.data.get("media_album_name")

    @property
    def media_duration(self) -> int | None:
        return self.coordinator.data.get("media_duration")

    @property
    def media_position(self) -> int | None:
        return self.coordinator.data.get("media_position")

    @property
    def media_position_updated_at(self):
        if self.state == MediaPlayerState.PLAYING:
            return dt_util.utcnow()
        return None

    @property
    def media_content_type(self) -> MediaType | None:
        if self.state in (MediaPlayerState.PLAYING, MediaPlayerState.PAUSED):
            return MediaType.MUSIC
        return None

    @property
    def source(self) -> str | None:
        return self.coordinator.data.get("source")

    @property
    def source_list(self) -> list[str] | None:
        return self.coordinator.data.get("source_list")

    @property
    def shuffle(self) -> bool | None:
        return self.coordinator.data.get("shuffle", False)

    @property
    def repeat(self) -> RepeatMode | None:
        return _REPEAT_MAP.get(self.coordinator.data.get("repeat", "off"), RepeatMode.OFF)

    @property
    def sound_mode(self) -> str | None:
        return self.coordinator.data.get("sound_mode")

    @property
    def sound_mode_list(self) -> list[str] | None:
        return self.coordinator.data.get("sound_mode_list")

    async def async_turn_on(self) -> None:
        self.coordinator.set_state(state="idle")

    async def async_turn_off(self) -> None:
        self.coordinator.set_state(state="off", media_title=None, media_artist=None, media_album_name=None)

    async def async_media_play(self) -> None:
        self.coordinator.set_state(state="playing")

    async def async_media_pause(self) -> None:
        self.coordinator.set_state(state="paused")

    async def async_media_stop(self) -> None:
        self.coordinator.set_state(state="idle", media_title=None, media_artist=None, media_album_name=None, media_position=0)

    async def async_media_next_track(self) -> None:
        self.coordinator.set_state(media_position=0)

    async def async_media_previous_track(self) -> None:
        self.coordinator.set_state(media_position=0)

    async def async_set_volume_level(self, volume: float) -> None:
        self.coordinator.set_state(volume_level=max(0.0, min(1.0, volume)))

    async def async_volume_up(self) -> None:
        vol = min(1.0, (self.coordinator.data.get("volume_level") or 0.3) + 0.05)
        self.coordinator.set_state(volume_level=round(vol, 2))

    async def async_volume_down(self) -> None:
        vol = max(0.0, (self.coordinator.data.get("volume_level") or 0.3) - 0.05)
        self.coordinator.set_state(volume_level=round(vol, 2))

    async def async_mute_volume(self, mute: bool) -> None:
        self.coordinator.set_state(is_volume_muted=mute)

    async def async_select_source(self, source: str) -> None:
        self.coordinator.set_state(source=source)

    async def async_select_sound_mode(self, sound_mode: str) -> None:
        self.coordinator.set_state(sound_mode=sound_mode)

    async def async_media_seek(self, position: float) -> None:
        dur = self.coordinator.data.get("media_duration") or 360
        self.coordinator.set_state(media_position=max(0, min(dur, int(position))))

    async def async_set_shuffle(self, shuffle: bool) -> None:
        self.coordinator.set_state(shuffle=shuffle)

    async def async_set_repeat(self, repeat: RepeatMode) -> None:
        r = {v: k for k, v in _REPEAT_MAP.items()}.get(repeat, "off")
        self.coordinator.set_state(repeat=r)
