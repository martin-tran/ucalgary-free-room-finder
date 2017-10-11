import unittest
import scrapper

from unittest.mock import call
from unittest.mock import patch
from bs4 import BeautifulSoup as bs


class TestScrapper(unittest.TestCase):
    
    def setUp(self):
        with open('sci_sample.txt', 'r') as f:
            sci_sample = f.read()
        self.sci_soup = bs(sci_sample, 'html.parser')

        with open('art_sample.txt', 'r') as f:
            art_sample = f.read()
        self.art_soup = bs(art_sample, 'html.parser')
    
    def testRegex(self):
        self.assertIsNone(scrapper.TABLE_ID.search(''))
        self.assertIsNone(scrapper.TABLE_ID.search('uofa-table-1'))
        self.assertIsNone(scrapper.TABLE_ID.search('uofc-table'))
        self.assertIsNotNone(scrapper.TABLE_ID.search('uofc-table-0'))

        self.assertIsNone(scrapper.RE_TIME.search(''))
        self.assertIsNone(scrapper.RE_TIME.search('ABC 12:34-23:53'))
        self.assertIsNone(scrapper.RE_TIME.search('MWF 0:0-24:00'))
        re_time_match = scrapper.RE_TIME.search('TR 13:00 - 15:00')
        self.assertIsNotNone(re_time_match)
        self.assertDictEqual(re_time_match.groupdict(),
                             {'days':'TR', 'start':'13:00', 'end':'15:00'})

        self.assertIsNone(scrapper.RE_ROOM.search(''))
        self.assertIsNone(scrapper.RE_ROOM.search('MS ONESIXTY'))
        self.assertIsNone(scrapper.RE_ROOM.search('07 160'))
        re_room_match = scrapper.RE_ROOM.search('MS 160')
        self.assertIsNotNone(re_room_match)
        self.assertDictEqual(re_room_match.groupdict(),
                             {'building':'MS', 'room_num':'160'})

    @patch('scrapper.dbadmin.DBAdmin')
    def testScrapSci(self, *unused_args):
        test_scrapper = scrapper.Scrapper()
        sci_cls = self.sci_soup.find_all(id=scrapper.TABLE_ID)[0].find_all('tr')

        test_scrapper._scrap_sci(list(sci_cls[0].children))
        test_scrapper._scrap_sci(list(sci_cls[1].children))
        test_scrapper._scrap_sci(list(sci_cls[2].children))        

        calls = [call('KNB126', 'TR', '15:30', '16:45'),
                 call('MS156', 'TR', '10:00', '10:50'),
                 call('MS156', 'TR', '12:00', '12:50')]
        test_scrapper.dba.add_time.assert_has_calls(calls)

    @patch('scrapper.dbadmin.DBAdmin')
    def testScrapArt(self, *unused_args):
        test_scrapper = scrapper.Scrapper()
        art_cls = self.art_soup.find_all(id=scrapper.TABLE_ID)[0].find_all('tr')

        test_scrapper._scrap_art(list(art_cls[0].children))
        test_scrapper._scrap_art(list(art_cls[1].children))

        calls = [call('TRA102', 'T', '14:00', '15:50'),
                 call('TRA102', 'R', '14:00', '15:50')]
        test_scrapper.dba.add_time.assert_has_calls(calls)


if __name__ == '__main__':
    unittest.main()
