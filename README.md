gdocsorganizer
==============

Organize tasks from iCAL feeds
This is a task I did for a job interview, basically reads an iCAL feed and creates a layout using Bootstrap with a couple of calculations.

The template system is really basic and straightforward, but I am sure it can 
help some people by providing real-world example of using iCAL python library.


Usage example:

````python
from fics import FeedICS

# Test
#feed = FeedICS('basic.ics')

feed = FeedICS('https://www.google.com/calendar/ical/xxxxxxxxxxxxxxxxxx/private-xxxxxxxxxxxxxxxx/basic.ics', 1)
feed.generate_html('clients.html', 'Bootstrap.html')
```
