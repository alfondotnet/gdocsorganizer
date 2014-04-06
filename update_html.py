from fics import FeedICS

#feed = FeedICS('basic.ics')

feed = FeedICS('https://www.google.com/calendar/ical/jh9vj9npns3jke9qf1atbe1afg%40group.calendar.google.com/private-a61b99c934a5cd5604d1a28022d920cb/basic.ics', 1)

feed.generate_html('clients.html', 'Bootstrap.html')