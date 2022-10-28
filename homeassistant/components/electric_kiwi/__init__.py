"""The Electric Kiwi integration."""
from __future__ import annotations

from typing import Any

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client, config_entry_oauth2_flow
from electrickiwi_api import ElectricKiwiApi

from . import api
from .const import DOMAIN
from ...exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Electric Kiwi from a config entry."""
    implementation = (
        await config_entry_oauth2_flow.async_get_config_entry_implementation(
            hass, entry
        )
    )

    session = config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation)

    try:
        await session.async_ensure_token_valid()
    except aiohttp.ClientResponseError as err:
        if 400 <= err.status < 500:
            raise ConfigEntryAuthFailed from err
        raise ConfigEntryNotReady from err
    except aiohttp.ClientError as err:
        raise ConfigEntryNotReady from err

    # if not async_entry_has_scopes(hass, entry):
    #     raise ConfigEntryAuthFailed(
    #         "Required scopes are not available, reauth required"
    #     )

    # If using an aiohttp-based API lib
    hass.data[DOMAIN][entry.entry_id] = ElectricKiwiApi(api.AsyncConfigEntryAuth(
        aiohttp_client.async_get_clientsession(hass), session
    )).set_active_session()
    # we need to set the client number and connection id

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
