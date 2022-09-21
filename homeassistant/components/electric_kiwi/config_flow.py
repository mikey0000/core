"""Config Flow for Flick Electric integration."""
import asyncio
import logging

import async_timeout
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    DEVICE_AUTH_CREDS,
    AccessTokenAuthImpl,
    DeviceAuth,
    DeviceFlow,
    OAuthError,
    async_create_device_flow,
    get_feature_access,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_CLIENT_ID): str,
        vol.Optional(CONF_CLIENT_SECRET): str,
    }
)


class OAuth2FlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Config flow to handle Google Calendars OAuth2 authentication."""

    DOMAIN = DOMAIN

    def __init__(self) -> None:
        """Set up instance."""
        super().__init__()
        self._reauth_config_entry: config_entries.ConfigEntry | None = None
        self._device_flow: DeviceFlow | None = None

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return logging.getLogger(__name__)

    async def async_step_import(self, info: dict[str, Any]) -> FlowResult:
        """Import existing auth into a new config entry."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        implementations = await config_entry_oauth2_flow.async_get_implementations(
            self.hass, self.DOMAIN
        )
        assert len(implementations) == 1
        self.flow_impl = list(implementations.values())[0]
        self.external_data = info
        return await super().async_step_creation(info)


