"""UI configuration of a single history instance."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from .const import DOMAIN, SOURCE, DUTY


class HistoryConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        if user_input is not None:
            return self.async_create_entry(title="Spülmaschine Verlauf", data=user_input)
        return self.async_show_form(step_id="user", data_schema=vol.Schema({
            vol.Required("source", default=SOURCE): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")),
            vol.Required("duty", default=DUTY): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="input_select")),
        }))
