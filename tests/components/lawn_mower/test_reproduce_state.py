"""The tests for reproduction of state."""

import pytest

from homeassistant.components.lawn_mower import (
    DOMAIN,
    SERVICE_DISABLE_SCHEDULE,
    SERVICE_DOCK,
    SERVICE_ENABLE_SCHEDULE,
    SERVICE_PAUSE,
    SERVICE_START_MOWING,
    LawnMowerActivity,
)
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.state import async_reproduce_state

from tests.common import async_mock_service

ENTITY = "lawn_mower.test"


@pytest.mark.parametrize(
    ("service", "next_service", "activity", "next_activity"),
    [
        (
            SERVICE_DISABLE_SCHEDULE,
            SERVICE_ENABLE_SCHEDULE,
            LawnMowerActivity.DOCKED_SCHEDULE_DISABLED,
            LawnMowerActivity.DOCKED_SCHEDULE_ENABLED,
        ),
        (
            SERVICE_ENABLE_SCHEDULE,
            SERVICE_DISABLE_SCHEDULE,
            LawnMowerActivity.DOCKED_SCHEDULE_ENABLED,
            LawnMowerActivity.DOCKED_SCHEDULE_DISABLED,
        ),
        (
            SERVICE_DOCK,
            SERVICE_START_MOWING,
            LawnMowerActivity.DOCKED_SCHEDULE_ENABLED,
            LawnMowerActivity.MOWING,
        ),
        (
            SERVICE_PAUSE,
            SERVICE_START_MOWING,
            LawnMowerActivity.PAUSED,
            LawnMowerActivity.MOWING,
        ),
        (
            SERVICE_START_MOWING,
            SERVICE_PAUSE,
            LawnMowerActivity.MOWING,
            LawnMowerActivity.PAUSED,
        ),
    ],
)
async def test_reproducing_states(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
    service,
    next_service,
    activity: LawnMowerActivity,
    next_activity: LawnMowerActivity,
) -> None:
    """Test reproducing mower states."""
    hass.states.async_set(ENTITY, activity)

    calls = async_mock_service(hass, DOMAIN, service)
    next_calls = async_mock_service(hass, DOMAIN, next_service)

    await async_reproduce_state(hass, [State(ENTITY, activity)])

    assert len(calls) == 0
    # Test invalid state is handled
    await async_reproduce_state(hass, [State(ENTITY, "not_supported")])

    assert "not_supported" in caplog.text
    assert len(calls) == 0

    await async_reproduce_state(hass, [State(ENTITY, next_activity)])

    assert len(next_calls) == 1
    assert next_calls[0].domain == "lawn_mower"
    assert next_calls[0].data == {"entity_id": ENTITY}
