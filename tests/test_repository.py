import importlib.util
from pathlib import Path
import tempfile
import unittest

path = Path(__file__).resolve().parents[1] / 'custom_components/spuelmaschine_verlauf/repository.py'
spec = importlib.util.spec_from_file_location('repository', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
Repository = module.Repository


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'history.sqlite'
        self.repo = Repository(self.path)
        self.repo.initialize()

    def tearDown(self):
        self.tmp.cleanup()

    def test_initial_finished_is_baseline_not_invented_finish(self):
        self.assertFalse(self.repo.observe('finished', 'Paul', True)[1])
        self.assertEqual(self.repo.report()['total'], 0)

    def test_one_record_per_transition_and_persistent_restart_latch(self):
        self.repo.observe('running', 'Paul')
        first, created = self.repo.observe('finished', 'Paul')
        self.assertTrue(created)
        self.assertEqual(first['assigned_to'], 'Paul')
        reloaded = Repository(self.path)
        reloaded.initialize()
        self.assertFalse(reloaded.observe('finished', 'Paul', True)[1])
        reloaded.observe('unavailable', 'Paul')
        self.assertFalse(reloaded.observe('finished', 'Paul')[1])
        self.assertEqual(reloaded.report()['total'], 1)

    def test_new_cycle_preserves_unconfirmed_previous(self):
        first, _ = self.repo.record_finished('Paul', 'one')
        second, _ = self.repo.record_finished('Paul', 'two')
        report = self.repo.report()
        self.assertEqual(report['total'], 2)
        self.assertEqual(report['open_id'], second['id'])
        self.assertEqual(report['entries'][1]['status'], 'nicht_bestaetigt')
        self.assertIsNone(report['entries'][1]['emptied_at'])
        self.assertEqual(report['entries'][1]['emptied_by'], 'Vera/Manuel')
        self.assertIsNone(report['entries'][1]['waiting_minutes'])
        self.assertIsNone(report['entries'][0]['emptied_by'])
        self.assertEqual(report['entries'][0]['assigned_to'], 'Paul')
        with self.assertRaises(ValueError):
            self.repo.record_emptied(first['id'], 'Paul')

    def test_new_finish_after_restart_assigns_parent_fallback(self):
        self.repo.observe('running', 'Paul')
        first, _ = self.repo.observe('finished', 'Paul')
        reloaded = Repository(self.path)
        reloaded.initialize()
        reloaded.observe('running', 'Paul')
        second, created = reloaded.observe('finished', 'Paul')
        self.assertTrue(created)
        rows = reloaded.report()['entries']
        previous = next(r for r in rows if r['id'] == first['id'])
        self.assertEqual(previous['emptied_by'], 'Vera/Manuel')
        self.assertEqual(previous['status'], 'nicht_bestaetigt')
        self.assertIsNone(previous['emptied_at'])
        self.assertEqual(reloaded.report()['open_id'], second['id'])

    def test_new_cycle_does_not_overwrite_actual_confirmations(self):
        for index, person in enumerate(['Paul', 'Maximilian', 'Vera', 'Manuel']):
            assigned = person if person in ['Paul', 'Maximilian'] else 'Paul'
            cycle, _ = self.repo.record_finished(assigned, f'confirmed-{index}')
            confirmed, _ = self.repo.record_emptied(cycle['id'], person)
            self.repo.record_finished('Paul', f'next-{index}')
            row = next(r for r in self.repo.report()['entries'] if r['id'] == cycle['id'])
            self.assertEqual(row['emptied_by'], person)
            self.assertEqual(row['emptied_at'], confirmed['emptied_at'])
            self.assertEqual(row['status'], 'erledigt')

    def test_duplicate_finish_does_not_assign_parent_fallback(self):
        self.repo.observe('running', 'Paul')
        self.repo.observe('finished', 'Paul')
        self.repo.observe('unavailable', 'Paul')
        self.repo.observe('finished', 'Paul')
        report = self.repo.report()
        self.assertEqual(report['total'], 1)
        self.assertEqual(report['entries'][0]['status'], 'offen')
        self.assertIsNone(report['entries'][0]['emptied_by'])

    def test_manual_key_is_idempotent_and_does_not_close_current_cycle(self):
        first, _ = self.repo.record_finished('Paul', 'one')
        second, _ = self.repo.record_finished('Paul', 'two')
        repeat, changed = self.repo.record_finished('Maximilian', 'one')
        self.assertFalse(changed)
        self.assertEqual(repeat['id'], first['id'])
        self.assertEqual(self.repo.report()['open_id'], second['id'])

    def test_confirmation_and_duplicate_confirmation_survive_restart(self):
        cycle, _ = self.repo.record_finished('Paul', 'one')
        done, changed = self.repo.record_emptied(cycle['id'], 'Paul')
        self.assertTrue(changed)
        self.assertEqual(done['status'], 'erledigt')
        self.assertIsNotNone(done['emptied_at'])
        reloaded = Repository(self.path)
        repeated, changed = reloaded.record_emptied(cycle['id'], 'Paul')
        self.assertFalse(changed)
        self.assertEqual(done['emptied_at'], repeated['emptied_at'])
        self.assertIsNone(reloaded.report()['open_id'])

    def test_wrong_child_and_unknown_person_cannot_confirm(self):
        cycle, _ = self.repo.record_finished('Paul', 'one')
        for person in ['Maximilian', 'Gast']:
            with self.assertRaises(ValueError):
                self.repo.record_emptied(cycle['id'], person)
        self.assertEqual(self.repo.report()['entries'][0]['status'], 'offen')

    def test_parent_confirmation_records_parent(self):
        for person in ['Vera', 'Manuel']:
            cycle, _ = self.repo.record_finished('Paul', person)
            row, changed = self.repo.record_emptied(cycle['id'], person)
            self.assertTrue(changed)
            self.assertEqual(row['assigned_to'], 'Paul')
            self.assertEqual(row['emptied_by'], person)

    def test_offline_finished_is_flagged_as_observed_time(self):
        self.repo.observe('running', 'Paul')
        row, changed = Repository(self.path).observe('finished', 'Paul', startup=True)
        self.assertTrue(changed)
        self.assertTrue(row['observed_after_restart'])

    def test_bad_duty_rolls_back_state_and_can_retry(self):
        self.repo.observe('running', 'Paul')
        with self.assertRaises(ValueError):
            self.repo.observe('finished', 'unavailable')
        self.assertEqual(self.repo.report()['total'], 0)
        self.assertTrue(self.repo.observe('finished', 'Paul')[1])

    def test_report_pagination_and_retains_all_records(self):
        for i in range(45):
            self.repo.record_finished('Paul', str(i))
        page = self.repo.report(30)
        self.assertEqual(page['total'], 45)
        self.assertEqual(len(page['entries']), 30)
        self.assertEqual(len(self.repo.report(30, 30)['entries']), 15)

    def test_monthly_statistics_include_all_records_and_merge_parents(self):
        for i in range(36):
            cycle, _ = self.repo.record_finished('Paul', str(i))
            person = ['Paul', 'Vera', 'Manuel'][i % 3]
            self.repo.record_emptied(cycle['id'], person)
        report = self.repo.report(1)
        self.assertEqual(len(report['entries']), 1)
        stats = report['statistics'][0]
        self.assertEqual(stats['total'], 36)
        self.assertEqual(stats['people'], {'Paul': 12, 'Maximilian': 0, 'Vera / Manuel': 24})
        self.assertEqual(stats['assumed'], 0)

    def test_statistics_month_uses_local_emptying_time_and_keeps_year(self):
        for key, stamp in [('one', '2025-12-31T23:30:00+00:00'), ('two', '2026-12-31T23:30:00+00:00')]:
            cycle, _ = self.repo.record_finished('Paul', key)
            self.repo.record_emptied(cycle['id'], 'Paul')
            with self.repo.connect() as db:
                db.execute('UPDATE cycles SET emptied_at=? WHERE id=?', (stamp, cycle['id']))
        stats = self.repo.report(30, 0, 'Europe/Berlin')['statistics']
        self.assertEqual([m['month'] for m in stats], ['2027-01', '2026-01'])
        self.assertTrue(all(m['total'] == 1 for m in stats))

    def test_statistics_flag_assumed_and_exclude_open_cycle(self):
        old, _ = self.repo.record_finished('Paul', 'old')
        with self.repo.connect() as db:
            db.execute('UPDATE cycles SET finished_at=? WHERE id=?', ('2026-10-12T10:00:00+00:00', old['id']))
        self.repo.record_finished('Paul', 'new')
        stats = self.repo.report()['statistics']
        self.assertEqual(len(stats), 1)
        self.assertEqual(stats[0]['month'], '2026-10')
        self.assertEqual(stats[0]['total'], 1)
        self.assertEqual(stats[0]['assumed'], 1)
        self.assertEqual(stats[0]['people']['Vera / Manuel'], 1)


if __name__ == '__main__':
    unittest.main()
