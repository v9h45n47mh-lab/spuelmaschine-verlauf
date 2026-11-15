"""Exercise the shipped YAML templates against the real SQLite repository.

Test dependencies: PyYAML and Jinja2 (not runtime integration dependencies).
This is not a replacement for a live Home Assistant automation test.
"""
from pathlib import Path
import tempfile
import ast
import asyncio
import importlib.util
from types import SimpleNamespace as NS
import unittest
import yaml
from jinja2.nativetypes import NativeEnvironment
from test_repository import Repository


class BlueprintLoader(yaml.SafeLoader):
    pass


BlueprintLoader.add_constructor('!input', lambda loader, node: ('input', loader.construct_scalar(node)))
BLUEPRINT = yaml.load((Path(__file__).resolve().parents[1] /
    'blueprints/automation/spuelmaschine_nfc.yaml').read_text(), Loader=BlueprintLoader)


class NfcTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Repository(Path(self.tmp.name) / 'history.sqlite')
        self.repo.initialize()
        self.duty = 'Paul'
        self.devices = dict(manuel_device='manuel-phone', vera_device='vera-phone',
                            maximilian_device='max-phone', paul_device='paul-phone')
        self.env = NativeEnvironment()
        self.env.globals['states'] = lambda entity: self.duty
        self.env.globals['state_attr'] = self.attr
        self.switches = 0
        users = {name.lower(): NS(id=name.lower(), name=name, is_admin=False, is_active=True, system_generated=False) for name in ['Manuel','Vera','Maximilian','Paul']}
        async def get_user(uid): return users.get(uid)
        async def get_users(): return list(users.values())
        self.users=users
        self.hass=NS(data={},auth=NS(async_get_user=get_user,async_get_users=get_users))
        spec=importlib.util.spec_from_file_location('permission_client',Path(__file__).resolve().parents[1]/'custom_components/spuelmaschine_verlauf/family_access.py')
        client=importlib.util.module_from_spec(spec);spec.loader.exec_module(client)
        source=ast.parse((Path(__file__).resolve().parents[1]/'custom_components/spuelmaschine_verlauf/__init__.py').read_text())
        helper=next(n for n in source.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='authorize_empty')
        ns={'allows':client.allows,'DOMAIN':'spuelmaschine_verlauf','PEOPLE':set(users[n].name for n in users),'ServiceValidationError':ValueError}
        exec(compile(ast.Module(body=[helper],type_ignores=[]),'<shipped actor check>','exec'),ns)
        self.authorize=ns['authorize_empty']

    def attr(self, entity, attr):
        report = self.repo.report()
        return report['open_id' if attr == 'offener_spuelgang' else 'entries']

    def render(self, template, ctx):
        value = self.env.from_string(template).render(**ctx)
        if isinstance(value, str):
            value = value.strip()
            if value in ['True', 'False', 'None']:
                return ast.literal_eval(value)
        return value

    def scan(self, device):
        steps = BLUEPRINT['actions']
        ctx = dict(self.devices, history_entity='sensor.history', duty_entity='input_select.duty',
                   trigger={'event': {'data': {'device_id': device}, 'context': {'user_id': None}}})
        for name, template in steps[1]['variables'].items():
            ctx[name] = self.render(template, ctx)
        for step in steps[2:4]:
            if not self.render(step['value_template'], ctx):
                return False
        data = {key: self.render(value, ctx) for key, value in steps[4]['data'].items()}
        try:
            override=asyncio.run(self.authorize(self.hass,None,data.pop('actor_user_id') or None,data['person']))
            if not override and self.duty!=data['person']:return False
            _, changed = self.repo.record_emptied(**data,override_duty=override)
        except ValueError:return False
        ctx['result'] = {'changed': changed}
        if self.render(steps[5]['if'][0]['value_template'], ctx):
            self.duty = self.render(steps[5]['then'][0]['data']['option'], ctx)
            self.switches += 1
        return changed

    def test_child_scan_records_immediately_and_switches_once(self):
        self.repo.record_finished('Paul', 'one')
        self.assertTrue(self.scan('paul-phone'))
        self.assertEqual(self.duty, 'Maximilian')
        self.assertFalse(self.scan('paul-phone'))
        self.assertFalse(self.scan('max-phone'))
        self.assertEqual(self.switches, 1)
        row = self.repo.report()['entries'][0]
        self.assertEqual(row['emptied_by'], 'Paul')
        self.assertIsNotNone(row['emptied_at'])
        self.repo.record_finished('Maximilian', 'two')
        self.assertTrue(self.scan('max-phone'))
        self.assertEqual(self.duty, 'Paul')

    def test_parents_always_allowed_without_duty_change(self):
        for assigned in ['Paul', 'Maximilian']:
            self.duty = assigned
            for name in ['vera', 'manuel']:
                self.repo.record_finished(assigned, assigned + name)
                self.assertTrue(self.scan(name + '-phone'))
                self.assertEqual(self.duty, assigned)
                self.assertEqual(self.repo.report()['entries'][0]['emptied_by'], name.title())
        self.assertEqual(self.switches, 0)

    def test_unknown_and_wrong_child_are_ignored(self):
        self.repo.record_finished('Paul', 'one')
        for device in ['stranger', 'max-phone', None, '']:
            self.assertFalse(self.scan(device))
        self.assertIsNotNone(self.repo.report()['open_id'])
        self.assertEqual(self.switches, 0)

    def test_no_open_cycle_is_noop_for_everyone(self):
        for device in self.devices.values():
            self.assertFalse(self.scan(device))
        self.assertEqual(self.repo.report()['total'], 0)

    def test_current_duty_and_recorded_assignment_must_both_match(self):
        self.repo.record_finished('Paul', 'one')
        self.duty = 'Maximilian'
        self.assertFalse(self.scan('paul-phone'))
        self.assertFalse(self.scan('max-phone'))
        self.assertTrue(self.scan('vera-phone'))
        self.assertEqual(self.duty, 'Maximilian')

    def test_ambiguous_device_mapping_is_rejected(self):
        self.repo.record_finished('Paul', 'one')
        self.devices['vera_device'] = 'paul-phone'
        self.assertFalse(self.scan('paul-phone'))
        self.assertIsNotNone(self.repo.report()['open_id'])

    def test_central_role_override_and_revocation(self):
        grants={'confirm_own':True}
        self.hass.data['family_access_manager']=NS(application_protocol=1,application_permissions=lambda user,app:dict(grants))
        self.repo.record_finished('Paul','one')
        self.assertFalse(self.scan('max-phone'))
        grants['confirm_any']=True
        self.assertTrue(self.scan('max-phone'))
        self.repo.record_finished('Paul','two')
        grants.clear()
        self.assertFalse(self.scan('paul-phone'))
        self.assertFalse(self.scan('vera-phone'))

    def test_device_identity_supports_unique_full_account_names(self):
        self.users['paul'].name='Paul Wagner'
        self.repo.record_finished('Paul','one')
        self.assertTrue(self.scan('paul-phone'))

    def test_authenticated_person_cannot_be_forged(self):
        with self.assertRaises(ValueError):
            asyncio.run(self.authorize(self.hass,'paul','vera','Vera'))
        self.users['paul'].is_active=False
        with self.assertRaises(ValueError):
            asyncio.run(self.authorize(self.hass,'paul',None,'Paul'))

    def test_queue_reads_variables_in_actions_without_wait_or_notify(self):
        self.assertEqual(BLUEPRINT['mode'], 'queued')
        self.assertNotIn('variables', BLUEPRINT)
        text = str(BLUEPRINT['actions'])
        self.assertNotIn('notify.', text)
        self.assertNotIn('wait_for_trigger', text)
        self.assertEqual(BLUEPRINT['triggers'][0]['event_type'], 'tag_scanned')


if __name__ == '__main__':
    unittest.main()
