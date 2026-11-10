"""Persistent dishwasher history, deliberately without notifications or duty changes."""
import asyncio
import logging
from pathlib import Path
from homeassistant.components import frontend
from homeassistant.components.http import StaticPathConfig
import voluptuous as vol
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED, Platform
from homeassistant.core import CoreState, SupportsResponse, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_state_change_event
from .const import DOMAIN, SIGNAL
from .repository import Repository, CHILDREN, PEOPLE

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SENSOR]


async def async_setup(hass, config):
    await hass.http.async_register_static_paths([StaticPathConfig(
        '/spuelmaschine-verlauf',
        str(Path(__file__).parent / 'frontend'), False)])
    frontend.add_extra_js_url(hass, '/spuelmaschine-verlauf/card.js?v=0.4.2')
    async def service(call):
        manager = hass.data.get(DOMAIN)
        if manager is None:
            raise ServiceValidationError("Die Integration Spülmaschine Verlauf ist nicht geladen.")
        if call.service == "get_history":
            return await manager.report(call.data.get('limit', 100), call.data.get('offset', 0))
        if call.service == "record_finished":
            return await manager.finish(call.data['cycle_key'])
        return await manager.empty(call.data['cycle_id'], call.data['person'])

    hass.services.async_register(DOMAIN, 'record_finished', service,
        schema=vol.Schema({vol.Required('cycle_key'): vol.All(cv.string, vol.Length(min=1, max=200))}),
        supports_response=SupportsResponse.OPTIONAL)
    hass.services.async_register(DOMAIN, 'record_emptied', service,
        schema=vol.Schema({vol.Required('cycle_id'): cv.string,
                           vol.Required('person'): vol.In(sorted(PEOPLE))}),
        supports_response=SupportsResponse.OPTIONAL)
    hass.services.async_register(DOMAIN, 'get_history', service,
        schema=vol.Schema({vol.Optional('limit', default=100): vol.All(vol.Coerce(int), vol.Range(min=1, max=1000)),
                           vol.Optional('offset', default=0): vol.All(vol.Coerce(int), vol.Range(min=0))}),
        supports_response=SupportsResponse.ONLY)
    return True


async def async_setup_entry(hass, entry):
    manager = Manager(hass, entry)
    await hass.async_add_executor_job(manager.repo.initialize)
    await manager.refresh()
    hass.data[DOMAIN] = manager
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    @callback
    def changed(event):
        state = event.data.get('new_state')
        old = event.data.get('old_state')
        if state is not None and (old is None or old.state != state.state):
            entry.async_create_background_task(hass, manager.observe(state.state), 'Spülmaschinenstatus speichern')

    async def started(event=None):
        async with manager.lock:
            state = hass.states.get(entry.data['source'])
            if state:
                await manager.observe_locked(state.state, startup=True)
            # Register after startup snapshot to avoid racing startup baseline.
            entry.async_on_unload(async_track_state_change_event(hass, [entry.data['source']], changed))

    if hass.state == CoreState.running:
        await started()
    else:
        entry.async_on_unload(hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, started))
    return True


async def async_unload_entry(hass, entry):
    if await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data.pop(DOMAIN, None)
        return True
    return False


class Manager:
    def __init__(self, hass, entry):
        self.hass = hass
        self.entry = entry
        self.repo = Repository(hass.config.path('spuelmaschine_verlauf.sqlite'))
        self.lock = asyncio.Lock()
        self.snapshot = {'total': 0, 'open_id': None, 'entries': []}

    def duty(self):
        state = self.hass.states.get(self.entry.data['duty'])
        value = state.state if state else ''
        return value

    async def refresh(self):
        self.snapshot = await self.hass.async_add_executor_job(self.repo.report, 30, 0, self.hass.config.time_zone)
        async_dispatcher_send(self.hass, SIGNAL)

    async def observe(self, state):
        async with self.lock:
            await self.observe_locked(state)

    async def observe_locked(self, state, startup=False):
        try:
            record, created = await self.hass.async_add_executor_job(self.repo.observe, state, self.duty(), startup)
            if created:
                await self.refresh()
                self.hass.bus.async_fire(f'{DOMAIN}_finished', record)
        except Exception as err:
            # Automatic observations must not fail silently. Keeping previous
            # persisted source state allows a later observation to retry.
            _LOGGER.error('Spülmaschinenverlauf konnte Status nicht speichern: %s', err)

    async def finish(self, cycle_key):
        async with self.lock:
            try:
                record, changed = await self.hass.async_add_executor_job(self.repo.record_finished, self.duty(), cycle_key)
            except (ValueError, OSError) as err:
                raise ServiceValidationError(str(err)) from err
            await self.refresh()
            if changed:
                self.hass.bus.async_fire(f'{DOMAIN}_finished', record)
            return {'entry': record, 'created': changed}

    async def empty(self, cycle_id, person):
        async with self.lock:
            try:
                record, changed = await self.hass.async_add_executor_job(self.repo.record_emptied, cycle_id, person)
            except (ValueError, OSError) as err:
                raise ServiceValidationError(str(err)) from err
            await self.refresh()
            if changed:
                self.hass.bus.async_fire(f'{DOMAIN}_emptied', record)
            return {'entry': record, 'changed': changed}

    async def report(self, limit, offset):
        async with self.lock:
            return await self.hass.async_add_executor_job(self.repo.report, limit, offset, self.hass.config.time_zone)
