"""The tests for Electric Kiwi sensors."""

from datetime import timezone
from unittest.mock import AsyncMock, Mock, patch

from freezegun import freeze_time
import pytest

from homeassistant.components.electric_kiwi import (
    ACCOUNT_COORDINATOR,
    DOMAIN,
    HOP_COORDINATOR,
    ElectricKiwiAccountDataCoordinator,
    ElectricKiwiHOPDataCoordinator,
)
from homeassistant.components.electric_kiwi.const import ATTRIBUTION
from homeassistant.components.electric_kiwi.sensor import (
    ACCOUNT_SENSOR_TYPES,
    ElectricKiwiAccountSensorEntityDescription,
    _check_and_move_time,
)
from homeassistant.components.sensor import (
    ATTR_STATE_CLASS,
    SensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import ATTR_ATTRIBUTION, ATTR_DEVICE_CLASS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import EntityRegistry
import homeassistant.util.dt as dt_util

from .conftest import TIMEZONE

from tests.common import MockConfigEntry


@pytest.mark.parametrize(
    ("sensor", "sensor_state"),
    [
        ("sensor.hour_of_free_power_start", "4:00 PM"),
        ("sensor.hour_of_free_power_end", "5:00 PM"),
    ],
)
async def test_hop_sensors(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    ek_api: AsyncMock,
    entity_registry: EntityRegistry,
    sensor,
    sensor_state,
) -> None:
    """Test HOP sensors for the Electric Kiwi integration."""

    with patch(
        "homeassistant.helpers.config_entry_oauth2_flow.async_get_config_entry_implementation",
        return_value=AsyncMock(),
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        entries = hass.config_entries.async_entries(DOMAIN)
        assert entries[0].state is ConfigEntryState.LOADED

        hop_coordinator: ElectricKiwiHOPDataCoordinator = hass.data[DOMAIN][
            config_entry.entry_id
        ][HOP_COORDINATOR]
        assert hop_coordinator
        entry = entity_registry.async_get(sensor)
        assert entry

        state = hass.states.get(sensor)
        assert state
        value = _check_and_move_time(hop_coordinator.data, sensor_state)
        if value.tzinfo != timezone.utc:
            value = value.astimezone(timezone.utc)
        assert state.state == value.isoformat(timespec="seconds")
        assert state.attributes.get(ATTR_ATTRIBUTION) == ATTRIBUTION
        assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.TIMESTAMP


async def test_check_and_move_time(ek_api: AsyncMock) -> None:
    """Test correct time is returned for the hop time depending on time of day."""
    hop = await ek_api(Mock()).get_hop()

    test_time = dt_util.now(TIMEZONE).replace(
        hour=18, minute=0, second=0, day=21, month=6, year=2023
    )
    dt_util.set_default_time_zone(TIMEZONE)

    with freeze_time(test_time):
        value = _check_and_move_time(hop, "4:00 PM")
        assert str(value) == "2023-06-22 16:00:00+12:00"

    test_time = dt_util.now(TIMEZONE).replace(
        hour=10, minute=0, second=0, day=21, month=6, year=2023
    )

    with freeze_time(test_time):
        value = _check_and_move_time(hop, "4:00 PM")
        assert str(value) == "2023-06-21 16:00:00+12:00"


@pytest.mark.parametrize(
    ("sensor", "sensor_state"),
    [
        ("sensor.total_running_balance", "184.09"),
        ("sensor.total_current_balance", "-102.22"),
        ("sensor.next_billing_date", "2020-11-03T00:00:00"),
        ("sensor.hour_of_power_savings", "3.5"),
    ],
)
async def test_account_sensors(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    ek_api: AsyncMock,
    entity_registry: EntityRegistry,
    sensor,
    sensor_state,
) -> None:
    """Test Account sensors for the Electric Kiwi integration."""

    with patch(
        "homeassistant.helpers.config_entry_oauth2_flow.async_get_config_entry_implementation",
        return_value=AsyncMock(),
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        entries = hass.config_entries.async_entries(DOMAIN)
        assert entries[0].state is ConfigEntryState.LOADED

        account_coordinator: ElectricKiwiAccountDataCoordinator = hass.data[DOMAIN][
            config_entry.entry_id
        ][ACCOUNT_COORDINATOR]
        assert account_coordinator
        entry = entity_registry.async_get(sensor)
        assert entry

        AccountSensors = list(
            filter(lambda x: entry.unique_id.endswith(x.key), ACCOUNT_SENSOR_TYPES)
        )
        AccountSensor: ElectricKiwiAccountSensorEntityDescription = AccountSensors[0]
        assert AccountSensor

        state = hass.states.get(sensor)
        assert state
        assert state.state == sensor_state
        assert state.attributes.get(ATTR_ATTRIBUTION) == ATTRIBUTION
        assert state.attributes.get(ATTR_DEVICE_CLASS) == AccountSensor.device_class
        assert state.attributes.get(ATTR_STATE_CLASS) == AccountSensor.state_class
