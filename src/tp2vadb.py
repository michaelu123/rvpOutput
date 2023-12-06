#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import argparse
from datetime import date,timedelta

import tourServer
import vadb
import cal


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


parser = argparse.ArgumentParser(description="Erzeuge eine XML-Datei für die VADB HH mit Daten des Tourenportals")
parser.add_argument("-a", "--aktuell", dest="useRest", action="store_true",
                    help="Aktuelle Daten werden vom Server geholt")
parser.add_argument("-u", "--unter", dest="includeSub", action="store_true",
                    default=True,
                    help="Untergliederungen einbeziehen")
parser.add_argument("-c", "--cal", dest="useCal", action="store_true",
                    default=False,
                    help="Erzeuge Kalender-Einträge")
parser.add_argument("-t", "--type", dest="eventType", choices=["R", "T", "A"],
                    help="Typ (R=Radtour, T=Termin, A=Alles), default=A",
                    default="R")
parser.add_argument("-r", "--rad", dest="radTyp",
                    choices=["R", "T", "M", "A"],
                    help="Fahrradtyp (R=Rennrad, T=Tourenrad, M=Mountainbike, A=Alles), default=A",
                    default="A")
parser.add_argument("-s", "--start", dest="start", help="Startdatum (TT.MM.YYYY), Heute falls nicht angegeben", default="")
parser.add_argument("-e", "--end", dest="end", help="Endedatum (TT.MM.YYYY), Heute+<zeitraum> Tage, falls nicht angegeben", default="")
parser.add_argument("unitnummern",
                    help="Gliederungsnummer(n), z.B. 152059 für München, komma-separierte Liste")
parser.add_argument("-z", "--zeitraum", dest="zeitraum", help="Tourdaten von heute bis in <zeitraum> Tagen", default=90)

# -u -t A -r A 182 01.08.2020 31.08.2020
args = parser.parse_args()
unitKeys = args.unitnummern.split(",")
useRest = args.useRest
includeSub = args.includeSub
useCal = args.useCal
start = args.start
if start == "":
    start = date.today().strftime("%d.%m.%Y")
end = args.end
if end == "":
    end = (date.today() + timedelta(days=int(args.zeitraum))).strftime("%d.%m.%Y")
eventType = args.eventType
radTyp = args.radTyp
tourServerVar = tourServer.EventServer(useRest, includeSub, 1)

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

events = []
for unitKey in unitKeys:
    events.extend(tourServerVar.getEvents(unitKey.strip(), start, end, eventType))

events.sort(key=lambda x: x.get("beginning"))  # sortieren nach Datum
# tourServerVar.calcNummern()
with cal.CalHandler(tourServerVar) if useCal else vadb.VADBHandler(tourServerVar) as handler:
    for event in events:
        event = tourServerVar.getEvent(event)
        if event.isTermin():
            handler.handleTermin(event)
        else:
            if radTyp != "Alles" and event.getRadTyp() != radTyp:
                continue
            handler.handleTour(event)
            # break

"""
158     Hamburg
140004  Schwerin
162260  Cuxhaven
162270  Harburg
162280  Lüchow-Dannenberg
162290  Lüneburg
162291  Uelzen
162310  Rotenburg
162320  Heidekreis
162330  Stade
170130  Lauenburg       
170160  Neumünster      
170180  Ostholstein     
170190  Pinneberg       
170230  Bad Segeberg   
170240  Steinburg       
170291  Stormarn

158,140004,162260,162270,162280,162290,162291,162310,162320,162330,170130,170160,170180,170190,170230,170240,170291
"""
