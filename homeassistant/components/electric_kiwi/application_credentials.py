"""application_credentials platform the Electric Kiwi integration."""

from homeassistant.components.application_credentials import AuthorizationServer
from .const import OAUTH2_AUTHORIZE, OAUTH2_TOKEN
from homeassistant.core import HomeAssistant


async def async_get_authorization_server(hass: HomeAssistant) -> AuthorizationServer:
    """Return authorization server."""
    return AuthorizationServer(
        authorize_url=OAUTH2_AUTHORIZE,
        token_url=OAUTH2_TOKEN,
    )

async def async_get_description_placeholders(hass: HomeAssistant) -> dict[str, str]:
    """Return description placeholders for the credentials dialog."""
    return {
        "more_info_url": "https://www.home-assistant.io/integrations/electric_kiwi/"
    }

