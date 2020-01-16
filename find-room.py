#!/usr/bin/env python3

import argparse
import os
from src import dbadmin
from src import scrapper

from datetime import date

DAYS = {x:day for (x, day) in enumerate(['M', 'T', 'W', 'R', 'F', 'S', 'U'], start=1)}
URLFILE_SCI = 'data/course_listing_urls_sci.txt'
URLFILE_ART = 'data/course_listing_urls_arts.txt'
URLFILE_HAS = 'data/course_listing_urls_haskayne.txt'
dir_path = os.path.dirname(os.path.realpath(__file__))

parser = argparse.ArgumentParser()
action = parser.add_mutually_exclusive_group()
parser.add_argument('-U', '--update', help='scrap the department websites\' '+
                    'course listings to update the database', action='store_true')
parser.add_argument('-R', '--remove', help='remove the current database if it exists',
                    action='store_true')
action.add_argument('-f', '--find', help='find a free room given the time and day',
                    action='store_true')
action.add_argument('-c', '--check', help='check if a specific room is free ' +
                    'an interval', action='store_true')
parser.add_argument('-s', '--start_time', help='the start of the time the room ' +
                    'must be free', default='00:00')
parser.add_argument('-e', '--end_time', help='the end of the time the room ' +
                    'must be free', default='24:00')
parser.add_argument('-d', '--days', help='the days to search for input as a '+
                    'single string in the format [MTWRFSU]',
                    default=DAYS[date.today().isoweekday()])
parser.add_argument('-r', '--room', help='the room name to query in the format ' +
                    '[A-Z]{2,4}[0-9]{3}')
args = parser.parse_args()


def main():
    admin = dbadmin.DBAdmin()

    if args.remove:
        if os.path.isfile('room_data.db'):
            confirm = input('Are you sure you want to remove the database? (y/n) ')
            if confirm == 'y':
                os.remove('room_data.db')
        else:
            print('No database found.')

    if args.update:
        confirm = input('This operation could take very long. '
                        'Are you sure you want to update the database? (y/n) ')
        if confirm == 'y':
            with scrapper.Scrapper() as a_scrapper:
                faculties = [('SCIENCE', URLFILE_SCI, a_scrapper._scrap_sci),
                             ('HASKAYNE', URLFILE_HAS, a_scrapper._scrap_haskayne)]
                """
                faculties = [('SCIENCE', URLFILE_SCI, a_scrapper._scrap_sci),
                             ('ARTS', URLFILE_ART, a_scrapper._scrap_art),
                             ('HASKAYNE', URLFILE_HAS, a_scrapper._scrap_haskayne)]
                """
                for faculty in faculties:
                    a_scrapper.scrap(*faculty)

    if args.find:
        for day in args.days:
            for k, v in admin.find_room(args.days,
                                        args.start_time,
                                        args.end_time).items():
                print('{}: {}-{}'.format(k, v[0][0], v[0][1]))

    if args.check:
        for day in args.days:
            print(admin.check_room(args.room, day))


if __name__ == '__main__':
    main()
