"""Support for Electric Kiwi account balance."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

import async_timeout
from electrickiwi_api import ElectricKiwiApi
from electrickiwi_api.exceptions import ApiException
from electrickiwi_api.model import AccountBalance

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ATTRIBUTION, CURRENCY_DOLLAR, PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import Throttle

from .const import (
    ATTR_HOP_PERCENTAGE,
    ATTR_NEXT_BILLING_DATE,
    ATTR_TOTAL_CURRENT_BALANCE,
    ATTR_TOTAL_RUNNING_BALANCE,
    ATTRIBUTION,
    DOMAIN,
    NAME,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(hours=6)


@dataclass
class ElectricKiwiRequiredKeysMixin:
    """Mixin for required keys."""

    value_func: Callable[[AccountBalance], str | datetime | None]


@dataclass
class ElectricKiwiSensorEntityDescription(
    SensorEntityDescription, ElectricKiwiRequiredKeysMixin
):
    """Describes Electric Kiwi sensor entity."""


SENSOR_TYPES: tuple[ElectricKiwiSensorEntityDescription, ...] = (
    ElectricKiwiSensorEntityDescription(
        key=ATTR_TOTAL_RUNNING_BALANCE,
        name=f"{NAME} total running balance",
        icon="mdi:currency-usd",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=CURRENCY_DOLLAR,
        value_func=lambda account_balance: account_balance.total_running_balance,
    ),
    ElectricKiwiSensorEntityDescription(
        key=ATTR_TOTAL_CURRENT_BALANCE,
        name=f"{NAME} total current balance",
        icon="mdi:currency-usd",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=CURRENCY_DOLLAR,
        value_func=lambda account_balance: account_balance.total_account_balance,
    ),
    ElectricKiwiSensorEntityDescription(
        key=ATTR_NEXT_BILLING_DATE,
        name=f"{NAME} next billing date",
        icon="mdi:calendar",
        device_class=SensorDeviceClass.DATE,
        value_func=lambda account_balance: datetime.strptime(
            account_balance.next_billing_date, "%Y-%m-%d"
        ),
    ),
    ElectricKiwiSensorEntityDescription(
        key=ATTR_HOP_PERCENTAGE,
        name=f"{NAME} Hour of Power savings",
        icon="",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_func=lambda account_balance: account_balance.connections[
            0
        ].hop_percentage,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Electric Kiwi Sensor Setup."""
    api: ElectricKiwiApi = hass.data[DOMAIN][entry.entry_id]
    account_api = ElectricKiwiAccountData(api, SCAN_INTERVAL)
    await account_api.async_update()

    entities = [
        ElectricKiwiAccountSensor(account_api, description)
        for description in SENSOR_TYPES
    ]
    async_add_entities(entities)


class ElectricKiwiAccountSensor(SensorEntity):
    """Entity object for Electric Kiwi sensor."""

    entity_description: ElectricKiwiSensorEntityDescription

    def __init__(
        self,
        api: ElectricKiwiAccountData,
        description: ElectricKiwiSensorEntityDescription,
    ) -> None:
        """Entity object for Electric Kiwi sensor."""
        self._api: ElectricKiwiAccountData = api
        self._balance: AccountBalance
        self.entity_description = description
        self._attributes = {
            ATTR_ATTRIBUTION: ATTRIBUTION,
        }

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"{self._api.customer_number}_{self._api.connection_id}_{self.entity_description.key}"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"{self.entity_description.name}"

    @property
    def native_value(self) -> datetime | str | None:
        """Return the state of the sensor."""
        return self.entity_description.value_func(self._api.balance)

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Return the state attributes."""
        return self._attributes

    async def async_update(self) -> None:
        """Get the Electric Kiwi Account Balance data from the web service."""
        await self._api.throttled_update()

        _LOGGER.debug("Account data from sensor: %s", self._api.balance)


class ElectricKiwiAccountData:
    """ElectricKiwi Data object."""

    def __init__(self, api, interval) -> None:
        """wrap the api so it can be shared across entities without making multiple calls."""
        self._api = api
        self.customer_number = api.customer_number
        self.connection_id = api.connection_id
        self.throttled_update = Throttle(interval)(self.async_update)
        self.balance = AccountBalance
        self.balance.total_account_balance = "0"
        self.balance.total_running_balance = "0"

    async def async_update(self) -> None:
        """Async update to get the balances."""
        async with async_timeout.timeout(60):
            try:
                self.balance = await self._api.get_account_balance()
            except ApiException as err:
                _LOGGER.error("Error updating account balance entities: %s", err)
            _LOGGER.debug("Account data: %s", self.balance)
