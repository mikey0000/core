"""The lawn mower integration."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from enum import IntFlag
from functools import partial
import logging
from typing import Any, final

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.entity import Entity, EntityDescription
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN

SCAN_INTERVAL = timedelta(seconds=60)

_LOGGER = logging.getLogger(__name__)

SERVICE_START_MOWING = "start_mowing"
SERVICE_PAUSE = "pause"
SERVICE_ENABLE_SCHEDULE = "enable_schedule"
SERVICE_DISABLE_SCHEDULE = "disable_schedule"
SERVICE_DOCK = "dock"

ERROR = "error"
PAUSED = "paused"
MOWING = "mowing"
DOCKED_SCHEDULE_ENABLED = "docked_schedule_enabled"
DOCKED_SCHEDULE_DISABLED = "docked_schedule_disabled"


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the lawn_mower component."""
    component = hass.data[DOMAIN] = EntityComponent[LawnMowerEntity](
        _LOGGER, DOMAIN, hass, SCAN_INTERVAL
    )
    await component.async_setup(config)

    component.async_register_entity_service(
        SERVICE_START_MOWING, {}, "async_service_start_mowing"
    )
    component.async_register_entity_service(SERVICE_PAUSE, {}, "async_service_pause")
    component.async_register_entity_service(
        SERVICE_ENABLE_SCHEDULE, {}, "async_service_enable_schedule"
    )
    component.async_register_entity_service(
        SERVICE_DISABLE_SCHEDULE, {}, "async_service_disable_schedule"
    )
    component.async_register_entity_service(SERVICE_DOCK, {}, "async_service_dock")

    return True


class Activity(IntFlag):
    """Activity state of the lawn mower entity."""

    ERROR = 1
    PAUSED = 2
    MOWING = 4
    DOCKED_SCHEDULE_DISABLED = 8
    DOCKED_SCHEDULE_ENABLED = 16


class LawnMowerEntityFeature(IntFlag):
    """Supported features of the lawn mower entity."""

    START_MOWING = 1
    PAUSE = 2
    DOCK = 4
    ENABLE_SCHEDULE = 8
    DISABLE_SCHEDULE = 16
    BATTERY = 32
    LINK = 64


@dataclass
class LawnMowerEntityEntityDescription(EntityDescription):
    """A class that describes lawn mower entities."""


class LawnMowerEntity(Entity):
    """Base class for lawn mower entities."""

    entity_description: LawnMowerEntityEntityDescription
    _attr_activity: Activity | None = None
    _attr_supported_features: int

    @final
    @property
    def state(self) -> Activity | None:
        """Return the current state."""
        return self._attr_activity

    @property
    def supported_features(self) -> int:
        """Flag lawn mower features that are supported."""
        return self._attr_supported_features

    def start_mowing(self) -> None:
        """Start mowing."""
        raise NotImplementedError()

    async def async_start_mowing(self, **kwargs: Any) -> None:
        """Start mowing."""
        await self.hass.async_add_executor_job(partial(self.start_mowing, **kwargs))

    def dock(self) -> None:
        """Dock the mower."""
        raise NotImplementedError()

    async def async_dock(self, **kwargs: Any) -> None:
        """Dock the mower."""
        await self.hass.async_add_executor_job(partial(self.dock, **kwargs))

    def pause(self) -> None:
        """Pause the lawn mower."""
        raise NotImplementedError()

    async def async_pause(self, **kwargs: Any) -> None:
        """Pause the lawn mower."""
        await self.hass.async_add_executor_job(partial(self.pause, **kwargs))

    def enable_schedule(self) -> None:
        """Enable the schedule for the lawn mower."""
        raise NotImplementedError()

    async def async_enable_schedule(self, **kwargs: Any) -> None:
        """Enable the schedule for the lawn mower."""
        await self.hass.async_add_executor_job(partial(self.enable_schedule, **kwargs))

    def disable_schedule(self) -> None:
        """Disable the schedule for the lawn mower."""
        raise NotImplementedError()

    async def async_disable_schedule(self, **kwargs: Any) -> None:
        """Disable the schedule for the lawn mower."""
        await self.hass.async_add_executor_job(partial(self.disable_schedule, **kwargs))


async def async_service_start_mowing(
    entity: LawnMowerEntity, service: ServiceCall
) -> None:
    """Handle start mowing service."""
    kwargs = dict(service.data.items())
    await entity.async_start_mowing(**kwargs)


async def async_service_dock(entity: LawnMowerEntity, service: ServiceCall) -> None:
    """Handle dock service."""
    await entity.async_dock()


async def async_service_pause(entity: LawnMowerEntity, service: ServiceCall) -> None:
    """Handle pause service."""
    await entity.async_pause()


async def async_service_enable_schedule(
    entity: LawnMowerEntity, service: ServiceCall
) -> None:
    """Handle enable schedule service."""
    kwargs = dict(service.data.items())
    await entity.async_enable_schedule(**kwargs)


async def async_service_disable_schedule(
    entity: LawnMowerEntity, service: ServiceCall
) -> None:
    """Handle disable schedule service."""
    kwargs = dict(service.data.items())
    await entity.async_disable_schedule(**kwargs)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up lawn mower devices."""
    component: EntityComponent[LawnMowerEntity] = hass.data[DOMAIN]
    return await component.async_setup_entry(entry)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    component: EntityComponent[LawnMowerEntity] = hass.data[DOMAIN]
    return await component.async_unload_entry(entry)
