"""Compact latest history for a standard Markdown dashboard card."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from .const import DOMAIN, SIGNAL


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([HistorySensor(hass.data[DOMAIN])])


class HistorySensor(SensorEntity):
    _attr_name = "Spülmaschine Verlauf"
    _attr_unique_id = "spuelmaschine_verlauf_history"
    _attr_icon = "mdi:dishwasher"
    _attr_should_poll = False

    def __init__(self, manager):
        self.manager = manager

    @property
    def native_value(self):
        return self.manager.snapshot['total']

    @property
    def extra_state_attributes(self):
        report = self.manager.snapshot
        return {'offener_spuelgang': report['open_id'], 'eintraege': report['entries'],
                'anzeige_limit': 30, 'speicherung': 'SQLite, unabhängig vom Recorder'}

    async def async_added_to_hass(self):
        self.async_on_remove(async_dispatcher_connect(self.hass, SIGNAL, self.async_write_ha_state))
