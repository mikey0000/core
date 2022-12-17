"""Support for Electric Kiwi account balance."""
from datetime import timedelta
import logging

import async_timeout
from electrickiwi_api import ElectricKiwiApi
from electrickiwi_api.model import AccountBalance

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ATTRIBUTION, ATTR_FRIENDLY_NAME, CURRENCY_DOLLAR
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import Throttle

from .const import ATTRIBUTION, DOMAIN

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(hours=24)

FRIENDLY_NAME = "Electric Kiwi Account Balance"


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Electric Kiwi Sensor Setup."""
    api: ElectricKiwiApi = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([ElectricKiwiBalanceSensor(api)], True)


class ElectricKiwiBalanceSensor(SensorEntity):
    """Entity object for Electric Kiwi sensor."""

    _attr_native_unit_of_measurement = f"{CURRENCY_DOLLAR}"

    def __init__(self, api: ElectricKiwiApi) -> None:
        """Entity object for Electric Kiwi sensor."""
        self._api: ElectricKiwiApi = api
        self._balance: AccountBalance = None
        self._attributes = {
            ATTR_ATTRIBUTION: ATTRIBUTION,
            ATTR_FRIENDLY_NAME: FRIENDLY_NAME,
        }

    @property
    def name(self):
        """Return the name of the sensor."""
        return FRIENDLY_NAME

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._balance.total_running_balance

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    @Throttle(SCAN_INTERVAL)
    async def async_update(self):
        """Get the Electric Kiwi Account Balance data from the web service."""
        async with async_timeout.timeout(60):
            self._balance = await self._api.get_account_balance()

        _LOGGER.debug("Pricing data: %s", self._balance.total_running_balance)
