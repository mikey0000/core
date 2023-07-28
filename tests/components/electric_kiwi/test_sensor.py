"""The tests for Electric Kiwi sensors."""

from datetime import timezone
from unittest.mock import AsyncMock, patch

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
    HOP_SENSOR_TYPES,
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
        value = _check_and_move_time(hop_coordinator.data, sensor_state)
        if value.tzinfo != timezone.utc:
            value = value.astimezone(timezone.utc)
        assert state.state == value.isoformat(timespec="seconds")
        assert state.attributes.get(ATTR_ATTRIBUTION) == ATTRIBUTION
        assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.TIMESTAMP

        HOPSensors = list(
            filter(lambda x: entry.unique_id.endswith(x.key), HOP_SENSOR_TYPES)
        )
        HOPSensor: ElectricKiwiAccountSensorEntityDescription = HOPSensors[0]
        assert HOPSensor


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
        assert state.state == sensor_state
        assert state.attributes.get(ATTR_ATTRIBUTION) == ATTRIBUTION
        assert state.attributes.get(ATTR_DEVICE_CLASS) == AccountSensor.device_class
        assert state.attributes.get(ATTR_STATE_CLASS) == AccountSensor.state_class
