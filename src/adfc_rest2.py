#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""
USAGE
You must have a document open, and a text frame selected.
Simply run the script, which asks if you want to read from the rest interface
or from(previously written) json files.
Note that any text in the frame will be deleted before the text from
the XML file is added.
The script also assumes you have created a styles named 'Radtour_titel' etc,
which it will apply to the frame.
"""
import sys

import csvHandler
import textHandler
import tourServer


def toDate(dmy):  # 21.09.2018
    d = dmy[0:2]
    m = dmy[3:5]
    if len(dmy) == 10:
        y = dmy[6:10]
    else:
        y = "20" + dmy[6:8]
    if y < "2018":
        raise ValueError("Kein Datum vor 2018 möglich")
    if int(d) == 0 or int(d) > 31 or int(m) == 0 or \
            int(m) > 12 or int(y) < 2000 or int(y) > 2100:
        raise ValueError("Bitte Datum als dd.mm.jjjj angeben, nicht als " + dmy)
    return y + "-" + m + "-" + d  # 2018-09-21


try:
    arg0 = sys.argv[0]
    if arg0.find(".py") == -1:
        raise ImportError
    else:
        import scribusHandler
    handler = scribusHandler.ScribusHandler()
    tourServerVar = tourServer.EventServer(handler.getUseRest(),
                                          handler.getIncludeSub(), 4)
    unitKeys = handler.getUnitKeys().split(",")
    start = handler.getStart()
    end = handler.getEnd()
    eventType = handler.getEventType()
    radTyp = handler.getRadTyp()
except ImportError:
    import printHandler
    import http.client as httplib
    import argparse
    parser = argparse.ArgumentParser(description="Formatiere Daten des Tourenportals")
    parser.add_argument("-a", "--aktuell", dest="useRest", action="store_true",
                        help="Aktuelle Daten werden vom Server geholt")
    parser.add_argument("-u", "--unter", dest="includeSub", action="store_true",
                        help="Untergliederungen einbeziehen")
    parser.add_argument("-f", "--format", dest="ausgabeformat", choices=["S", "M", "C"],
                        help="Ausgabeformat (S=Starnberg, M=München, C=CSV",
                        default="S")
    parser.add_argument("-t", "--type", dest="eventType", choices=["R", "T", "A"],
                        help="Typ (R=Radtour, T=Termin, A=Alles), default=A",
                        default="A")
    parser.add_argument("-r", "--rad", dest="radTyp",
                        choices=["R", "T", "M", "A"],
                        help="Fahrradtyp (R=Rennrad, T=Tourenrad, M=Mountainbike, A=Alles), default=A",
                        default="A")
    parser.add_argument("nummer",
                        help="Gliederungsnummer(n), z.B. 152059 für München, komma-separierte Liste")
    parser.add_argument("start", help="Startdatum (TT.MM.YYYY)")
    parser.add_argument("end", help="Endedatum (TT.MM.YYYY)")
    args = parser.parse_args()
    unitKeys = args.nummer.split(",")
    useRest = args.useRest
    includeSub = args.includeSub
    start = args.start
    end = args.end
    eventType = args.eventType
    radTyp = args.radTyp
    tourServerVar = tourServer.TourServer(False, useRest, includeSub)
    ausgabeformat = args.ausgabeformat
    if ausgabeformat == "S":
        handler = printHandler.PrintHandler()
    elif ausgabeformat == "M":
        handler = textHandler.TextHandler()
    elif ausgabeformat == "C":
        handler = csvHandler.CsvHandler(sys.stdout)
    else:
        handler = printHandler.PrintHandler()

start = toDate(start)
end = toDate(end)

if eventType == "R":
    eventType = "Radtour"
elif eventType == "T":
    eventType = "Termin"
elif eventType == "A":
    eventType = "Alles"
else:
    raise ValueError("Typ muss R für Radtour, T für Termin, oder A für beides sein")

if radTyp == "R":
    radTyp = "Rennrad"
elif radTyp == "T":
    radTyp = "Tourenrad"
elif radTyp == "M":
    radTyp = "Mountainbike"
elif radTyp == "A":
    radTyp = "Alles"
else:
    raise ValueError("Rad muss R für Rennrad, T für Tourenrad, M für Mountainbike, oder A für Alles sein")

touren = []
for unitKey in unitKeys:
    touren.extend(tourServerVar.getEvents(unitKey.strip(), start, end, eventType))


touren.sort(key=lambda x: x.get("beginning"))  # sortieren nach Datum
tourServerVar.calcNummern()

if len(touren) == 0:
    handler.nothingFound()
for tour in touren:
    tour = tourServerVar.getEvent(tour)
    if tour.isTermin():
        handler.handleTermin(tour)
    else:
        if radTyp != "Alles" and tour.getRadTyp() != radTyp:
            continue
        handler.handleTour(tour)
