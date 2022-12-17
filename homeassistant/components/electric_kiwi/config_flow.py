"""Config flow for Electric Kiwi."""
import logging
from typing import Any

from homeassistant.helpers import config_entry_oauth2_flow

from .const import DOMAIN


class ElectricKiwiOauth2FlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Config flow to handle Electric Kiwi OAuth2 authentication."""

    DOMAIN = DOMAIN

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return logging.getLogger(__name__)

    @property
    def extra_authorize_data(self) -> dict[str, Any]:
        """Extra data that needs to be appended to the authorize url."""
        return {
            "scope": "read_connection_detail read_billing_frequency "
            "read_account_running_balance read_consumption_summary read_consumption_averages "
            "read_hop_intervals_config read_hop_connection save_hop_connection read_session"
        }
