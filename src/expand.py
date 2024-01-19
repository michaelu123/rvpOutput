import datetime
import os
import re
import sys
import time

import tourRest
from myLogger import logger

paramRE = re.compile(r"\${(\w*?)}")
fmtRE = re.compile(r"\.fmt\((.*?)\)")

schwierigkeitMap = {0: "sehr einfach",
                    1: "sehr einfach",
                    2: "einfach",
                    3: "mittel",
                    4: "schwer",
                    5: "sehr schwer"}

# schwarzes Quadrat = Wingdings 2 0xA2, weißes Quadrat = 0xA3
schwierigkeitMMap = {0: "\u00a3\u00a3\u00a3\u00a3\u00a3",
                     1: "\u00a2\u00a3\u00a3\u00a3\u00a3",
                     2: "\u00a2\u00a2\u00a3\u00a3\u00a3",
                     3: "\u00a2\u00a2\u00a2\u00a3\u00a3",
                     4: "\u00a2\u00a2\u00a2\u00a2\u00a3",
                     5: "\u00a2\u00a2\u00a2\u00a2\u00a2"}
# Dreieck Spitze links unten = Wingdings 3 0x78, Dreieck Spitze Mitte oben = 0x70
schwierigkeitHMap = {0: "\u0078\u0020\u0020\u0020",
                     1: "\u0078\u0020\u0020\u0020",
                     2: "\u0070\u0020\u0020\u0020",
                     3: "\u0070\u0070\u0020\u0020",
                     4: "\u0070\u0070\u0070\u0020",
                     5: "\u0070\u0070\u0070\u0070"}

"""
see https://stackoverflow.com/questions/4770297/convert-utc-datetime-string-to-local-datetime-with-python
"""


def convertToMEZOrMSZ(s: str):  # '2018-04-29T06:30:00+00:00'
    dt = time.strptime(s[0:19], "%Y-%m-%dT%H:%M:%S")
    t = time.mktime(dt)
    dt1 = datetime.datetime.fromtimestamp(t)
    dt2 = datetime.datetime.utcfromtimestamp(t)
    diff = (dt1 - dt2).seconds
    t += diff
    dt = datetime.datetime.fromtimestamp(t)
    return dt


#  it seems that with "pyinstaller -F" tkinter (resp. TK) does not find data files relative to the MEIPASS dir
def pyinst(path):
    path = path.strip()
    if os.path.exists(path):
        return path
    if hasattr(sys, "_MEIPASS"):  # i.e. if running as exe produced by pyinstaller
        pypath = sys._MEIPASS + "/" + path
        if os.path.exists(pypath):
            return pypath
    return path


def expHeute(_, format):
    if format is None:
        return str(datetime.date.today())
    else:
        # return datetime.date.today().strftime(format)
        return datetime.datetime.now().strftime(format)


def expEnd(event, format):
    dt = convertToMEZOrMSZ(event.getEndDatumRaw())
    if format is None:
        return str(dt)
    else:
        return dt.strftime(format)


def expStart(event, format):
    dt = convertToMEZOrMSZ(event.getDatumRaw())
    if format is None:
        return str(dt)
    else:
        return dt.strftime(format)


def expNummer(tour, _):
    k = tour.getKategorie()[0]
    if k == "T":
        k = "G"  # Tagestour -> Ganztagestour
    return tour.getRadTyp()[0].upper() + " " + tour.getNummer() + " " + k


def expName(event, _):
    return event.getName()


def expKurzBeschreibung(event, _):
    return event.getKurzbeschreibung()

def expCity(event, _):
    return event.getCity()


def expStreet(event, _):
    return event.getStreet()


def expKategorie(event, _):
    return event.getKategorie()


def expSchwierigkeit(tour, _):
    return schwierigkeitMap[tour.getSchwierigkeit()]

def expSchwierigkeitM(tour, _):
    return schwierigkeitMMap[tour.getSchwierigkeit()]

def expSchwierigkeitH(tour, _):
    return schwierigkeitHMap[tour.getSchwierigkeit()]

def expTourLength(tour, _):
    return tour.getStrecke()


def expTourLeiterM(tour, _):
    tl = tour.getPersonen()
    if len(tl) == 0:
        return ""
    return ", ".join(tl)


def expHoehenMeter(tour, _):
    return tour.getHoehenmeter()


def expAnstiege(tour, _):
    return tour.getAnstiege()


def expCharacter(tour, _):
    return tour.getCharacter()


def expAbfahrtenM(tour, _):
    afs = tour.getAbfahrten()
    if len(afs) == 0:
        return ""
    if afs[0][1] != "":
        s = afs[0][1] + " Uhr; " + afs[0][2]
    else:
        s = afs[0][2]
    for afx, af in enumerate(afs[1:]):
        if afs[afx][1] != "":
            s = s + "\n " + str(afx + 2) + ". Startpunkt: " + afs[afx][1] + " Uhr;" + afs[afx][2]
        else:
            s = s + "\n " + str(afx + 2) + ". Startpunkt: " + afs[afx][2]
    return s


def expTourStufe(tour, _):
    return tour.getRadTyp()[0].upper() + " " + str(tour.getSchwierigkeit())


def expRadTypen(tour, _):
    typen = tour.getRadTypen()
    return ", ".join(typen)

def expZusatzInfo(tour, _):
    zi = tour.getZusatzInfo()
    if len(zi) == 0:
        return None
    txt = ""
    for z in zi:
        txt += z + "\n"
    return txt

def expPreise(tour, _):
    res = tour.getPrices()
    if res is None:
        return "Nicht angegeben"
    (minp, maxp) = res
    return "Mitglieder " + str(minp) + ", Nichtmitglieder " + str(maxp)

def expAnmeldung(tour, _):
    return tour.getAnmeldung()

def expOrganizer(tour, _):
    return tour.getOrganizer()
def expOrganizer2(tour, _):
    return tour.getOrganizer2()

class Expand:
    def __init__(self):
        self.expFunctions = {  # keys in lower case
            "heute": expHeute,
            "start": expStart,
            "end": expEnd,
            "nummer": expNummer,
            "titel": self.expTitel,
            "beschreibung": self.expBeschreibung,
            "kurz": expKurzBeschreibung,
            "tourleiter": self.expTourLeiter,
            "betreuer": self.expBetreuer,
            "name": expName,
            "city": expCity,
            "street": expStreet,
            "kategorie": expKategorie,
            "schwierigkeit": expSchwierigkeit,
            "schwierigkeitm": expSchwierigkeitM,
            "schwierigkeith": expSchwierigkeitH,
            "tourlänge": expTourLength,
            "tourstufe": expTourStufe,
            "abfahrten": self.expAbfahrten,
            "zusatzinfo": expZusatzInfo,
            "höhenmeter": expHoehenMeter,
            "anstiege": expAnstiege,
            "character": expCharacter,
            "abfahrtenm": expAbfahrtenM,
            "tourleiterm": expTourLeiterM,
            "radtypen": expRadTypen,
            "preise": expPreise,
            "anmeldung": expAnmeldung,
            "organizer": expOrganizer,
            "organizer2": expOrganizer2,
            "seite": lambda e, f: "{:>2}".format(self.pageNr),  # 01-99
        }

    def expand(self, s, event):
        while True:
            mp = paramRE.search(s)
            if mp is None:
                return s
            gp = mp.group(1).lower()
            sp = mp.span()
            mf = fmtRE.search(s, pos=sp[1])
            if mf is not None and sp[1] == mf.span()[0]:  # i.e. if ${param] is followed immediately by .fmt()
                gf = mf.group(1)
                sf = mf.span()
                s = s[0:sf[0]] + s[sf[1]:]
                expanded = self.expandParam(gp, event, gf)
            else:
                expanded = self.expandParam(gp, event, None)
            if expanded is None:  # special case for beschreibung, handled as markdown
                return None
            try:
                s = s[0:sp[0]] + expanded + s[sp[1]:]
            except Exception:
                logger.error("expanded = " + expanded)

    def expandParam(self, param, event, format):
        try:
            f = self.expFunctions[param]
            return f(event, format)
        except Exception as e:
            err = 'Fehler mit dem Parameter "' + param + \
                  '" des Events ' + self.eventMsg
            print(err)
            logger.exception(err)
            return param

    def expTitel(self, event, _):
        if self.linkType == "Frontend":
            self.url = event.getFrontendLink()
        elif self.linkType == "Backend":
            self.url = event.getBackendLink()
        else:
            self.url = None

        titel = event.getTitel()
        logger.info("Titel: " + event.getTitel())
        state = event.getPublState()
        if state == "Published":
            return titel
        if state == "Review":
            mark = "Prüfung"
        elif state == "Draft":
            mark = "Entwurf"
        elif state == "Cancelled":
            mark = "Gestrichen"
        else:
            mark = state
        return titel + " (" + mark + ")"

    def expBeschreibung(self, event, _):
        desc = event.getBeschreibung(False)
        return desc

    def expPersonen(self, bezeichnung, event):
        tl = event.getPersonen()
        if len(tl) == 0:
            return ""
        return bezeichnung + ": " + ", ".join(tl)

    def expTourLeiter(self, tour, _):
        return self.expPersonen("Tourleiter", tour)

    def expBetreuer(self, termin, _):
        return self.expPersonen("Betreuer", termin)

    def expAbfahrten(self, tour, _):
        afs = tour.getAbfahrten()
        if len(afs) == 0:
            return ""
        afl = []
        for af in afs:
            if af[1] == "":
                afl.append(af[2])
            else:
                afl.append(af[0] + " " + af[1] + " " + af[2])
        # print("AB0:", self.runX, "<<" + self.para.runs[self.runX].text + ">>", " ".join(["<" + run.text + ">" for run in self.para.runs]))
        return "Ort" + ("" if len(afs) == 1 else "e") + ": " + ", ".join(afl)
