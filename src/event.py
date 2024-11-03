import re
import time
import xml.sax
import os
import json
from abc import ABC, abstractmethod

from myLogger import logger

weekdays = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
character = ["", "durchgehend Asphalt", "fester Belag", "unebener Untergrund", "unbefestigte Wege"]
span1RE = r'<span.*?>'
span2RE = r'</span>'

sommerzeiten = None
sommerzeitenDefault = {
    "2020": {
        "begSZ": "2020-03-29",
        "endSZ": "2020-10-25"
    },
    "2021": {
        "begSZ": "2021-03-28",
        "endSZ": "2021-10-31"
    },
    "2022": {
        "begSZ": "2022-03-27",
        "endSZ": "2022-10-30"
    },
    "2023": {
        "begSZ": "2023-03-26",
        "endSZ": "2023-10-29"
    },
    "2024": {
        "begSZ": "2024-03-31",
        "endSZ": "2024-10-27"
    },
    "2025": {
        "begSZ": "2025-03-30",
        "endSZ": "2025-10-26"
    },
    "2026": {
        "begSZ": "2026-03-29",
        "endSZ": "2026-10-25"
    }
}


def loadSZ():
    szPath = "c:/temp/tpjson/sommerzeiten.json"
    global sommerzeiten
    if not os.path.exists(szPath):
        with open(szPath, "w") as jsonFileSz:
            json.dump(sommerzeitenDefault, jsonFileSz, indent=4)
    with open(szPath, "r") as jsonFileSz:
        sommerzeiten = json.load(jsonFileSz)


# see https://stackoverflow.com/questions/4770297/convert-utc-datetime-string-to-local-datetime-with-python
def convertToMEZOrMSZ(beginning):  # '2018-04-29T06:30:00+00:00'
    if beginning[10:19] == "T00:00:00":
        return beginning[0:10]  # without time, just return day
    # scribus/Python2 does not support %z
    beginning = beginning[0:19]  # '2018-04-29T06:30:00'
    d = time.strptime(beginning, "%Y-%m-%dT%H:%M:%S")
    oldDay = d.tm_yday
    year = beginning[0:4]
    if sommerzeiten is None:
        loadSZ()
    begSZ = None
    endSZ = None
    try:
        begSZ = sommerzeiten[year]["begSZ"]
        endSZ = sommerzeiten[year]["endSZ"]
    except:
        pass
    if begSZ is None or endSZ is None:
        raise ValueError("year " + beginning + " not configured in c:/temp/tpjson/sommerzeiten.json")
    sz = begSZ <= beginning < endSZ
    epochGmt = time.mktime(d)
    epochMez = epochGmt + ((2 if sz else 1) * 3600)
    mezTuple = time.localtime(epochMez)
    newDay = mezTuple.tm_yday
    mez = time.strftime("%Y-%m-%dT%H:%M:%S", mezTuple)
    if oldDay != newDay:
        logger.warning("day rollover from %s to %s", beginning, mez)
    return mez


def getTime(date):
    # if convertToMEZOrMSZ returned only day, then time=""
    if len(date) <= 16:
        return ""
    return date[11:16]


class SAXHandler(xml.sax.handler.ContentHandler):
    def __init__(self):
        super().__init__()
        self.r = []

    def startElement(self, name, attrs):
        pass

    def endElement(self, name):
        pass

    def characters(self, content):
        self.r.append(content)

    def ignorableWhiteSpace(self, whitespace):
        pass

    def skippedEntity(self, name):
        pass

    def val(self):
        return "".join(self.r)


def removeSpcl(s):
    while s.count("<br>"):
        s = s.replace("<br>", "\n")
    while s.count("&nbsp;"):
        s = s.replace("&nbsp;", " ")
    while s.count("<u>"):
        s = s.replace("<u>", "^^")
    while s.count("</u>"):
        s = s.replace("</u>", "^^")
    return s


def OLDremoveHTML(s):
    if s.find("</") == -1:  # no HTML
        return s
    try:
        htmlHandler = SAXHandler()
        xml.sax.parseString("<xxxx>" + s + "</xxxx>", htmlHandler)
        return htmlHandler.val()
    except:
        logger.exception("can not parse '%s'", s)
        return s


def removeHTML(s):
    s = re.sub(span1RE, "", s)
    s = re.sub(span2RE, "", s)
    return s


# Clean text
def normalizeText(t):
    # Rip off blank paragraphs, double spaces, html tags, quotes etc.
    changed = True
    while changed:
        changed = False
        t = t.strip()
        while t.count('***'):
            t = t.replace('***', '**')
            changed = True
        while t.count('**'):
            t = t.replace('**', '')
            changed = True
        while t.count('###'):
            t = t.replace('###', '##')
            changed = True
        while t.count('##'):
            t = t.replace('##', '')
            changed = True
        while t.count('~~~'):
            t = t.replace('~~~', '~~')
            changed = True
        while t.count('~~'):
            t = t.replace('~~', '')
            changed = True
        while t.count('\t'):
            t = t.replace('\t', ' ')
            changed = True
        if isinstance(t, str):  # crashes with Unicode/Scribus ??
            while t.count('\xa0'):
                t = t.replace('\xa0', ' ')
                changed = True
        while t.count('  '):
            t = t.replace('  ', ' ')
            changed = True
        while t.count('<br>'):
            t = t.replace('<br>', '\n')
            changed = True
        while t.count('\r'):  # DOS/Windows paragraph end.
            t = t.replace('\r', '\n')  # Change by new line
            changed = True
        while t.count('\n> '):
            t = t.replace('\n> ', '\n')
            changed = True
        while t.count(' \n'):
            t = t.replace(' \n', '\n')
            changed = True
        while t.count('\n '):
            t = t.replace('\n ', '\n')
            changed = True
        while t.count('\n\n'):
            t = t.replace('\n\n', '\n')
            changed = True
        if t.startswith('> '):
            t = t.replace('> ', '')
            changed = True
    return t


class Event(ABC):
    @abstractmethod
    def getTitel(self):
        pass

    @abstractmethod
    def getEventItemId(self):
        pass

    @abstractmethod
    def getFrontendLink(self):
        pass

    @abstractmethod
    def getBackendLink(self):
        pass

    @abstractmethod
    def getAbfahrten(self):
        pass

    @abstractmethod
    def getBeschreibung(self, raw):
        pass

    @abstractmethod
    def getKurzbeschreibung(self):
        pass

    @abstractmethod
    def isTermin(self):
        pass

    @abstractmethod
    def getSchwierigkeit(self):
        pass

    @abstractmethod
    def getTourSpeed(self):
        pass

    @abstractmethod
    def getMerkmale(self):
        pass

    @abstractmethod
    def getKategorie(self):
        pass

    @abstractmethod
    def getRadTyp(self):
        pass

    @abstractmethod
    def getRadTypen(self):
        pass

    @abstractmethod
    def getZusatzInfo(self):
        pass

    @abstractmethod
    def getStrecke(self):
        pass

    @abstractmethod
    def getHoehenmeter(self):
        pass

    @abstractmethod
    def getAnstiege(self):
        pass

    @abstractmethod
    def getCharacter(self):
        pass

    @abstractmethod
    def getDatum(self):
        pass

    @abstractmethod
    def getDatumRaw(self):
        pass

    @abstractmethod
    def getEndDatum(self):
        pass

    @abstractmethod
    def getEndDatumRaw(self):
        pass

    @abstractmethod
    def getPersonen(self):
        pass

    @abstractmethod
    def getImagePreview(self):
        pass

    @abstractmethod
    def getImageUrl(self):
        pass

    @abstractmethod
    def getImageStream(self, imageUrl, itemId):
        pass

    @abstractmethod
    def getName(self):
        pass

    @abstractmethod
    def getCity(self):
        pass

    @abstractmethod
    def getStreet(self):
        pass

    @abstractmethod
    def isExternalEvent(self):
        pass

    @abstractmethod
    def getPublState(self):
        pass

    @abstractmethod
    def getPrices(self):
        pass

    @abstractmethod
    def getAnmeldung(self):
        pass

    def getTitel(self):
        return self.titel
