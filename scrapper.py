#!/usr/bin/env python3

import re
import dbadmin

from urllib import request
from bs4 import BeautifulSoup as bs


URLFILE_SCI = 'course_listing_urls_sci.txt'
URLFILE_ART = 'course_listing_urls_arts.txt'
URLFILE_HAS = 'course_listing_urls_haskayne.txt'
TABLE_ID = re.compile('uofc-table-[0-9]{1,3}')
TABLE_CLASS = [['uofc-table'], ['uofc-table', 'has-details']]
RE_TIME = re.compile('(?P<days>[UMTWRFS]{1,3}) (?P<start>[0-9]{2}:[0-9]{2})'
                     '.*(?P<end>[0-9]{2}:[0-9]{2})')
RE_ROOM = re.compile('(?P<building>[A-Z]{2,4}).*(?P<room_num>[0-9]{3})')


class Scrapper():

    def __init__(self):
        self.dba = dbadmin.DBAdmin()
        self.dba.init_table()
        
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.dba.conn.close()

    def scrap(self, faculty_name, faculty_url, faculty_func):
        print('===============SCRAPPING {} COURSES==============='.format(faculty_name,))
        with open(faculty_url, 'r') as f:
           for line in [url.rstrip() for url in f]:
                print('\nScrapping course listings from:', line,
                      '\nRoom\t\tDays\tStart\tEnd')
                soup = bs(request.urlopen(line), 'html.parser')
                tables = soup.find_all(id=TABLE_ID)

                for table in tables:
                    if table['class'] in TABLE_CLASS:
                        for class_section in table.find_all('tr'):
                            if not class_section.find('div'):
                                faculty_func(list(class_section.children))
                                
         
    def _scrap_sci(self, tds):
        time = RE_TIME.search(tds[2].text)
        place = RE_ROOM.search(tds[3].text)
        if time and place:
            print('{}\t\t{}\t{}\t{}'
                  .format(place['building']+place['room_num'],
                          time['days'],
                          time['start'],
                          time['end']))
            self.dba.add_time(place['building']+place['room_num'],
                              time['days'],
                              time['start'],
                              time['end'])
            
    def _scrap_art(self, tds):
        time = RE_TIME.search(tds[5].text)
        place = RE_ROOM.search(tds[7].text)
        if time and place:
            print('{}\t\t{}\t{}\t{}'
                  .format(place['building']+place['room_num'],
                          time['days'],
                          time['start'],
                          time['end']))
            self.dba.add_time(place['building']+place['room_num'],
                              time['days'],
                              time['start'],
                              time['end'])

def main():
    with Scrapper() as scrapper:
        faculties = [('SCIENCE', URLFILE_SCI, scrapper._scrap_sci),
                     ('ARTS', URLFILE_ART, scrapper._scrap_art)]
        for faculty in faculties:
            scrapper.scrap(*faculty)

            
if __name__ == '__main__':
    main()
