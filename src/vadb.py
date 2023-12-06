import json
import math
import random
import re
from datetime import datetime
from decimal import getcontext
from string import digits, ascii_uppercase

decCtx = getcontext()
decCtx.prec = 7  # 5.2 digits, max=99999.99
charset = digits + ascii_uppercase
maxLatLonDiff = 0.005
maxDist = 100  # meters

paramRE = re.compile(r"\${(\w*?)}")


def distance(origin, destination):
    """
    Calculate the Haversine distance.

    Parameters
    ----------
    origin : tuple of float
        (lat, long)
    destination : tuple of float
        (lat, long)

    Returns
    -------
    distance_in_km : float

    Examples
    --------
    >>> origin = (48.1372, 11.5756)  # Munich
    >>> destination = (52.5186, 13.4083)  # Berlin
    >>> round(distance(origin, destination), 1)
    504.2
    """
    lat1, lon1 = origin
    lat2, lon2 = destination
    radius = 6371  # km

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) * math.sin(dlon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = radius * c * 1000.0  # return meters
    return d


def randomId(length):
    r1 = random.choice(ascii_uppercase)  # first a letter
    r2 = [random.choice(charset) for _ in range(length - 1)]  # then any mixture of capitalletters and numbers
    return r1 + ''.join(r2)


def expTitel(tour):
    return tour.getTitel().replace("]]>", "")


def expEventItemId(tour):
    return tour.getEventItemId()


def expKurz(tour):
    kurz = "<p>" + tour.getKurzbeschreibung() + "<br>Kategorie: " + tour.getKategorie() + "<br>Geeignet für: " + \
           tour.getRadTyp() + "<br>" + "<br>".join(tour.getZusatzInfo()) + "<br>Schwierigkeitsgrad: " + \
           ["unbekannt", "sehr einfach", "einfach", "mittel", "schwer", "sehr schwer"][tour.getSchwierigkeit()] + "</p>"
    kurz = kurz.replace("<br><br>", "<br>").replace("]]>", "")
    return kurz


def expFrontendLink(tour):
    return tour.getFrontendLink()


def expPublishDate(tour):
    return tour.getPublishDate().replace("T", " ")


def expDate(tour):
    t = tour.getDatum()
    return t[2][0:10]  # YYY-MM-DD


def expTime(tour):
    t = tour.getDatum()
    return t[1]


def expDuration(tour):
    b = tour.getDatumRaw()
    b = b[0:19]  # '2018-04-29T06:30:00'
    b = datetime.strptime(b, "%Y-%m-%dT%H:%M:%S")
    e = tour.getEndDatumRaw()
    e = e[0:19]  # '2018-04-29T07:30:00'
    e = datetime.strptime(e, "%Y-%m-%dT%H:%M:%S")
    d = e - b  # a timedelta!
    d = d.total_seconds() / 60  # timedelta in minutes
    return str(int(d))


def expImageUrl(tour):
    return tour.getImageUrl()


def expOrtsname(tour):
    t = tour.getStartpunkt()
    if t[0] != "":
        return t[0]  # name
    return t[2]  # city


def expCity(tour):
    t = tour.getStartpunkt()
    return t[2]  # city


def expStreet(tour):
    t = tour.getStartpunkt()
    return t[1]  # street


def expLatitude(tour):
    t = tour.getStartpunkt()
    return str(t[3])  # latitude


def expLongitude(tour):
    t = tour.getStartpunkt()
    return str(t[4])  # longitude


def expPricing(tour):
    maxPrice = 0.0
    prices = tour.getPrices()
    if prices is not None:
        (minPrice, maxPrice) = prices
    if prices is None or maxPrice == 0.0:
        return ["           <freeOfCharge>true</freeOfCharge>\n"]
    else:
        return [
            f"        <fromPrice>€{minPrice}</fromPrice>\n",
            f"        <toPrice>€{maxPrice}</toPrice>\n",
        ]


def expCategories(_tour):  # wir belassen es erstmal bei Category Radtouren
    return ['        <Category id="36"/>\n']


def readPOIs():
    with open("locs.json", "r", encoding="utf-8") as jsonFile:
        pois = json.load(jsonFile)
        return pois


class VADBHandler:
    def __init__(self, tourServerVar):
        self.tourServerVar = tourServerVar
        self.expFunctions = {  # keys in lower case
            "titel": expTitel,
            "eventItemId": expEventItemId,
            "publishDate": expPublishDate,
            "kurz": expKurz,
            "frontendLink": expFrontendLink,
            "date": expDate,
            "time": expTime,
            "duration": expDuration,
            "imageUrl": expImageUrl,
            "ortsname": expOrtsname,
            "latitude": expLatitude,
            "longitude": expLongitude,
            "street": expStreet,
            "city": expCity,
            "copyright": self.expCopyRight,
            "addressPoi": self.expPoi,
            "<ExpandCategories/>": expCategories,
            "<ExpandPricing/>": expPricing,
        }

        self.xmlFile = "./ADFC_VADB_template.xml"
        self.outputFile = "./ADFC-VADB.xml"
        self.output = open(self.outputFile, "w", encoding="utf-8")
        self.addressPOIs = readPOIs()
        self.unknownLocs = self.readUnknownLocs()
        pass

    def expandCmd(self, tour, cmd):
        f = self.expFunctions.get(cmd)
        if f is None:
            return "???" + cmd + "???"
        return f(tour)

    def __enter__(self):
        self.output.write("<events>\n")
        return self

    def __exit__(self, *args):
        self.output.write("</events>\n")
        self.output.close()

    def handleTermin(self, termin):
        pass

    def handleTour(self, tour):
        # print(tour.getLatLon(), tour.getName(), tour.getCity(), tour.getStreet())
        # print(tour.getZusatzInfo());
        # print(tour.getMerkmale())
        # print(self.expCopyRight(tour))
        # if True: return
        if self.expPoi(tour) == "6137":
            return
        with open(self.xmlFile, "r", encoding="utf-8") as input:
            for line in input:
                mp = paramRE.search(line, 0)
                if mp is not None:
                    sp = mp.span()
                    cmd = line[sp[0] + 2:sp[1] - 1]
                    line = line[0:sp[0]] + self.expandCmd(tour, cmd) + line[sp[1]:]
                    self.output.writelines([line])
                elif line.find("<Expand") > 0:
                    ll = self.expandCmd(tour, line.strip())
                    self.output.writelines(ll)
                else:
                    self.output.writelines([line])

    def expCopyRight(self, tour):
        try:
            content = self.tourServerVar.readCopyRight(tour.getSlug(), tour.getFrontendLink())
            x = content.find(b'copyright')
            if x >= 0:
                s = content[x:x + 100].decode("utf-8")
                s = s.replace("\\", "")
                x = s.find(':"')
                y = s.find('"', x + 2)
                return (s[x + 2:y]).replace("]]>", "")
        except:
            return "ADFC"

    def findNearestPoiId(self, lat, lon):
        minDist = maxDist
        minPoi = None
        for poi in self.addressPOIs:
            plat = poi.get("latitude")
            plon = poi.get("longitude")
            if abs(lat - plat) > maxLatLonDiff or abs(lon - plon) > maxLatLonDiff:
                d = maxDist
            else:
                d = distance((lat, lon), (plat, plon))
            if d < minDist:
                minDist = d
                minPoi = poi
        return minPoi.get("poi") if minPoi is not None else None

    def expPoi(self, tour):
        (tlat, tlon) = tour.getLatLon()
        nid = self.findNearestPoiId(tlat, tlon)
        if id is not None:
            return str(nid)
        ort = tour.getStartpunkt()
        self.unknownLocs[str(tlat) + "," + str(tlon)] = {
            "link": tour.getFrontendLink(),
            "name": ort[0] if ort[0] != "" else ort[2],
            "city": ort[2],
            "street": ort[1]
        }
        with open("unknown_locs.json", "w") as jsonFile:
            json.dump(self.unknownLocs, jsonFile, indent=4)
        return "6137"

    def readUnknownLocs(self):
        newUL = {}
        try:
            with open("unknown_locs.json", "r", encoding="utf-8") as jsonFile:
                unknownLocs = json.load(jsonFile)
            # are any unknownlocs in the possibly enhanced locs.json? If yes, remove
            for ul in unknownLocs.keys():
                (lat, lon) = ul.split(',')
                (lat, lon) = (float(lat), float(lon))
                if self.findNearestPoiId(lat, lon) is None:
                    newUL[ul] = unknownLocs[ul]
            if len(newUL) != len(unknownLocs):
                unknownLocs = newUL
                with open("unknown_locs.json", "w") as jsonFile:
                    json.dump(self.unknownLocs, jsonFile, indent=4)
        except:
            unknownLocs = {}
        return unknownLocs


"""
Categories Expansion:
        <Category id="2">
            <i18nName>
                <I18n id="11">
                    <de>
                        <![CDATA[ Bühnenkunst ]]>
                    </de>
                    <en>
                        <![CDATA[ Stage Art ]]>
                    </en>
                </I18n>
            </i18nName>
        </Category>
        <Category id="3">
            <i18nName>
                <I18n id="12">
                    <de>
                        <![CDATA[ Theater ]]>
                    </de>
                    <en>
                        <![CDATA[ Theatre ]]>
                    </en>
                </I18n>
            </i18nName>
        </Category>
        <Category id="8">
            <i18nName>
                <I18n id="17">
                    <de>
                        <![CDATA[ Lesungen ]]>
                    </de>
                    <en>
                        <![CDATA[ Reading ]]>
                    </en>
                </I18n>
            </i18nName>
        </Category>
        
???        
    <criteria>
        <!-- IDs depend upon customer project -->
        <Criterion id="1"/>
        <Criterion id="2"/>
    </criteria>

pricing??    
        <fromPrice>$5.0</fromPrice>
        <toPrice>10.0</toPrice>
        <absolutePrice>15.0</absolutePrice>
        <freeOfCharge>false</freeOfCharge>
        <priceDescription>
            <I18n>
                <de>
                    <![CDATA[priceDescription]]>
                </de>
            </I18n>
        </priceDescription>
        
    <bookingLink>
        <!-- has to be a valid URL -->
        <I18n>
            <de>
                <![CDATA[http://www.booking-link.de]]>
            </de>
            <en>
                <![CDATA[http://www.booking-link.en]]>
            </en>
        </I18n>
    </bookingLink>

https://intern-touren-termine.adfc.de/api/images/2b6a400f-d5ac-46bf-9133-b53ecd5a180c/download
https://intern-touren-termine.adfc.de/api/images/7e0249e0-0d44-42cf-93b5-5a0f3b76a9ed/download
https://intern-touren-termine.adfc.de/api/images/3e53feb6-3ce3-4b21-9c09-6744a02b7c94/download

imageTitle?? imageDescription?
                   <title>
                        <I18n>
                            <de>
                                <![CDATA[${imageTitle}]]>
                            </de>
                        </I18n>
                    </title>
                    <description>
                        <I18n>
                            <de>
                                <![CDATA[image-description]]>
                            </de>
                        </I18n>
                    </description>
imageType?? 
             <imageType>
                <!-- note: depending on customer project -->
                <ImageType id="1"/>
            </imageType>

<!--
fehlend in shmh:
entityState
client
creationTime
lastChangeTime
bookingLink ist leer
        <categories>
            <Category id="116"/>
        </categories>
        <criteria>
            <Criterion id="135"/>
        </criteria>
        <pricing/>

        <duration>
           <![CDATA[ ]]>??? anstatt 3:45?
        </duration>

        <copyright>
            <I18n>
                <de>Stiftung Historische Museen Hamburg</de>
            </I18n>

        <location>
            <AddressPoi id="811"/>
        </location>
        <contributor>
            <AddressPoi id="811"/>
        </contributor>


locid 6137
contr 6137

-->


"""
