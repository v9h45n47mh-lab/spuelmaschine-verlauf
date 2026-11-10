"""Exercise the shipped YAML templates against the real SQLite repository.

Test dependencies: PyYAML and Jinja2 (not runtime integration dependencies).
This is not a replacement for a live Home Assistant automation test.
"""
from pathlib import Path
import tempfile
import ast
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
                   trigger={'event': {'data': {'device_id': device}}})
        for name, template in steps[1]['variables'].items():
            ctx[name] = self.render(template, ctx)
        for step in steps[2:4]:
            if not self.render(step['value_template'], ctx):
                return False
        data = {key: self.render(value, ctx) for key, value in steps[4]['data'].items()}
        _, changed = self.repo.record_emptied(**data)
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

    def test_queue_reads_variables_in_actions_without_wait_or_notify(self):
        self.assertEqual(BLUEPRINT['mode'], 'queued')
        self.assertNotIn('variables', BLUEPRINT)
        text = str(BLUEPRINT['actions'])
        self.assertNotIn('notify.', text)
        self.assertNotIn('wait_for_trigger', text)
        self.assertEqual(BLUEPRINT['triggers'][0]['event_type'], 'tag_scanned')


if __name__ == '__main__':
    unittest.main()
