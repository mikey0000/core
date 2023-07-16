"""Reproduce a lawn mower state."""
from __future__ import annotations

import asyncio
from collections.abc import Iterable
import logging
from typing import Any

from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import Context, HomeAssistant, State

from . import (
    DOMAIN,
    SERVICE_DISABLE_SCHEDULE,
    SERVICE_DOCK,
    SERVICE_ENABLE_SCHEDULE,
    SERVICE_PAUSE,
    SERVICE_START_MOWING,
    LawnMowerActivity,
)

_LOGGER = logging.getLogger(__name__)

ACTIVITIES = {item.value for item in LawnMowerActivity}


async def _async_reproduce_state(
    hass: HomeAssistant,
    state: State,
    *,
    context: Context | None = None,
    reproduce_options: dict[str, Any] | None = None,
) -> None:
    """Reproduce a single state."""
    if (cur_state := hass.states.get(state.entity_id)) is None:
        _LOGGER.warning("Unable to find entity %s", state.entity_id)
        return

    if state.state not in ACTIVITIES:
        _LOGGER.warning(
            "Invalid state specified for %s: %s", state.entity_id, state.state
        )
        return

    # Return if we are already at the right state.
    if cur_state.state == state.state:
        return

    service_data = {ATTR_ENTITY_ID: state.entity_id}

    if state.state == LawnMowerActivity.DOCKED_SCHEDULE_DISABLED:
        service = SERVICE_DISABLE_SCHEDULE
    elif state.state == LawnMowerActivity.DOCKED_SCHEDULE_ENABLED:
        service = SERVICE_ENABLE_SCHEDULE
    elif state.state == LawnMowerActivity.DOCKING:
        service = SERVICE_DOCK
    elif state.state == LawnMowerActivity.MOWING:
        service = SERVICE_START_MOWING
    elif state.state == LawnMowerActivity.PAUSED:
        service = SERVICE_PAUSE

    await hass.services.async_call(
        DOMAIN, service, service_data, context=context, blocking=True
    )


async def async_reproduce_states(
    hass: HomeAssistant,
    states: Iterable[State],
    *,
    context: Context | None = None,
    reproduce_options: dict[str, Any] | None = None,
) -> None:
    """Reproduce Lawn Mower states."""
    await asyncio.gather(
        *(
            _async_reproduce_state(
                hass, state, context=context, reproduce_options=reproduce_options
            )
            for state in states
        )
    )
