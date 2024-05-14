# encoding: utf-8
import event
import time
from myLogger import logger

anstiege = ["flach", "einzelne Steigungen", "hügelig", "bergig"]
schwierList = ["unbekannt", "sehr einfach", "einfach", "mittel", "schwer", "sehr schwer"]

class RestEvent(event.Event):
    def __init__(self, eventJS, eventJSSearch, eventServer):
        self.eventJS = eventJS
        self.eventJSSearch = eventJSSearch
        self.eventServer = eventServer
        self.tourLocations = eventJS.get("tourLocations")
        self.itemTags = eventJS.get("itemTags")
        self.eventItem = eventJS.get("eventItem")
        self.titel = self.eventItem.get("title").strip()
        logger.info("eventItemId %s %s", self.titel, self.eventItem.get("eventItemId"))

    def getTitel(self):
        return self.titel

    def getEventItemId(self):
        return self.eventItem.get("eventItemId")

    def getPublishDate(self):
        datum = self.eventItem.get("cPublishDate")
        datum = event.convertToMEZOrMSZ(datum)
        return datum

    def getFrontendLink(self):
        return "https://touren-termine.adfc.de/radveranstaltung/" + self.eventItem.get("cSlug")

    def getSlug(self):
        return self.eventItem.get("cSlug")

    def getBackendLink(self):
        return "https://intern-touren-termine.adfc.de/modules/events/" + self.eventItem.get("eventItemId")

    def getNummer(self):
        num = self.eventJSSearch.get("eventNummer")
        if num is None:
            num = "999"
        return num

    def getAbfahrten(self):
        abfahrten = []
        for tourLoc in self.tourLocations:
            typ = tourLoc.get("type")
            logger.debug("typ %s", typ)
            if typ != "Startpunkt" and typ != "Treffpunkt":
                continue
            if not tourLoc.get("withoutTime"):
                # for first loc, get starttime from eventItem, beginning in tourloc is often wrong
                if len(abfahrten) == 0:
                    beginning = self.getDatum()[1]
                else:
                    beginning = tourLoc.get("beginning")
                    logger.debug("beginning %s", beginning)  # '2018-04-24T12:00:00'
                    beginning = event.convertToMEZOrMSZ(beginning)  # '2018-04-24T14:00:00'
                    beginning = event.getTime(beginning)  # 14:00
            else:
                beginning = ""
            name = tourLoc.get("name")
            street = tourLoc.get("street")
            city = tourLoc.get("city")
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
            abfahrt = (typ, beginning, loc)
            abfahrten.append(abfahrt)
        return abfahrten

    def getStartpunkt(self):
        # return first loc that is Startpunkt or Treffpunkt
        for tourLoc in self.tourLocations:
            typ = tourLoc.get("type")
            if typ != "Startpunkt" and typ != "Treffpunkt":
                continue
            name = tourLoc.get("name")
            street = tourLoc.get("street")
            city = tourLoc.get("city")
            latitude = tourLoc.get("latitude")
            longitude = tourLoc.get("longitude")
            return name, street, city, latitude, longitude
        return None

    def getBeschreibung(self, raw):
        desc = self.eventItem.get("description")
        desc = event.removeHTML(desc)
        desc = event.removeSpcl(desc)
        if raw:
            return desc
        desc = event.normalizeText(desc)
        return desc

    def getKurzbeschreibung(self):
        desc = self.eventItem.get("cShortDescription")
        desc = event.normalizeText(desc)
        return desc

    def isTermin(self):
        return self.eventItem.get("eventType") == "Termin"

    def getSchwierigkeit(self):
        if self.isTermin():
            return "-"
        schwierigkeit = self.eventItem.get("cAdjustedTourDifficulty")
        if schwierigkeit != "":
            return schwierList.index(schwierigkeit)
        schwierigkeit = self.eventItem.get("cTourDifficulty")
        if schwierigkeit < 1.4:
            return 1
        if schwierigkeit < 2.3:
            return 2
        if schwierigkeit < 3.1:
            return 3
        if schwierigkeit < 4.0:
            return 4
        return 5  # ["unbekannt", "sehr einfach, "einfach", "mittel", "schwer", "sehr schwer"][i] ??

    """ 
    itemtags has categories
        for Termine:
        "Aktionen, bei denen Rad gefahren wird" : getKategorie, e.g. Fahrrad-Demo, Critical Mass
        "Radlertreff / Stammtisch / Öffentliche Arbeits..." : getKategorie, e.g. Stammtisch
        "Serviceangebote": getKategorie, e.g. Codierung, Selbsthilfewerkstatt
        "Versammlungen" : getKategorie, e.g. Aktiventreff, Mitgliederversammlung
        "Vorträge & Kurse": getKategorie, e.g. Kurse, Radreisevortrag
        for Touren:
        "Besondere Charakteristik /Thema": getZusatzInfo
        "Besondere Zielgruppe" : getZusatzInfo
        "Geeignet für": getRadTyp
        "Typen (nach Dauer und Tageslage)" : getKategorie, e.g. Ganztagstour
        "Weitere Eigenschaften"  : getZusatzinfo, e.g. Bahnfahrt
    """

    def getMerkmale(self):
        merkmale = []
        for itemTag in self.itemTags:
            tag = itemTag.get("tag")
            merkmale.append(tag)
        return merkmale

    def getKategorie(self):
        for itemTag in self.itemTags:
            tag = itemTag.get("tag")
            category = itemTag.get("category")
            if category.startswith("Aktionen,") \
                    or category.startswith("Radlertreff") or category.startswith("Service") \
                    or category.startswith("Versammlungen") or category.startswith("Vortr") \
                    or category.startswith("Typen "):
                return tag
        return "Ohne"

    def getRadTyp(self):
        # wenn nur Rennrad oder nur Mountainbike, dann dieses, sonst Tourenrad
        rtCnt = 0
        for itemTag in self.itemTags:
            category = itemTag.get("category")
            if category.startswith("Geeignet "):
                rtCnt += 1
        for itemTag in self.itemTags:
            tag = itemTag.get("tag")
            category = itemTag.get("category")
            if category.startswith("Geeignet "):
                if rtCnt == 1 and (tag == "Rennrad" or tag == "Mountainbike"):
                    return tag
        return "Tourenrad"

    def getRadTypen(self):
        typen = []
        for itemTag in self.itemTags:
            tag = itemTag.get("tag")
            category = itemTag.get("category")
            if category.startswith("Geeignet "):
                typen.append(tag)
        return typen

    def getZusatzInfo(self):
        besonders = []
        weitere = []
        zielgruppe = []
        for itemTag in self.itemTags:
            tag = itemTag.get("tag")
            category = itemTag.get("category")
            if category == "Besondere Charakteristik /Thema":
                besonders.append(tag)
            if category == "Weitere Eigenschaften":
                weitere.append(tag)
            if category == "Besondere Zielgruppe":
                zielgruppe.append(tag)
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
        tl = self.eventItem.get("cTourLengthKm")
        return str(tl) + " km"

    def getHoehenmeter(self):
        h = self.eventItem.get("cTourHeight")
        return str(h)

    def getAnstiege(self):
        h = self.eventItem.get("cTourClimb")
        if 1 <= h <= 4:
            return anstiege[h-1]
        return "unbekannt"

    def getCharacter(self):
        c = self.eventItem.get("cTourSurface")
        return event.character[c]

    def getDatum(self):
        datum = self.eventItem.get("beginning")
        datum = event.convertToMEZOrMSZ(datum)
        # fromisoformat defined in Python3.7, not used by Scribus
        # date = datetime.fromisoformat(datum)
        logger.debug("datum <%s>", str(datum))
        day = str(datum[0:10])
        date = time.strptime(day, "%Y-%m-%d")
        weekday = event.weekdays[date.tm_wday]
        res = (weekday + ", " + day[8:10] + "." + day[5:7] + "." + day[0:4], event.getTime(datum), datum)
        return res

    def getDatumRaw(self):
        return self.eventItem.get("beginning")

    def getEndDatum(self):
        enddatum = self.eventItem.get("end")
        enddatum = event.convertToMEZOrMSZ(enddatum)
        # fromisoformat defined in Python3.7, not used by Scribus
        # enddatum = datetime.fromisoformat(enddatum)
        logger.debug("enddatum %s", str(enddatum))
        day = str(enddatum[0:10])
        date = time.strptime(day, "%Y-%m-%d")
        weekday = event.weekdays[date.tm_wday]
        res = (weekday + ", " + day[8:10] + "." + day[5:7] + "." + day[0:4], event.getTime(enddatum))
        return res

    def getEndDatumRaw(self):
        return self.eventItem.get("end")

    def getPersonen(self):
        personen = []
        organizer = self.eventItem.get("cOrganizingUserId")
        if organizer is not None and len(organizer) > 0:
            org = self.eventServer.getUser(organizer)
            if org is not None:
                personen.append(str(org))
        organizer2 = self.eventItem.get("cSecondOrganizingUserId")
        if organizer2 is not None and len(organizer2) > 0 and organizer2 != organizer:
            org = self.eventServer.getUser(organizer2)
            if org is not None:
                personen.append(str(org))
        return personen

    def getImagePreview(self):
        images = self.eventJS.get("images")
        if len(images) > 0:
            return images[0].get("preview")

    def getImageUrl(self):
        imageId = self.eventJS.get("eventItemImages")[0].get("imageId")
        return f"https://intern-touren-termine.adfc.de/api/images/{imageId}/download"

    def getImageStream(self, imageUrl, itemId):
        return self.eventServer.getImageStream(imageUrl, itemId)

    def getName(self):
        tourLoc = self.tourLocations[0]
        return tourLoc.get("name")

    def getCity(self):
        tourLoc = self.tourLocations[0]
        return tourLoc.get("city")

    def getStreet(self):
        tourLoc = self.tourLocations[0]
        return tourLoc.get("street")

    def getLatLon(self):
        tourLoc = self.tourLocations[0]
        return tourLoc.get("latitude"), tourLoc.get("longitude")

    def isExternalEvent(self):
        return self.eventItem.get("cExternalEvent") == "true"

    def getPublState(self):
        return self.eventItem.get("cStatus")

    def getPrices(self):
        minPrice = 9999999.0
        maxPrice = 0.0
        itemPrices = self.eventJS.get("eventItemPrices")
        if itemPrices is None or len(itemPrices) == 0:
            return None
        for itemPrice in itemPrices:
            price = itemPrice.get("price")
            if price < minPrice:
                minPrice = price
            if price > maxPrice:
                maxPrice = price
        return minPrice, maxPrice

    def getAnmeldung(self):
        rtype = self.eventItem.get("cRegistrationType")
        rurl = self.eventItem.get("cExternalRegistrationUrl")
        rstart = self.eventItem.get("registrationStart")
        max = self.eventItem.get("maximum")
        closDate = self.eventItem.get("closingDate")
        res = rtype
        if rstart is not None and rstart != "":
            rstart = event.convertToMEZOrMSZ(rstart)
            res += ", ab " + rstart
        res += ", max Teilnehmer: "
        if max == 0:
            res += "unbegrenzt"
        else:
            res += str(max)
        if closDate is not None and closDate != "":
            closDate = event.convertToMEZOrMSZ(closDate)
            closDate = closDate[8:10] + "." + closDate[5:7] + "." + closDate[0:4] + " " + event.getTime(closDate)
            res += ", Anmeldeschluss: " + closDate + " (" + self.getDatum()[0][4:9] + ")"
        if rurl != "":
            res += ", extUrl=" + rurl
        return res

    def getOrganizer(self):
        organizer = self.eventItem.get("cOrganizingUserId")
        if organizer is not None and len(organizer) > 0:
            org = self.eventServer.getUser(organizer)
            if org is not None:
                return org.firstName + " " + org.lastName
        return "?"

    def getOrganizer2(self):
        organizer2 = self.eventItem.get("cSecondOrganizingUserId")
        if organizer2 is not None and len(organizer2) > 0:
            org = self.eventServer.getUser(organizer2)
            if org is not None:
                return org.firstName + " " + org.lastName
        return "?"


class User:
    def __init__(self, userJS):
        u = userJS.get("user")
        self.firstName = u.get("firstName")
        self.lastName = u.get("lastName")
        try:
            self.phone = u.get("cellPhone")
            if self.phone is None or self.phone == "":
                self.phone = userJS.get("temporaryContacts")[0].get("phone")
        except Exception:
            self.phone = None

    def __repr__(self):
        name = self.firstName + " " + self.lastName
        if self.phone is not None and self.phone != "":
            name += " (" + self.phone + ")"
        return name
