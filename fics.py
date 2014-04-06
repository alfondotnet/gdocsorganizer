from icalendar import Calendar, Event, vDatetime, vPeriod
import operator
from datetime import datetime, date, timedelta
from wheezy.template.engine import Engine
from wheezy.template.ext.core import CoreExtension
from wheezy.template.loader import FileLoader
import urllib

from time import sleep

# https://github.com/collective/icalendar with full suport of timezones
# datetimes ISO 8601


class FeedICS:
    
    def __init__(self, file, http_link=0):
        
        self.clients_hours = dict()
        self.total_hours_unbooked = 0
        self.total_hours_booked = 0
        self.calendar = None
        
        self.morning_starts = (9,0)
        self.morning_ends = (13,0)
        
        self.afternoon_starts = (13,30)
        self.afternoon_ends = (17,30)
        
        self.lunch_time = (self.morning_ends,self.afternoon_starts)
        
        ''' Bookings dictionary:
            Key: gregorian date of the day of the booking
            Value: Dictionary of intervals
                
                Intervals dictionary:
                Key: Start datetime
                Value: (End datetime, client)
        '''
        self.bookings = dict() 
        
        now = datetime.now()
        self.last_booking_date = date(now.year,now.month,now.day)
        
        self.read_ics_file(file, http_link)
        
    
    def read_ics_file(self, file, http_link=0):
        
        if http_link:
            f = urllib.urlopen(file)
        else:
            f = open(file, 'rb')
            
        try:
            self.calendar = Calendar.from_ical(f.read())
            self.get_parameters()
        
        finally:
            if http_link == 0:
                f.close()
                
    
    def get_parameters(self):

        for component in self.calendar.walk('vevent'):
    
            client = component.get('summary')
            
            if client:
                            
                start = vDatetime.from_ical(component.get('dtstart').to_ical())
                end = vDatetime.from_ical(component.get('dtend').to_ical())
                
                hours = (end-start).seconds // 3600  # end - start is a timedelta
                
                # We only store day month and year to after index them nicely
                booking_key = date(start.year,start.month,start.day)
                
                if booking_key > self.last_booking_date:
                    self.last_booking_date = booking_key
                
                # Update the bookings dictionary
                
                if booking_key in self.bookings:
                    self.bookings[booking_key][start] = (end,client)
                else:
                    self.bookings[booking_key] = {start : (end,client)}
                
                # Update the clients_hours dictionary 
                
                if client in self.clients_hours:
                    self.clients_hours[client] += hours
                else:
                    self.clients_hours[client] = hours
                    
                self.total_hours_booked += hours
                


    def get_unbooked_hours(self):
        
        datetime_now = datetime.now()
        date_now = date(datetime_now.year,datetime_now.month,datetime_now.day)
        list_unbooked_intervals = list()
        current_date = date_now
        
        while True:
            
            # We do not consider weekends 
            if current_date.weekday() in [5,6]:
                current_date += timedelta(days=1)
                continue
              
            unbooked_intervals_day = list()
            
            if current_date in self.bookings:
                # In a current day, we iterate over its bookings
                
                current_hour = self.morning_starts
                
                for b in sorted(self.bookings[current_date]):
                    
                    b_start = b.hour, b.minute
                    
                    if (b_start[0] - current_hour[0]) + (b_start[1] - current_hour[1]) > 0:
                                                
                        interval_start = datetime(current_date.year, current_date.month, current_date.day,current_hour[0],current_hour[1],0) 
                        interval_end = datetime(current_date.year, current_date.month, current_date.day,b_start[0],b_start[1],0)    
                                
                        if ((interval_start.hour,interval_start.minute),(interval_end.hour,interval_end.minute)) != self.lunch_time:
                            # We don't take into account lunch time
                            unbooked_intervals_day.append((interval_start,interval_end))
                            
                            self.total_hours_unbooked += (interval_end - interval_start).seconds // 3600
                    
                    current_hour = (self.bookings[current_date][b][0].hour,self.bookings[current_date][b][0].minute) # datatime of the booking end
                
                else:
                    
                    # Consider the end of the day
                    
                    if (self.afternoon_ends[0] - current_hour[0]) + (self.afternoon_ends[1] - current_hour[1]) > 0:
                        
                        interval_start = datetime(current_date.year, current_date.month, current_date.day,current_hour[0],current_hour[1],0) 
                        interval_end = datetime(current_date.year, current_date.month, current_date.day,self.afternoon_ends[0],self.afternoon_ends[1],0)    
                    
                        unbooked_intervals_day.append((interval_start,interval_end))
                        self.total_hours_unbooked += (interval_end - interval_start).seconds // 3600 
                
            else:
                
                # If we have an entire day unbooked 
                
                # Morning
                m_start = datetime(current_date.year, current_date.month, current_date.day,self.morning_starts[0],self.morning_starts[1],0) 
                m_end = datetime(current_date.year, current_date.month, current_date.day,self.morning_ends[0],self.morning_ends[1],0) 
                
                # Afternoon
                a_start = datetime(current_date.year, current_date.month, current_date.day,self.afternoon_starts[0],self.afternoon_starts[1],0)    
                a_end = datetime(current_date.year, current_date.month, current_date.day,self.afternoon_ends[0],self.afternoon_ends[1],0)    
                        
                unbooked_intervals_day.append((m_start,m_end))
                unbooked_intervals_day.append((a_start,a_end))
                 
                self.total_hours_unbooked += 8
                    
            list_unbooked_intervals.extend(unbooked_intervals_day)
            
            if current_date == self.last_booking_date:
                break    
            
            current_date += timedelta(days=1) 
               
        return list_unbooked_intervals  
                    
            
                
    def generate_html(self, filename, template_file="Default.html"):
        
        engine = Engine(
            loader=FileLoader(['templates']),
            extensions=[CoreExtension()]
            )
        
        template = engine.get_template(template_file)
        
        try:
            file = open(filename, "w")
            try:

                clients_list_descendant = list(reversed(sorted(self.clients_hours.items(), key=lambda x: x[1])))
                file.write(template.render({'clients_hours':clients_list_descendant,
                                            'total_hours':str(self.total_hours_booked),
                                            'unbooked_timeranges':self.get_unbooked_hours(),
                                            'total_hours_unbooked': self.total_hours_unbooked}))
            finally:
                file.close()
        except IOError:
            pass
        
        