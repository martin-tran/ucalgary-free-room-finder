import re
import dbadmin

from urllib import request
from bs4 import BeautifulSoup as bs


URLFILE_SCI = 'course_listing_urls_sci.txt'
SCIENCE = ('unitis unitis-courses unitis-courses-course-listings collapsed '
           'odd attached-row details-row collapsed-detail-row')
TABLE_ID = re.compile('uofc-table-[0-9]{1,3}')
TABLE_CLASS = [['uofc-table'], ['uofc-table', 'has-details']]
RE_TIME = re.compile('(?P<days>[UMTWRFS]{1,3}) (?P<start>[0-9]{2}:[0-9]{2})'
                     '.*(?P<end>[0-9]{2}:[0-9]{2})')
RE_ROOM = re.compile('(?P<building>[A-Z]{2,4}).*(?P<room_num>[0-9]{3})')

def main():
    dba = dbadmin.DBAdmin()
    dba.init_table()
    with open(URLFILE_SCI, 'r') as f:
        for line in [url.rstrip() for url in f]:
            print('\nScrapping course listings from:', line,
                  '\nRoom\t\tDays\tStart\tEnd')
            soup = bs(request.urlopen(line), 'html.parser')
            tables = soup.find_all(id=TABLE_ID)

            for table in tables:
                if table['class'] in TABLE_CLASS:
                    for class_section in table.find_all('tr'):
                        if not class_section.find('div'):
                            tds = list(class_section.children)
                            time = RE_TIME.search(tds[2].text)
                            place = RE_ROOM.search(tds[3].text)
                            if time and place:
                                print('{}\t\t{}\t{}\t{}'
                                      .format(place['building']+place['room_num'],
                                              time['days'],
                                              time['start'],
                                              time['end']))
                                dba.add_time(place['building']+place['room_num'],
                                                 time['days'],
                                                 time['start'],
                                                 time['end'])
    dba.conn.close()

if __name__ == '__main__':
    main()
