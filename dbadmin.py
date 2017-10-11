import sqlite3

DAYS = {day:x for (x, day) in enumerate(['M', 'T', 'W', 'R', 'F', 'S', 'U'], start=1)}


def humanize_time(time):
    """Convert a time from the database's format to a human readable string.
       
       Args:
         time::Int - The time to convert.
       Returns:
         _::String - The converted time.
    """
    time_str = '{:04d}'.format(time, )
    if time_str[2:] == '25':
        return '{}:{}'.format(time_str[:2], 15)
    if time_str[2:] == '50':
        return '{}:{}'.format(time_str[:2], 30)
    if time_str[2:] == '75':
        return '{}:{}'.format(time_str[:2], 45)
    return '{}:{}'.format(time_str[:2], time_str[2:])


def dehumanize_time(time):
    """Convert a human readable time in 24h format to what the database needs.
    
       Args:
         time::String - The time to convert.
       Returns:
         _::Int - The converted time.
    """
    if time[3:] == '15':
        return int(time[:2] + '25')
    if time[3:] == '30':
        return int(time[:2] + '50')
    if time[3:] == '45':
        return int(time[:2] + '75')
    if time[3:] == '50':
        return int(time[:2]+time[3:])+50
    return int(time[:2] + '00')


def _consolidate_times(times):
    """Consolidates contiguous time intervals for a list of times.
       
       Args:
         times::[(Int, Int)] - The list of times to consolidate. Check the README
           for specifications on format.
       Returns:
         joined_times::[(Int, Int)] - A list of consolidated times.
    """    
    joined_times = []
    if not times: return joined_times
    start, end = times[0]
    for i in range(1, len(times)):
        if end != times[i][0]:
            joined_times.append((start, end))
            start, end = times[i]
        else:
            end = times[i][1]
    joined_times.append((start, end))
    return joined_times


class DBAdmin():

    def __init__(self):
        self.conn = sqlite3.connect('room_data.db')
        self.c = self.conn.cursor()

    @property
    def conn(self):
        return self.conn

    @property
    def c(self):
        return self.c
    
    def init_table(self):
        self.conn.execute('CREATE TABLE IF NOT EXISTS rooms('
                          'room TEXT NOT NULL, '
                          'day INT, '
                          'time INT, '
                          'taken INT DEFAULT 0)')

    def add_room(self, room):
        """Add a room to the database. Defaults all times as free.
    
           Args:
             room::String - The name of the room to add. Should be in the
                            format [A-Z]{2-3}[0-9]{2-3}, eg, MS160.
        """
        for i in range(0, 2400, 25):
            timeslots = [(room.upper(), d, i, 0) for d in range(1, 8)]
            self.c.executemany('INSERT INTO rooms VALUES (?,?,?,?)', (timeslots))
        self.conn.commit()

    def add_time(self, room, days, start, end):
        """Add a time a room is being used.

           Args:
             room::String - The name of the room to add.
             days::String - The days of the week the room is being used. 
               Weeks start on Monday.
             start::String - The time the room starts being used in 24 hour format.
               Only times in increments of 15 minutes from the hour are accepted.
             end::String - The time the room stops being used in 24 hour format.
               Only times in increments of 15 minutes from the hour are accepted.
        """
        if not self.c.execute('SELECT EXISTS (SELECT 1 FROM rooms '
                              'WHERE room="{}" LIMIT 1)'
                              .format(room,)).fetchone()[0]:
            self.add_room(room)
        dehu_start, dehu_end = dehumanize_time(start), dehumanize_time(end)
        for day in days:
            for i in range(dehu_start, dehu_end+1, 25):
                self.c.execute('UPDATE rooms SET taken = 1 WHERE '
                               'room = "{}" AND day = {} AND time = {}'
                               .format(room.upper(), DAYS[day], i))
        self.conn.commit()

    def check_room(self, room, day):
        """Returns the times a specific room is free for the day.
    
           Args:
             room::String - The name of the room to check.
             day::String - The day of the week the room is checked for.
           Returns:
             times::[(Int, Int)] - The time intervals the room is free.
        """
        times = []
        for time in self.c.execute('SELECT time FROM rooms WHERE room '
                                   '= "{}" AND day = {} AND taken = 0 ORDER BY time'
                                   .format(room.upper(), DAYS[day])):
            times.append((time[0], time[0]+25))
        return [(humanize_time(x), humanize_time(y)) for
                (x, y) in _consolidate_times(times)]

    def find_room(self, day, start=0, end=2400):
        """Returns the rooms that are available between start and end.

           Args:
             day::String - The day of the week the room must be free. Weeks start on Monday.
             start::String - The time the room starts being free used in 24 hour format.
               Only times in increments of 15 minutes from the hour are accepted.
             end::String - The time the room must be free until in 24 hour format.
               Only times in increments of 15 minutes from the hour are accepted.
           Returns:
             rooms_joined::{String:[(Int, Int)]} - A dictionary mapping rooms to the 
               times they are free to use.
        """
        rooms, rooms_joined = {}, {}
        dehu_start, dehu_end = dehumanize_time(start), dehumanize_time(end)
        for room, time in self.c.execute('SELECT room, time FROM rooms WHERE day = {} AND '
                                         'time >= {} AND time <= {} AND taken = 0 '
                                         'ORDER BY room, time'
                                         .format(DAYS[day], dehu_start, dehu_end)):
            if room not in rooms:
                rooms[room] = [(time, time+25)]
            else:
                rooms[room].append((time, time+25))

        for room, times in rooms.items():
            consolidated_times = _consolidate_times(times)
            for time_range in consolidated_times:
                if time_range[0] <= dehu_start and time_range[1] >= dehu_end:
                    rooms_joined[room] = consolidated_times
                    break
        return rooms_joined
