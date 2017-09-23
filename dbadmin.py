import sqlite3


conn = sqlite3.connect('room_data.db')
c = conn.cursor()


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
    return int(time[:2] + '00')


def add_room(room):
    """Add a room to the database. Defaults all times as free.
    
       Args:
         room::String - The name of the room to add. Should be in the
                        format [A-Z]{2-3}[0-9]{2-3}, eg, MS160.
    """
    for i in range(0, 2400, 25):
        timeslots = [(room.upper(), d, i, 0) for d in range(7)]
        c.executemany('INSERT INTO rooms VALUES (?,?,?,?)', (timeslots))
    conn.commit()

def add_time(room, day, start, end):
    """Add a time a room is being used.

       Args:
         room::String - The name of the room to add.
         day::Int - The day of the week the room is being used. Weeks start on Sunday.
         start::Int - The time the room starts being used. Check the README for 
           details on the format.
         end::Int - The time the room is done being used.  Check the README for 
           details on the format.
    """
    for i in range(start, end, 25):
        c.execute('''UPDATE rooms SET taken = 1 WHERE 
                     room = "{}" AND day = {} AND time = {}'''
                  .format(room.upper(), day, i))
    conn.commit()
    
def check_room(room, day):
    """Returns the times a specific room is free for the day.
    
       Args:
         room::String - The name of the room to check.
         day::Int - The day of the week the room is checked for.
       Returns:
         times::[(Int, Int)] - The time intervals the room is free.
    """
    times = []
    for time in c.execute('''SELECT time FROM rooms WHERE room = "{}" AND day = {} AND
                             taken = 0 ORDER BY time'''.format(room.upper(), day)):
        times.append((time[0], time[0]+25))
    return _consolidate_times(times)


def find_room(day, start=0, end=2400):
    """Returns the rooms that are fully or partially available between start and end.

       Args:
         day::Int - The day of the week the room must be free. Weeks start on Sunday.
         start::Int - The start time to search for a free room. Check the README for 
           details on the format.
         end::Int - The end time to search for a free room. Check the README for 
           details on the format.
       Returns:
         rooms_joined::{String:[(Int, Int)]} - A dictionary mapping rooms to the 
           times they are free to use.
    """
    rooms, rooms_joined = {}, {}
    for room, time in c.execute('''SELECT room, time FROM rooms WHERE day = {} AND
                                   time >= {} AND time <= {} AND taken = 0
                                   ORDER BY room, time'''
                                .format(day, start, end)):
        if room not in rooms:
            rooms[room] = [(time, time+25)]
        else:
            rooms[room].append((time, time+25))

    for room, times in rooms.items():
        rooms_joined[room] = _consolidate_times(times)
        
    return rooms_joined


def _consolidate_times(times):
    """Consolidates contiguous time intervals for a list of times.
       
       Args:
         times::[(Int, Int)] - The list of times to consolidate. Check the README
           for specifications on format.
       Returns:
         joined_times::[(Int, Int)] - A list of consolidated times.
    """    
    joined_times = []
    start, end = times[0]
    for i in range(1, len(times)):
        if end != times[i][0]:
            joined_times.append((start, end))
            start, end = times[i]
        else:
            end = times[i][1]
    joined_times.append((start, end))
    return joined_times

