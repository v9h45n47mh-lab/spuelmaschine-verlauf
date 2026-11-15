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
from .family_access import allows, register
from .const import DOMAIN, SIGNAL
from .repository import Repository, CHILDREN, PEOPLE

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SENSOR]


async def authorize_empty(hass, context_user_id, actor_user_id, person):
    """Resolve the authenticated caller; trusted device automations may supply identity."""
    uid = context_user_id or actor_user_id
    user = await hass.auth.async_get_user(uid) if uid else None
    if not uid:
        matches = [u for u in await hass.auth.async_get_users()
                   if u.is_active and not u.system_generated and (u.name or '').strip().split(' ')[0].casefold() == person.casefold()]
        if len(matches) != 1:
            raise ServiceValidationError('Der Ausräumer benötigt eine eindeutige HA-Kontozuordnung.')
        user = matches[0]
    if not user or not user.is_active or user.system_generated or (user.name or '').strip().split(' ')[0].casefold() != person.casefold():
        raise ServiceValidationError('Du kannst nicht für einen anderen Benutzer bestätigen.')
    override = allows(hass, user, DOMAIN, 'confirm_any', person in {'Vera', 'Manuel'})
    if not override and not allows(hass, user, DOMAIN, 'confirm_own', person in PEOPLE, audit=True):
        raise ServiceValidationError('Ausräumen ist für deine Rolle nicht freigegeben.')
    return override


async def async_setup(hass, config):
    await hass.http.async_register_static_paths([StaticPathConfig(
        '/spuelmaschine-verlauf',
        str(Path(__file__).parent / 'frontend'), False)])
    frontend.add_extra_js_url(hass, '/spuelmaschine-verlauf/card.js?v=0.5.0')
    async def service(call):
        manager = hass.data.get(DOMAIN)
        if manager is None:
            raise ServiceValidationError("Die Integration Spülmaschine Verlauf ist nicht geladen.")
        uid=call.context.user_id or call.data.get('actor_user_id')
        user=await hass.auth.async_get_user(uid) if uid else None
        if uid and (not user or not user.is_active or user.system_generated):raise ServiceValidationError('Keine gültige Anmeldung.')
        if call.service == 'get_history' and user and not allows(hass,user,DOMAIN,'view',True,audit=True):raise ServiceValidationError('Verlauf ist für deine Rolle nicht freigegeben.')
        if call.service == 'record_finished' and user and not allows(hass,user,DOMAIN,'manage',user.is_admin,audit=True):raise ServiceValidationError('Spülgänge erfassen ist für deine Rolle nicht freigegeben.')
        if call.service == "get_history":
            return await manager.report(call.data.get('limit', 100), call.data.get('offset', 0))
        if call.service == "record_finished":
            return await manager.finish(call.data['cycle_key'])
        person=call.data['person']
        override=await authorize_empty(hass, call.context.user_id, call.data.get('actor_user_id'), person)
        return await manager.empty(call.data['cycle_id'], person, override)

    hass.services.async_register(DOMAIN, 'record_finished', service,
        schema=vol.Schema({vol.Required('cycle_key'): vol.All(cv.string, vol.Length(min=1, max=200))}),
        supports_response=SupportsResponse.OPTIONAL)
    hass.services.async_register(DOMAIN, 'record_emptied', service,
        schema=vol.Schema({vol.Required('cycle_id'): cv.string,
                           vol.Required('person'): vol.In(sorted(PEOPLE)), vol.Optional('actor_user_id'): cv.string}),
        supports_response=SupportsResponse.OPTIONAL)
    hass.services.async_register(DOMAIN, 'get_history', service,
        schema=vol.Schema({vol.Optional('limit', default=100): vol.All(vol.Coerce(int), vol.Range(min=1, max=1000)),
                           vol.Optional('offset', default=0): vol.All(vol.Coerce(int), vol.Range(min=0))}),
        supports_response=SupportsResponse.ONLY)
    return True


async def async_setup_entry(hass, entry):
    await register(hass,DOMAIN,('view','confirm_own','confirm_any','manage','statistics'),lambda u:{'view':True,'confirm_own':(u.name or '').strip().split(' ')[0] in PEOPLE,'confirm_any':(u.name or '').strip() in {'Vera','Manuel'},'manage':u.is_admin,'statistics':(u.name or '').strip().split(' ')[0].casefold() in {'vera','manuel'}}, entry=entry)
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

    async def empty(self, cycle_id, person, override=False):
        async with self.lock:
            if not override and self.duty() != person:
                raise ServiceValidationError('Du bist aktuell nicht für das Ausräumen eingeteilt.')
            try:
                record, changed = await self.hass.async_add_executor_job(self.repo.record_emptied, cycle_id, person, override)
            except (ValueError, OSError) as err:
                raise ServiceValidationError(str(err)) from err
            await self.refresh()
            if changed:
                self.hass.bus.async_fire(f'{DOMAIN}_emptied', record)
            return {'entry': record, 'changed': changed}

    async def report(self, limit, offset):
        async with self.lock:
            return await self.hass.async_add_executor_job(self.repo.report, limit, offset, self.hass.config.time_zone)
