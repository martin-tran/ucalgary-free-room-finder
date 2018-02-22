import unittest
from src import dbadmin

from unittest.mock import call
from unittest.mock import patch
from unittest.mock import PropertyMock

class TestDBAdmin(unittest.TestCase):
    
    def testHumanizeTime(self):
        self.assertEqual(dbadmin.humanize_time(0), '00:00')
        self.assertEqual(dbadmin.humanize_time(100), '01:00')
        self.assertEqual(dbadmin.humanize_time(525), '05:15')
        self.assertEqual(dbadmin.humanize_time(1050), '10:30')
        self.assertEqual(dbadmin.humanize_time(1200), '12:00')
        self.assertEqual(dbadmin.humanize_time(2275), '22:45')
        self.assertEqual(dbadmin.humanize_time(2400), '24:00')

    def testDehumanizeTime(self):
        self.assertEqual(dbadmin.dehumanize_time('00:00'), 0)
        self.assertEqual(dbadmin.dehumanize_time('01:00'), 100)
        self.assertEqual(dbadmin.dehumanize_time('05:15'), 525)
        self.assertEqual(dbadmin.dehumanize_time('08:50'), 900)
        self.assertEqual(dbadmin.dehumanize_time('10:30'), 1050)
        self.assertEqual(dbadmin.dehumanize_time('12:00'), 1200)
        self.assertEqual(dbadmin.dehumanize_time('22:45'), 2275)
        self.assertEqual(dbadmin.dehumanize_time('24:00'), 2400)

    def testConsolidateTimes(self):
        self.assertListEqual(dbadmin.consolidate_times([]), [])
        self.assertListEqual(dbadmin.consolidate_times([(0, 25),
                                                         (25, 50),
                                                         (50, 75),
                                                         (75, 100)]),
                             [(0, 100)])
        self.assertListEqual(dbadmin.consolidate_times([(0, 25),
                                                         (50, 75),
                                                         (100, 125)]),
                             [(0, 25), (50, 75), (100, 125)])
        self.assertListEqual(dbadmin.consolidate_times([(0,25),
                                                         (25, 50),
                                                         (75,100),
                                                         (100, 125)]),
                             [(0, 50), (75, 125)])

    @patch('dbadmin.DBAdmin.conn', new_callable=PropertyMock)
    @patch('dbadmin.DBAdmin.c', new_callable=PropertyMock)
    def testAddRoom(self, *unused_args):
        dba = dbadmin.DBAdmin()
        dba.add_room('MS160')
        dba.c.executemany.assert_called()
        dba.conn.commit.assert_called_once()

    @patch('dbadmin.DBAdmin.add_room')
    @patch('dbadmin.DBAdmin.conn', new_callable=PropertyMock)
    @patch('dbadmin.DBAdmin.c', new_callable=PropertyMock)
    def testAddTime(self, *unused_args):
        dba = dbadmin.DBAdmin()
        dba.add_time('MS160', 'M', '10:00', '10:50')
        calls = [call('UPDATE rooms SET taken = 1 WHERE room = "MS160" '
                       'AND day = 1 AND time = 1000'),
                 call('UPDATE rooms SET taken = 1 WHERE room = "MS160" '
                       'AND day = 1 AND time = 1025'),
                 call('UPDATE rooms SET taken = 1 WHERE room = "MS160" '
                       'AND day = 1 AND time = 1050'),
                 call('UPDATE rooms SET taken = 1 WHERE room = "MS160" '
                       'AND day = 1 AND time = 1075')]
        dba.c.execute.assert_has_calls(calls)
        dba.add_room.assert_not_called()
        
    @patch('dbadmin.DBAdmin.conn', new_callable=PropertyMock)
    @patch('dbadmin.DBAdmin.c', new_callable=PropertyMock)
    def testCheckRoom(self, *unused_args):
        dba = dbadmin.DBAdmin()
        dba.c.execute.return_value = []
        self.assertEqual(dba.check_room('MS160', 'M'), [])
        dba.c.execute.return_value = [(0, 25), (25, 50), (50, 75), (75, 100)]
        self.assertEqual(dba.check_room('MS160', 'M'), [('00:00', '01:00')])
        dba.c.execute.return_value = [(0, 25), (25, 50), (75, 100), (100, 125)]
        self.assertEqual(dba.check_room('MS160', 'M'),
                         [('00:00', '00:30'), ('00:45', '01:15')])
        dba.c.execute.return_value = [(0, 25), (50, 75), (100, 125)]
        self.assertEqual(dba.check_room('MS160', 'M'),
                         [('00:00', '00:15'), ('00:30', '00:45'), ('01:00', '01:15')])

    @patch('dbadmin.DBAdmin.conn', new_callable=PropertyMock)
    @patch('dbadmin.DBAdmin.c', new_callable=PropertyMock)
    def testFindRoom(self, *unused_args):
        dba = dbadmin.DBAdmin()
        dba.c.execute.return_value = []
        self.assertEqual(dba.find_room('M', '00:00', '00:15'), {})
        dba.c.execute.return_value = [('MS160', 0), ('MS160', 25), ('MS160', 50)]
        self.assertEqual(dba.find_room('M', '00:00', '00:15'), {'MS160':[(0, 75)]})
        dba.c.execute.return_value = [('MS160', 0), ('MS160', 25), ('MS160', 50)]
        self.assertEqual(dba.find_room('M', '00:00'), {})
        dba.c.execute.return_value = [('MS160', 0), ('MS160', 25), ('MS160', 50)]
        self.assertEqual(dba.find_room('M', end='24:00'), {})


if __name__ == '__main__':
    unittest.main()
