import json
import math
import random
import re
import caldav
from datetime import datetime
from decimal import getcontext
from string import digits, ascii_uppercase

decCtx = getcontext()
decCtx.prec = 7  # 5.2 digits, max=99999.99
charset = digits + ascii_uppercase

paramRE = re.compile(r"\${(\w*?)}")


def expTitel(tour):
    return tour.getTitel()


def expDesc(tour):
    # desc = "<html><body>" + tour.getKurzbeschreibung() + "\nKategorie: " + tour.getKategorie() + "\nGeeignet für: " + \
    #        tour.getRadTyp() + "\n" + "\n".join(tour.getZusatzInfo()) + "\nSchwierigkeitsgrad: " + \
    #        ["unbekannt", "sehr einfach", "einfach", "mittel", "schwer", "sehr schwer"][tour.getSchwierigkeit()] + \
    #        "\n<a href=\"" + tour.getFrontendLink() + "\"Link</a></body></html>"
    desc = tour.getKurzbeschreibung() + "\nKategorie: " + tour.getKategorie() + "\nGeeignet für: " + \
           tour.getRadTyp() + "\n" + "\n".join(tour.getZusatzInfo()) + "\nSchwierigkeitsgrad: " + \
           ["unbekannt", "sehr einfach", "einfach", "mittel", "schwer", "sehr schwer"][tour.getSchwierigkeit()] + \
           "\nLink: " + tour.getFrontendLink()
    desc = desc.replace("\n\n", "\n").replace("\n", "\\n")
    return desc


def expStart(tour):
    t = tour.getDatum() # t = ("Sa, 27.03.2021", "16:00") => "20210327T160000"
    return t[0][10:14] + t[0][7:9] + t[0][4:6] + "T" + t[1][0:2] + t[1][3:5] + "00"


def expEnd(tour):
    t = tour.getEndDatum()
    return t[0][10:14] + t[0][7:9] + t[0][4:6] + "T" + t[1][0:2] + t[1][3:5] + "00"


def expLocation(tour):
    t = tour.getStartpunkt()
    name = t[0]
    street = t[1]
    city = t[2]
    loc = name
    if city != "":
        if loc == "":
            loc = city
        else:
            loc = loc + " " + city
    if street != "":
        if loc == "":
            loc = street
        else:
            loc = loc + " " + street
    return loc


class CalHandler:
    def __init__(self, tourServerVar):
        self.tourServerVar = tourServerVar
        self.expFunctions = {  # keys in lower case
            "titel": expTitel,
            "desc": expDesc,
            "start": expStart,
            "end": expEnd,
            "location": expLocation,
        }
        with open("cal.json", "r", encoding="utf-8") as jsonFile:
            conf = json.load(jsonFile)
        url = conf["url"]
        username = conf["username"]
        password = conf["password"]

        client = caldav.DAVClient(url=url, username=username, password=password)
        principal = client.principal()
        self.calendar = principal.calendars()[0]
        events = self.calendar.events()
        for ev in events:
            print(ev)
            if ev.vobject_instance.contents["prodid"][0].value.find("TTP2CAL") > 0:
                ev.delete()
        pass


    def expandCmd(self, tour, cmd):
        f = self.expFunctions.get(cmd)
        if f is None:
            return "???" + cmd + "???"
        return f(tour)


    def __enter__(self):
        return self


    def __exit__(self, *args):
        pass


    def handleTermin(self, termin):
        pass


    def handleTour(self, tour):
        input = [
            "BEGIN:VCALENDAR",
            "PRODID:-//TTP2CAL//EN",
            "VERSION:2.0",
            "BEGIN:VEVENT",
            "DTSTART;TZID=Europe/Berlin:${start}",
            "DTEND;TZID=Europe/Berlin:${end}",
            "SUMMARY:${titel}",
            "LOCATION:${location}",
            "DESCRIPTION:${desc}",
            # "X-ALT-DESC:${desc}", does not work with nextcloud!?
            "END:VEVENT",
            "END:VCALENDAR"]
        output = ""
        for l in input:
            mp = paramRE.search(l, 0)
            if mp is not None:
                sp = mp.span()
                cmd = l[sp[0] + 2:sp[1] - 1]
                l = l[0:sp[0]] + self.expandCmd(tour, cmd) + l[sp[1]:]
                output += l
            else:
                output += l
            output += "\n"
        self.calendar.save_event(output)
        pass

"""
BEGIN:VCALENDAR
PRODID:-//IDN nextcloud.com//Calendar app 2.1.3//EN
CALSCALE:GREGORIAN
VERSION:2.0
BEGIN:VEVENT
CREATED:20210322T174856Z
DTSTAMP:20210322T175241Z
LAST-MODIFIED:20210322T175241Z
SEQUENCE:3
UID:a95a2c15-e7a2-497e-9a15-9db2adc8b518
DTSTART;TZID=Europe/Berlin:20210323T190000
DTEND;TZID=Europe/Berlin:20210323T200000
SUMMARY:test
LOCATION:München
DESCRIPTION:Donec posuere vulputate arcu. Phasellus viverra nulla ut me
 tus varius laoreet. Etiam sollicitudin\, ipsum eu pulvinar rutrum\, tellus 
 ipsum laoreet sapien\, quis venenatis ante odio sit amet eros.\n\nMaecenas 
 malesuada. Nullam nulla eros\, ultricies sit amet\, nonummy id\, imperdiet 
 feugiat\, pede. Morbi vestibulum volutpat enim.\n\nFusce vulputate eleifend
  sapien. In ut quam vitae odio lacinia tincidunt. Maecenas nec odio et ante
  tincidunt tempus.\n\n
END:VEVENT
BEGIN:VTIMEZONE
TZID:Europe/Berlin
BEGIN:DAYLIGHT
TZOFFSETFROM:+0100
TZOFFSETTO:+0200
TZNAME:CEST
DTSTART:19700329T020000
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU
END:DAYLIGHT
BEGIN:STANDARD
TZOFFSETFROM:+0200
TZOFFSETTO:+0100
TZNAME:CET
DTSTART:19701025T030000
RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU
END:STANDARD
END:VTIMEZONE
END:VCALENDAR

Öffentlicher Link:
https://hh.adfc-clouds.de/index.php/apps/calendar/p/potEFL75WEX5nxBQ
"""
