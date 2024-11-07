import time
from xml.dom.minidom import *
import event
from myLogger import logger

schwierList = ["unbekannt", "sehr einfach", "einfach", "mittel", "schwer", "sehr schwer"]
restServer = None


# from https://stackoverflow.com/questions/191536/converting-xml-to-json-using-python Paulo Vj
def parse_element(element):
    dict_data = dict()
    if element.nodeType == element.TEXT_NODE:
        dict_data['data'] = element.data
    if element.nodeType not in [element.TEXT_NODE, element.DOCUMENT_NODE,
                                element.DOCUMENT_TYPE_NODE]:
        for item in element.attributes.items():
            dict_data[item[0]] = item[1]
    if element.nodeType not in [element.TEXT_NODE, element.DOCUMENT_TYPE_NODE]:
        for child in element.childNodes:
            child_name, child_dict = parse_element(child)
            if child_name in dict_data:
                try:
                    dict_data[child_name].append(child_dict)
                except AttributeError:
                    dict_data[child_name] = [dict_data[child_name], child_dict]
            else:
                dict_data[child_name] = child_dict
    for k in dict_data.keys():
        v = dict_data[k]
        if isinstance(v, dict):
            if len(v) == 1 and "#text" in v.keys():
                dict_data[k] = v["#text"]["data"]
            elif len(v) == 0:
                dict_data[k] = ""
    return element.nodeName, dict_data


def elimText(d):
    if isinstance(d, dict):
        if '#text' in d:
            del d['#text']
        if 'xsi:nil' in d:
            del d['xsi:nil']
        for n in d:
            d[n] = elimText(d[n])
        if len(d) == 0:
            return ""
    elif isinstance(d, list):
        for n in d:
            elimText(n)
        pass
    return d


# need to remove non-XML chars from XML
class XMLFilter:
    def __init__(self, f):
        self.f = f

    def read(self, n):
        s = self.f.read(n)
        s = s.replace("&#x1", "§§§§")  # ????
        return s


class XmlEvent(event.Event):
    def __init__(self, eventItem):
        self.eventItem = eventItem
        self.tourLocations = eventItem.get("TourLocations")
        self.titel = self.eventItem.get("Title").strip()
        self.eventNummer = 0
        logger.info("eventItemId %s %s", self.titel, self.getEventItemId())

    def getEventItemId(self):
        return self.eventItem.get("EventItemId")

    def getFrontendLink(self):
        try:
            evR = restServer.getEventById(self.getEventItemId(), self.getTitel())
            return evR.getFrontendLink()
        except:
            return None

    def getBackendLink(self):
        return "https://intern-touren-termine.adfc.de/modules/events/" + self.getEventItemId()

    def getNummer(self):
        num = self.eventNummer
        if num is None:
            num = "999"
        return num

    def makeList(self, e):
        if not isinstance(e, list):
            return [e]
        return e

    def tourLoc(self, tl):
        if tl is None:
            return None
        typ = tl.get("Type")
        if typ != "Startpunkt" and typ != "Treffpunkt" and typ != "Zielort":
            return None
        beginning = tl.get("Beginning")
        logger.debug("beginning %s", beginning)  # '2018-04-24T12:00:00'
        beginning = event.convertToMEZOrMSZ(beginning)  # '2018-04-24T14:00:00'
        # TODO wt
        beginning = event.getTime(beginning)  # 14:00
        name = tl.get("Name")
        street = tl.get("Street")
        city = tl.get("City")
        logger.debug("name '%s' street '%s' city '%s'", name, street, city)
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
        if typ == "Startpunkt":
            if self.isTermin():
                typ = "Treffpunkt"
            else:
                typ = "Start"
        if typ == "Zielort":
            typ = "Ziel"
        return (typ, beginning, loc)

    def getAbfahrten(self):
        abfahrten = []
        tl = self.tourLoc(self.eventItem.get("CDeparture"))
        if tl is not None:
            abfahrten.append(tl)

        tls = self.tourLocations
        if tls != "":
            tls = tls.get("ExportTourLocation")
            tls = self.makeList(tls)
            for tl in tls:
                tl = self.tourLoc(tl)
                if tl is not None:
                    abfahrten.append(tl)

        tl = self.tourLoc(self.eventItem.get("CDestination"))
        if tl is not None:
            abfahrten.append(tl)
        return abfahrten

    def getBeschreibung(self, raw):
        desc = self.eventItem.get("Description")
        desc = event.removeHTML(desc)
        desc = event.removeSpcl(desc)
        if raw:
            return desc
        desc = event.normalizeText(desc)
        return desc

    def getKurzbeschreibung(self):
        desc = self.eventItem.get("CShortDescription")
        desc = event.normalizeText(desc)
        return desc

    def isTermin(self):
        return self.eventItem.get("EventType") == "Termin"

    def getSchwierigkeit(self):
        if self.isTermin():
            return "-"
        schwierigkeit = self.eventItem.get("CAdjustedTourDifficulty")
        if schwierigkeit == "":
            schwierigkeit = self.eventItem.get("CTourDifficulty")
        if schwierigkeit == "":
            return 0
        return schwierList.index(schwierigkeit)

    def getTourSpeed(self):
        if self.isTermin():
            return "-"
        speed1 = self.eventItem.get("CTourSpeed")
        speed2 = self.eventItem.get("CTourSpeedKmh")
        if speed2 == "" or speed2 == "0":
            return speed1
        return speed2 + " km/h"

    def getMerkmale(self):
        merkmale = []
        for itemTag in ["FurtherProperties", "UseableFor", "SpecialTargetGroup", "SpecialCharacteristic"]:
            tag = self.eventItem.get(itemTag)
            if tag is None or tag == "":
                continue
            tags = self.makeList(tag.get("ExportTag"))
            for tag in tags:
                merkmale.append(tag.get("Tag"))
        return merkmale

    """ 
    Tags: (LV BY Stand Feb 2020), d.h. keine Termin-Tags! 
    'FurtherProperties': 
        {'Badepause', 'Picknick (Selbstverpflegung)', 'Bahnfahrt', 'Einkehr in Restauration', 'Zusatzkosten ( z.B. Eintritte, Fährtickets)'}, 
    'UseableFor': 
        {'Pedelec', 'Rennrad', 'Tandem', 'Liegerad', 'Mountainbike', 'Alltagsrad'}, 
    'SpecialCharacteristic': 
        {'Natur', 'Neubürger-/Kieztouren', 'Kultur', 'Stadt entdecken / erleben'}, 
    'SpecialTargetGroup': 
        {'Familien', 'Touren für Kinder (bis 14 Jahren)', 'Senioren', 'Touren für Jugendliche (15-18 Jahren)', 'Jugendliche', 'Menschen mit Behinderungen'}
    """

    def getKategorie(self):
        # until portal issues fixed:
        try:
            evR = restServer.getEventById(self.getEventItemId(), self.getTitel())
            return evR.getKategorie()
        except:
            return "Ohne"

    def getRadTyp(self):
        """
            Radtyp:
            "UseableFor": {
                "ExportTag": [
                    {
                        "Tag": "Alltagsrad"
                    },
                    {
                        "Tag": "Mountainbike"
                    },
                    {
                        "Tag": "Pedelec"
                    }
                ]
            },
        """
        # wenn nur Rennrad oder nur Mountainbike, dann dieses, sonst Tourenrad
        tag = self.eventItem.get("UseableFor")
        if tag is None or tag == "":
            return "Tourenrad"
        tags = self.makeList(tag.get("ExportTag"))
        rtCnt = len(tags)
        for tag in tags:
            t = tag.get("Tag")
            if rtCnt == 1 and (t == "Rennrad" or t == "Mountainbike"):
                return t
        return "Tourenrad"

    def getRadTypen(self):
        """
            Radtyp:
            "UseableFor": {
                "ExportTag": [
                    {
                        "Tag": "Alltagsrad"
                    },
                    {
                        "Tag": "Mountainbike"
                    },
                    {
                        "Tag": "Pedelec"
                    }
                ]
            },
        """
        tag = self.eventItem.get("UseableFor")
        if tag is None or tag == "":
            return ["Tourenrad"]
        tags = self.makeList(tag.get("ExportTag"))
        typen = []
        for tag in tags:
            t = tag.get("Tag")
            typen.append(t)
        return typen

    def getZusatzInfo(self):
        besonders = []
        weitere = []
        zielgruppe = []

        tag = self.eventItem.get("SpecialCharacteristic")
        if tag is not None and tag != "":
            besonders = [x.get("Tag") for x in self.makeList(tag.get("ExportTag"))]

        tag = self.eventItem.get("FurtherProperties")
        if tag is not None and tag != "":
            weitere = [x.get("Tag") for x in self.makeList(tag.get("ExportTag"))]

        tag = self.eventItem.get("SpecialTargetGroup")
        if tag is not None and tag != "":
            zielgruppe = [x.get("Tag") for x in self.makeList(tag.get("ExportTag"))]

        zusatzinfo = []
        if len(besonders) > 0:
            besonders = "Besondere Charakteristik/Thema: " + ", ".join(besonders)
            zusatzinfo.append(besonders)
        if len(weitere) > 0:
            weitere = "Weitere Eigenschaften: " + ", ".join(weitere)
            zusatzinfo.append(weitere)
        if len(zielgruppe) > 0:
            zielgruppe = "Besondere Zielgruppe: " + ", ".join(zielgruppe)
            zusatzinfo.append(zielgruppe)
        return zusatzinfo

    def getStrecke(self):
        tl = self.eventItem.get("CTourLengthKm")
        return tl + " km"

    def getHoehenmeter(self):
        h = self.eventItem.get("CTourHeight")
        return h

    def getAnstiege(self):
        h = self.eventItem.get("CTourClimb")  # flach, einzelne Anstiege, hügelig, bergig
        return h

    def getCharacter(self):
        c = self.eventItem.get("CTourSurface")
        return c

    def getDatum(self):
        """
            "Beginning": "2020-05-24T05:00:00",
            "BeginningDate": "24/05/2020",
            "BeginningTime": "05:00:00",
            "End": "2020-05-24T17:00:00",
            "EndDate": "24/05/2020",
            "EndTime": "05:00:00",
        """
        beginning = self.eventItem.get("Beginning")
        datum = event.convertToMEZOrMSZ(beginning)  # '2018-04-24T14:00:00'
        logger.debug("datum <%s>", str(datum))
        day = str(datum[0:10])
        date = time.strptime(day, "%Y-%m-%d")
        weekday = event.weekdays[date.tm_wday]
        res = (weekday + ", " + day[8:10] + "." + day[5:7] + "." + day[0:4], event.getTime(datum))
        return res

    def getDatumRaw(self):
        return self.eventItem.get("Beginning")

    def getEndDatum(self):
        beginning = self.eventItem.get("End")
        datum = event.convertToMEZOrMSZ(beginning)  # '2018-04-24T14:00:00'
        logger.debug("datum <%s>", str(datum))
        day = str(datum[0:10])
        date = time.strptime(day, "%Y-%m-%d")
        weekday = event.weekdays[date.tm_wday]
        # TODO wt
        res = (weekday + ", " + day[8:10] + "." + day[5:7] + "." + day[0:4], event.getTime(datum))
        return res

    def getEndDatumRaw(self):
        return self.eventItem.get("End")

    def getPersonen(self):
        try:
            evR = restServer.getEventById(self.getEventItemId(), self.getTitel())
            return evR.getPersonen()
        except:
            pass
        personen = []
        org = self.eventItem.get("Organizer")
        if org is not None and org != "":
            personen.append(org)
        org2 = self.eventItem.get("Organizer2")
        if org2 is not None and org2 != "" and org2 != org:
            personen.append(str(org2))
        return personen

    def getImagePreview(self):
        try:
            evR = restServer.getEventById(self.getEventItemId(), self.getTitel())
            return evR.getImagePreview()
        except Exception:
            logger.exception("cannot get image preview")
            pass
        return None

    def getPublState(self):
        try:
            evR = restServer.getEventById(self.getEventItemId(), self.getTitel())
            return evR.getPublState()
        except Exception:
            logger.exception("cannot get publication state")
            pass
        return None

    def getImageUrl(self):
        imageUrls = self.eventItem.get("EventItemImages")
        if imageUrls != "":
            imageUrls = imageUrls.get("ExportEventItemImage")
            imageUrls = self.makeList(imageUrls)
            return imageUrls[0].get("DownloadLink")

    def getImageStream(self, imageUrl, itemId):
        try:
            return restServer.getImageStream(imageUrl, itemId)
        except Exception:
            logger.log("cannot get image stream")
        return None

    def getName(self):
        dep = self.eventItem.get("CDeparture")
        return dep.get("Name")

    def getCity(self):
        dep = self.eventItem.get("CDeparture")
        return dep.get("City")

    def getStreet(self):
        dep = self.eventItem.get("CDeparture")
        return dep.get("Street")

    def isExternalEvent(self):
        return self.eventItem.get("CExternalEvent") == "Ja"

    def getPrices(self):
        minPrice = 9999999.0
        maxPrice = 0.0
        itemPrices = self.eventItem.get("EventItemPrices")
        if itemPrices is None or isinstance(itemPrices, str):
            return None
        itemPrices = itemPrices.get("ExportEventItemPrice")
        if itemPrices is None or len(itemPrices) == 0:
            return None
        for itemPrice in itemPrices:
            price = float(itemPrice.get("Price"))
            if price < minPrice:
                minPrice = price
            if price > maxPrice:
                maxPrice = price
        return minPrice, maxPrice

    def getAnmeldung(self):
        rtype = self.eventItem.get("CRegistrationType")
        rurl = self.eventItem.get("CExternalRegistrationUrl")
        max = self.eventItem.get("Maximum")
        closDate = self.eventItem.get("ClosingDate")
        res = rtype
        res += ", max Teilnehmer: "
        if max == "0":
            res += "unbegrenzt"
        else:
            res += max
        if closDate is not None and closDate != "":
            closDate = event.convertToMEZOrMSZ(closDate)  # '2018-04-24T14:00:00'
            closDate = closDate[8:10] + "." + closDate[5:7] + "." + closDate[0:4] + " " + event.getTime(closDate)
            # TODO wt
            res += ", Anmeldeschluss: " + closDate + " (" + self.getDatum()[0][4:9] + ")"
        if rurl != "":
            res += ", extUrl=" + rurl
        return res


    def getOrganizer(self):
        return self.eventItem.get("Organizer", "-")

    def getOrganizer2(self):
        return self.eventItem.get("Organizer2", "-")


class EventServer:
    def __init__(self, fn, rs):
        global restServer
        self.fn = fn
        restServer = rs
        self.events = {}
        self.alleTouren = []
        self.alleTermine = []

    def getEvents(self, unitKey, start, end, typ):
        unit = "Alles" if unitKey is None or unitKey == "" else unitKey
        # startYear = start[0:4]

        with open(self.fn, "r", encoding="utf-8") as f:
            f = XMLFilter(f)
            xmlt = parse(f)
        n, d = parse_element(xmlt)
        jsRoot = elimText(d)
        # jsonPath = "xml2.json"
        # with open(jsonPath, "w") as jsonFile:
        #     json.dump(jsRoot, jsonFile, indent=4)
        js = jsRoot.get("ExportEventItemList")
        js = js.get("EventItems")
        items = js.get("ExportEventItem")
        events = []
        if len(items) == 0:
            return events
        for item in iter(items):
            titel = item.get("Title")
            if titel is None:
                logger.error("Kein Titel für den Event %s", str(item))
                continue
            if item.get("IsCancelled") != "Nein":
                logger.info("Event %s ist gecancelt", titel)
                continue
            if typ != "Alles" and item.get("EventType") != typ:
                continue
            beginning = item.get("Beginning")
            if beginning is None:
                logger.error("Kein Beginn für den Event %s", titel)
                continue
            begDate = beginning[0:4]
            if begDate < start[0:4] or begDate > end[0:4]:
                continue
            ev = XmlEvent(item)
            if ev.isTermin():
                self.alleTermine.append(ev)
            else:
                self.alleTouren.append(ev)
            begDate = event.convertToMEZOrMSZ(beginning)[0:10]
            if begDate < start or begDate > end:
                logger.info("event " + titel + " not in timerange")
                continue
            # add other filter conditions here
            logger.info("event " + titel + " OK")
            self.events[ev.getEventItemId()] = ev
        return self.events.values()

    def getEvent(self, ev):
        return ev

    def getEventById(self, eventItemId, _titel):
        return self.events[eventItemId]

    def calcNummern(self):
        # too bad we base numbers on kategorie and radtyp,which we cannot get from the search result
        self.alleTouren.sort(key=lambda x: x.getDatumRaw())  # sortieren nach Datum
        yyyy = ""
        logger.info("Begin calcNummern")
        for tour in self.alleTouren:
            datum = tour.getDatumRaw()
            if datum[0:4] != yyyy:
                yyyy = datum[0:4]
                tnum = 100
                rnum = 300
                mnum = 400
                mtnum = 600
            radTyp = tour.getRadTyp()
            kategorie = tour.getKategorie()
            if kategorie == "Mehrtagestour":
                num = mtnum
                mtnum += 1
            elif radTyp == "Rennrad":
                num = rnum
                rnum += 1
            elif radTyp == "Mountainbike":
                num = mnum
                mnum += 1
            else:
                num = tnum
                tnum += 1
            tour.eventNummer = str(num)

        self.alleTermine.sort(key=lambda x: x.getDatumRaw())  # sortieren nach Datum
        yyyy = ""
        for termin in self.alleTermine:
            datum = termin.getDatumRaw()
            if datum[0:4] != yyyy:
                yyyy = datum[0:4]
                tnum = 700
            num = tnum
            tnum += 1
            termin.eventNummer = str(num)
        logger.info("End calcNummern")


"""
    "isTemplate": false,
    "isDraft": true,
    "isReview": false,
    "isPublished": false,
    "isFinished": false,
    "isTour": true,
    "isOptional": false
    "isCancelled": false,

"""
