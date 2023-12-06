# encoding: utf-8
import functools

import http.client as httplib
from concurrent.futures.thread import ThreadPoolExecutor
import threading
import json
import os
import sys
import ssl
from io import BytesIO
from urllib.request import urlopen
from urllib.parse import urlparse

import adfc_gliederungen
import tourRest
import event
from myLogger import logger


class EventServer:
    def __init__(self, useRest, includeSub, max_workers):
        self.tmpDir = "/tmp/tpjson" if sys.platform.startswith('linux') else "c:/temp/tpjson"
        self.useRest = useRest
        self.includeSub = includeSub
        self.max_workers = max_workers
        self.tpConns = []
        self.tpConnsLock = threading.Lock()
        self.events = {}
        self.alleTouren = []
        self.alleTermine = []

        try:
            os.makedirs(self.tmpDir)  # exist_ok = True does not work with Scribus (Python 2)
        except:
            pass
        self.getUser = functools.lru_cache(maxsize=100)(self.getUser)
        self.loadUnits()

    def getConn(self):
        with self.tpConnsLock:
            try:
                conn = self.tpConns.pop()
            except:
                conn = None
        if conn is None:
            ctx = ssl._create_default_https_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            conn = httplib.HTTPSConnection("api-touren-termine.adfc.de", context=ctx)
        return conn

    def putConn(self, conn):
        if conn is None:
            return
        with self.tpConnsLock:
            self.tpConns.insert(0, conn)

    def getEvents(self, unitKey, start, end, typ):
        unit = "Alles" if unitKey is None or unitKey == "" else unitKey
        startYear = int(start[0:4])
        endYear = int(end[0:4])
        events = []
        for yearI in range(startYear, endYear + 1):
            yearS = str(yearI)
            jsonPath = self.tmpDir + "/search-" + unit + ("_I_" if self.includeSub else "_") + yearS + ".json"
            if self.useRest or not os.path.exists(jsonPath):
                req = "/api/eventItems/search?limit=10000"
                par = ""
                if unitKey is not None and unitKey != "":
                    par += "&unitKey=" + unitKey
                    if self.includeSub:
                        par += "&includeSubsidiary=true"
                par += "&beginning=" + yearS + "-01-01"
                par += "&end=" + yearS + "-12-31"
                req += par
                resp, conn = self.httpget(req)
                if resp is None:
                    jsRoot = {}
                else:
                    jsRoot = json.load(resp)
                self.putConn(conn)
            else:
                resp = None
                with open(jsonPath, "r") as jsonFile:
                    jsRoot = json.load(jsonFile)
            if resp is not None:  # a REST call result always overwrites jsonPath
                with open(jsonPath, "w") as jsonFile:
                    json.dump(jsRoot, jsonFile, indent=4)
            items = jsRoot.get("items")
            if items is None or len(items) == 0:
                continue
            for item in iter(items):
                titel = item.get("title")
                if titel is None:
                    logger.error("Kein Titel für den Event %s", str(item))
                    continue
                if item.get("cStatus") == "Cancelled" or item.get("isCancelled"):
                    logger.info("Event %s ist gecancelt", titel)
                    continue
                if typ != "Alles" and item.get("eventType") != typ:
                    continue
                beginning = item.get("beginning")
                if beginning is None:
                    logger.error("Kein Beginn für den Event %s", titel)
                    continue
                begDate = beginning[0:4]
                if begDate < start[0:4] or begDate > end[0:4]:
                    continue
                if item.get("eventType") == "Radtour":
                    self.alleTouren.append(item)
                else:
                    self.alleTermine.append(item)
                begDate = event.convertToMEZOrMSZ(beginning)[0:10]
                if begDate < start or begDate > end:
                    logger.info("event " + titel + " not in timerange")
                    continue
                # add other filter conditions here
                logger.info("event " + titel + " OK")
                events.append(item)
        return events

    def getEvent(self, eventJsSearch):
        eventItemId = eventJsSearch.get("eventItemId")
        event = self.events.get(eventItemId)
        if event is not None:
            return event
        escTitle = "".join([(ch if ch.isalnum() else "_") for ch in eventJsSearch.get("title")])
        jsonPath = self.tmpDir + "/" + eventItemId[0:6] + "_" + escTitle + ".json"
        if self.useRest or not os.path.exists(jsonPath):
            resp, conn = self.httpget("/api/eventItems/" + eventItemId)
            if resp is None:
                eventJS = {}
            else:
                eventJS = json.load(resp)
            self.putConn(conn)
            eventJS["eventItemFiles"] = None  # save space
            #eventJS["images"] = []  # save space
            # if not os.path.exists(jsonPath):
            with open(jsonPath, "w") as jsonFile:
                json.dump(eventJS, jsonFile, indent=4)
            if resp is None:
                return None
        else:
            with open(jsonPath, "r") as jsonFile:
                try:
                    eventJS = json.load(jsonFile)
                except:
                    print("cannot parse " + jsonPath)
                    return None
        event = tourRest.RestEvent(eventJS, eventJsSearch, self)
        self.events[eventItemId] = event
        return event

    def getEventById(self, eventItemId, titel):
        ejs = {"eventItemId": eventItemId, "title": titel}
        return self.getEvent(ejs)

    def getImageStream(self, imageUrl, itemId):
        res = urlparse(imageUrl)
        x = res.path.rindex("/")
        imgPath = self.tmpDir + "/img_" + itemId[0:6] + "_" + res.path[x+1:]
        if self.useRest or not os.path.exists(imgPath):
            barr = urlopen(imageUrl).read()
            with open(imgPath, "wb") as imgFile:
                imgFile.write(barr)
        else:
            with open(imgPath, "rb") as imgFile:
                barr = imgFile.read()
        return BytesIO(barr)

    @functools.lru_cache(100)
    def getUser(self, userId):
        jsonPath = self.tmpDir + "/user_" + userId + ".json"
        if self.useRest or not os.path.exists(jsonPath):
            resp, conn = self.httpget("/api/users/" + userId)
            if resp is None:
                self.putConn(conn)
                return None
            userJS = json.load(resp)
            self.putConn(conn)
            userJS["simpleEventItems"] = None
            # if not os.path.exists(jsonPath):
            with open(jsonPath, "w") as jsonFile:
                json.dump(userJS, jsonFile, indent=4)
        else:
            with open(jsonPath, "r") as jsonFile:
                userJS = json.load(jsonFile)
        user = tourRest.User(userJS)
        return user

    def loadUnits(self):
        jsonPath = self.tmpDir + "/units.json"
        if not os.path.exists(jsonPath):
            resp, conn = self.httpget("/api/units/")
            if resp is None:
                self.putConn(conn)
                return None
            unitsJS = json.load(resp)
            self.putConn(conn)
            with open(jsonPath, "w") as jsonFile:
                json.dump(unitsJS, jsonFile, indent=4)
        else:
            with open(jsonPath, "r", encoding="utf-8") as jsonFile:
                unitsJS = json.load(jsonFile)
        adfc_gliederungen.load(unitsJS)

    def calcNummern(self):
        # too bad we base numbers on kategorie and radtyp,which we cannot get from the search result
        ThreadPoolExecutor(max_workers=self.max_workers).map(self.getEvent, self.alleTouren)
        self.alleTouren.sort(key=lambda x: x.get("beginning"))  # sortieren nach Datum
        yyyy = ""
        logger.info("Begin calcNummern")
        for tourJS in self.alleTouren:
            datum = tourJS.get("beginning")
            if datum[0:4] != yyyy:
                yyyy = datum[0:4]
                tnum = 100
                rnum = 300
                mnum = 400
                mtnum = 600
            tour = self.getEvent(tourJS)
            if tour is None:
                continue
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
            tourJS["eventNummer"] = str(num)

        self.alleTermine.sort(key=lambda x: x.get("beginning"))  # sortieren nach Datum
        yyyy = ""
        for tourJS in self.alleTermine:
            datum = tourJS.get("beginning")
            if datum[0:4] != yyyy:
                yyyy = datum[0:4]
                tnum = 700
            num = tnum
            tnum += 1
            tourJS["eventNummer"] = str(num)
        logger.info("End calcNummern")

    def httpget(self, req):
        conn = None
        for retries in range(2):
            try:
                conn = self.getConn()
                conn.request("GET", req)
            except Exception as e:
                logger.exception("error in request " + req)
                if isinstance(e, httplib.CannotSendRequest):
                    conn.close()
                    conn = None
                    continue
            try:
                resp = conn.getresponse()
            except Exception as e:
                logger.exception("cannot get response for " + req)
                if isinstance(e, httplib.ResponseNotReady):
                    conn.close()
                    conn = None
                    continue
            break
        try:
            if resp.status >= 300:
                logger.error("request %s failed: code %s reason %s: %s", req, resp.status, resp.reason, resp.read())
                return None
            else:
                logger.debug("resp %d %s", resp.status, resp.reason)
        except:
            pass
        return (resp, conn)

    def readCopyRight(self, cslug, link):
        path = self.tmpDir + "/" + cslug + "_copyright"
        if self.useRest or not os.path.exists(path):
            resp, conn = self.httpget(link)
            if resp is None:
                content = ""
            else:
                content = resp.read()
                x = content.find(b'copyright')
                if x > 0:
                    content = content[x:x + 100]
                else:
                    content = b""
            self.putConn(conn)
            with open(path, "wb") as outFile:
                outFile.write(content)
            if resp is None:
                return None
        else:
            with open(path, "rb") as inFile:
                try:
                    content = inFile.read()
                except:
                    print("cannot read " + path)
                    return None
        return content

    """

    {"tourLocations": [
    {"id": 18884, "eventItemId": "6c58408b-4780-4246-9d3a-afbcece318fc", "position": 0, "type": "Startpunkt",
     "name": "", "street": "Alte Utting, Lagerhausstr. 15", "city": "München", "zipCode": "81371",
     "latitude": 48.119942, "longitude": 11.556277, "beginning": "2020-01-28T18:00:00+00:00", "end": null,
     "created": "2019-12-13T12:03:26.273+00:00", "createUser": "michael.uhlenberg@adfc-bayern.de",
     "lastUpdate": "2019-12-13T12:06:58.32+00:00", "lastUser": "michael.uhlenberg@adfc-bayern.de",
     "location": {"isNull": false, "stSrid": 4326, "lat": 48.119942, "long": 11.556277, "z": null, "m": null,
                  "hasZ": false, "hasM": false}, "withoutTime": false, "seriesIdentifier": null,
     "locationIdentifier": "11c1ea10-11be-4850-bf6d-a8c66cff643c",
     "tourLocationId": "3cffe7c8-7221-499e-9050-327000a5911d"}], "eventItemFiles": [], "eventItemImages": [
    {"imageId": "274626dc-eb55-4daa-ac6e-f0e801e423b1", "eventItemId": "6c58408b-4780-4246-9d3a-afbcece318fc",
     "seriesIdentifier": "4d929539-a780-4dcb-97c1-00aebf0b2ee3", "id": 20033}], "images": [
    {"id": 9321, "fileName": "AlteUtting.jpg", "copyright": "alte-utting.de",
     "downloadLink": "https://adfcrtp.blob.core.cloudapi.de/public-production/274626dc-eb55-4daa-ac6e-f0e801e423b1/alteutting.jpg",
     "blobName": "274626dc-eb55-4daa-ac6e-f0e801e423b1/alteutting.jpg", "preview": ""}

https://touren-termine.adfc.de/radveranstaltung/23312-winterprogramm-radtour-von-munchen-nach-teheran
irgendwo im response steht:
			{"tourLocations":[{"id":18884,"eventItemId":"6c58408b-4780-4246-9d3a-afbcece318fc","position":0,"type":"Startpunkt","name":"","street":"Alte Utting, Lagerhausstr. 15","city":"München","zipCode":"81371","latitude":48.119942,"longitude":11.556277,"beginning":"2020-01-28T18:00:00+00:00","end":null,"created":"2019-12-13T12:03:26.273+00:00","createUser":"michael.uhlenberg@adfc-bayern.de","lastUpdate":"2019-12-13T12:06:58.32+00:00","lastUser":"michael.uhlenberg@adfc-bayern.de","location":{"isNull":false,"stSrid":4326,"lat":48.119942,"long":11.556277,"z":null,"m":null,"hasZ":false,"hasM":false},"withoutTime":false,"seriesIdentifier":null,"locationIdentifier":"11c1ea10-11be-4850-bf6d-a8c66cff643c","tourLocationId":"3cffe7c8-7221-499e-9050-327000a5911d"}],"eventItemFiles":[],"eventItemImages":[{"imageId":"274626dc-eb55-4daa-ac6e-f0e801e423b1","eventItemId":"6c58408b-4780-4246-9d3a-afbcece318fc","seriesIdentifier":"4d929539-a780-4dcb-97c1-00aebf0b2ee3","id":20033}],"images":[{"id":9321,"fileName":"AlteUtting.jpg","copyright":"alte-utting.de","downloadLink":"https://adfcrtp.blob.core.cloudapi.de/public-production/274626dc-eb55-4daa-ac6e-f0e801e423b1/alteutting.jpg","blobName":"274626dc-eb55-4daa-ac6e-f0e801e423b1/alteutting.jpg","preview":""}
			
    """
