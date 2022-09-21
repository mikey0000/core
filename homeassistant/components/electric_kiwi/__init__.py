"""The Electric Kiwi integration."""

from datetime import datetime as dt
import logging

import aiohttp
from homeassistant import config_entries
from homeassistant.components.application_credentials import (
    ClientCredential,
    async_import_client_credential,
)
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    Platform,
)
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    ConfigEntryNotReady,
    HomeAssistantError,
)
from .api import ApiAuthImpl, get_feature_access
from .const import CONF_TOKEN_EXPIRY, DOMAIN

_LOGGER = logging.getLogger(__name__)

CONF_ID_TOKEN = "id_token"

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Electric Kiwi from a config entry."""
    hass.data.setdefault(DOMAIN, {})


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

    if not async_entry_has_scopes(hass, entry):
        raise ConfigEntryAuthFailed(
            "Required scopes are not available, reauth required"
        )

    """assign the electric kiwi api with session here"""
    hass.data[DOMAIN][entry.entry_id] = {}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok



def async_entry_has_scopes(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Verify that the config entry desired scope is present in the oauth token."""
    access = get_feature_access(hass, entry)
    token_scopes = entry.data.get("token", {}).get("scope", [])
    return access.scope in token_scopes

