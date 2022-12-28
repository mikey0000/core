"""Test the Electric Kiwi config flow."""

from unittest.mock import patch

import pytest

from homeassistant import config_entries
from homeassistant.components.application_credentials import (
    ClientCredential,
    async_import_client_credential,
)
from homeassistant.components.electric_kiwi.const import (
    DOMAIN,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.setup import async_setup_component

CLIENT_ID = "1234"
CLIENT_SECRET = "5678"
REDIRECT_URI = "https://example.com/auth/external/callback"
SCOPES = "read_connection_detail+read_billing_frequency+read_account_running_balance+read_consumption_summary+read_consumption_averages+read_hop_intervals_config+read_hop_connection+save_hop_connection+read_session"


@pytest.fixture(autouse=True)
async def request_setup(current_request_with_host) -> None:
    """Request setup."""
    return


@pytest.fixture(autouse=True)
async def setup_app_creds(hass: HomeAssistant) -> None:
    """Fixture to setup application credentials component."""
    await async_setup_component(hass, "application_credentials", {})


@pytest.fixture
async def setup_credentials(hass: HomeAssistant) -> None:
    """Fixture to setup credentials."""
    assert await async_setup_component(hass, "application_credentials", {})
    await async_import_client_credential(
        hass,
        DOMAIN,
        ClientCredential(CLIENT_ID, CLIENT_SECRET),
    )


async def test_config_flow_no_credentials(hass):
    """Test config flow base case with no credentials registered."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result.get("type") == FlowResultType.ABORT
    assert result.get("reason") == "missing_credentials"


async def test_full_flow(
    hass: HomeAssistant, hass_client_no_auth, aioclient_mock
) -> None:
    """Check full flow."""
    await async_import_client_credential(
        hass, DOMAIN, ClientCredential(CLIENT_ID, CLIENT_SECRET), "imported-cred"
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": REDIRECT_URI,
        },
    )

    print(result)
    assert result["url"] == (
        f"{OAUTH2_AUTHORIZE}?response_type=code&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&state={state}"
        f"&scope={SCOPES}"
    )

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == 200
    assert resp.headers["content-type"] == "text/html; charset=utf-8"

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    with patch(
        "homeassistant.components.electric_kiwi.async_setup_entry", return_value=True
    ) as mock_setup:
        await hass.config_entries.flow.async_configure(result["flow_id"])

    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    assert len(mock_setup.mock_calls) == 1
