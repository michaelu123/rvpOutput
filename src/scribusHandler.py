# encoding: utf-8
import sys

from myLogger import logger

try:
    import scribus
except ModuleNotFoundError:
    raise ImportError

if True:
    yOrN = scribus.valueDialog("UseRest", "Sollen aktuelle Daten vom Server geholt werden? (j/n)").lower()[0]
    useRest = yOrN == 'j' or yOrN == 'y' or yOrN == 't'
    yOrN = scribus.valueDialog("IncludeSub", "Sollen Untergliederungen einbezogen werden? (j/n)").lower()[0]
    includeSub = yOrN == 'j' or yOrN == 'y' or yOrN == 't'
    eventType = scribus.valueDialog("Typ", "Typ (R=Radtour, T=Termin, A=Alles) (R/T/A)")
    radTyp  = scribus.valueDialog("Fahrradtyp", "Fahrradtyp (R=Rennrad, T=Tourenrad, M=Mountainbike, A=Alles) (R/T/M/A)")
    unitKeys = scribus.valueDialog("Gliederung(en)", "Bitte Nummer(n) der Gliederung angeben (komma-separiert)")
    start = scribus.valueDialog("Startdatum", "Startdatum (TT.MM.YYYY)")
    end = scribus.valueDialog("Endedatum", "Endedatum (TT.MM.YYYY)")
else:
    useRest = False
    includeSub = False
    eventType = "R"
    radTyp = "A"
    unitKeys="152085"
    start="01.04.2022"
    end="31.04.2022"

class ScribusHandler:
    def __init__(self):
        if not scribus.haveDoc():
            scribus.messageBox('Scribus - Script Error', "No document open", scribus.ICON_WARNING, scribus.BUTTON_OK)
            sys.exit(1)

        if scribus.selectionCount() == 0:
            scribus.messageBox('Scribus - Script Error',
                               "There is no object selected.\nPlease select a text frame and try again.",
                               scribus.ICON_WARNING, scribus.BUTTON_OK)
            sys.exit(2)
        if scribus.selectionCount() > 1:
            scribus.messageBox('Scribus - Script Error',
                               "You have more than one object selected.\nPlease select one text frame and try again.",
                               scribus.ICON_WARNING, scribus.BUTTON_OK)
            sys.exit(2)

        self.textbox = scribus.getSelectedObject()
        ftype = scribus.getObjectType(self.textbox)

        if ftype != "TextFrame":
            scribus.messageBox('Scribus - Script Error', "This is not a textframe. Try again.", scribus.ICON_WARNING,
                               scribus.BUTTON_OK)
            sys.exit(2)

        scribus.deleteText(self.textbox)
        self.insertPos = 0
        self.lastPStyle = ""
        self.insertText('Radtouren\n', 'Radtouren_titel')

    def insertText(self, text, pStyle):
        if text is None or text == "":
            return
        pos = self.insertPos
        scribus.insertText(text, pos, self.textbox)
        tlen = len(text)
        if pStyle is None:
            pStyle = self.lastPStyle
        # if cStyle is None:
        #   cStyle = self.lastCStyle
        scribus.selectText(pos, tlen, self.textbox)
        scribus.setParagraphStyle(pStyle, self.textbox)
        self.lastPStyle = pStyle
        # scribus.setCharacterStyle(cStyle, self.textbox)
        # self.lastCStyle = cStyle
        self.insertPos += tlen

    def getUseRest(self):
        return useRest
    def getIncludeSub(self):
        return includeSub
    def getUnitKeys(self):
        return unitKeys
    def getStart(self):
        return start
    def getEnd(self):
        return end
    def getEventType(self):
        return eventType
    def getRadTyp(self):
        return radTyp

    # def addStyle(self, style, frame):
    #      try:
    #          scribus.setParagraphStyle(style, frame)
    #      except scribus.NotFoundError:
    #          scribus.createParagraphStyle(style)
    #          scribus.setParagraphStyle(style, frame)

    def nothingFound(self):
        logger.info("Nichts gefunden")
        self.insertText("Nichts gefunden\n", None)

    def handleAbfahrt(self, abfahrt):
        # abfahrt = (type, beginning, loc)
        typ = abfahrt[0]
        uhrzeit = abfahrt[1]
        ort = abfahrt[2]
        logger.info("Abfahrt: type=%s uhrzeit=%s ort=%s", typ, uhrzeit, ort)
        self.insertText(typ + (': '+uhrzeit if uhrzeit != "" else "")+', '+ort+'\n', 'Radtour_start')

    def handleTextfeld(self, stil,textelement):
        logger.info("Textfeld: stil=%s text=%s", stil, textelement)
        if textelement != None:
            zeilen = textelement.split("\n")
            self.handleTextfeldList(stil, zeilen)

    def handleTextfeldList(self, stil, textList):
        logger.info("TextfeldList: stil=%s text=%s", stil, str(textList))
        for text in textList:
            if len(text) == 0:
                continue
            logger.info("Text: stil=%s text=%s", stil, text)
            self.insertText(text+'\n', stil)

    def handleTel(self, Name):
        telfestnetz = Name.getElementsByTagName("TelFestnetz")
        telmobil = Name.getElementsByTagName("TelMobil")
        if len(telfestnetz)!=0:
            logger.info("Tel: festnetz=%s", telfestnetz[0].firstChild.data)
            self.insertText(' ('+telfestnetz[0].firstChild.data+')', None)
        if len(telmobil)!=0:
            logger.info("Tel: mobil=%s", telmobil[0].firstChild.data)
            self.insertText(' ('+telmobil[0].firstChild.data+')', None, self.textbox)

    def handleName(self, name):
        logger.info("Name: name=%s", name)
        self.insertText(name, None, self.textbox)
        # handleTel(name) ham wer nich!

    def handleTourenleiter(self, TLs):
        self.insertText('Tourenleiter: ', 'Radtour_tourenleiter')
        names = ", ".join(TLs)
        self.insertText(names + '\n', None)

    def handleTitel(self, tt):
        logger.info("Titel: titel=%s", tt)
        self.insertText(tt+'\n', 'Radtour_titel')

    def handleKopfzeile(self, dat, kat, schwierig, strecke):
        logger.info("Kopfzeile: dat=%s kat=%s schwere=%s strecke=%s", dat, kat, schwierig, strecke)
        self.insertText(dat+':	'+kat+'	'+schwierig+'	'+strecke+'\n', 'Radtour_kopfzeile')

    def handleKopfzeileMehrtage(self, anfang, ende, kat, schwierig, strecke):
        logger.info("Mehrtage: anfang=%s ende=%s kat=%s schwere=%s strecke=%s", anfang, ende, kat, schwierig, strecke)
        self.insertText(anfang+' bis '+ende+':\n', 'Radtour_kopfzeile')
        self.insertText('	'+kat+'	'+schwierig+'	'+strecke+'\n', 'Radtour_kopfzeile')

    def handleTour(self, tour):
        try:
            titel = tour.getTitel()
            logger.info("Title %s", titel)
            datum = tour.getDatum()[0]
            logger.info("datum %s", datum)

            abfahrten = tour.getAbfahrten()
            if len(abfahrten) == 0:
                raise ValueError("kein Startpunkt in tour %s", titel)
            logger.info("abfahrten %s ", str(abfahrten))

            beschreibung = tour.getBeschreibung(False)
            logger.info("beschreibung %s", beschreibung)
            zusatzinfo = tour.getZusatzInfo()
            logger.info("zusatzinfo %s", str(zusatzinfo))
            kategorie = tour.getKategorie()
            radTyp = tour.getRadTyp()
            logger.info("kategorie %s radTyp %s", kategorie, radTyp)
            if kategorie == "Feierabendtour":
                schwierigkeit = "F"
            elif radTyp == "Rennrad":
                schwierigkeit = "RR"
            elif radTyp == "Mountainbike":
                schwierigkeit = "MTB"
            else:
                schwierigkeit = str(tour.getSchwierigkeit())
            if schwierigkeit == "0":
                schwierigkeit = "1"
            if schwierigkeit >= "1" and schwierigkeit <= "5":
                schwierigkeit = "*" * int(schwierigkeit)
            logger.info("schwierigkeit %s", schwierigkeit)
            strecke = tour.getStrecke()
            logger.info("strecke %s", strecke)

            if kategorie == 'Mehrtagestour':
                enddatum = tour.getEndDatum()[0]
                logger.info("enddatum %s", enddatum)

            personen = tour.getPersonen()
            logger.info("personen %s", str(personen))
            if len(personen) == 0:
                logger.error("Tour %s hat keinen Tourleiter", titel)
        except Exception as e:
            logger.exception("Fehler in der Tour %s: %s", titel, e)
            return

        self.insertText('\n', None)
        if kategorie == 'Mehrtagestour':
            self.handleKopfzeileMehrtage(datum, enddatum, kategorie, schwierigkeit, strecke)
        else:
            self.handleKopfzeile(datum, kategorie, schwierigkeit, strecke)
        self.handleTitel(titel)
        for abfahrt in abfahrten:
            self.handleAbfahrt(abfahrt)
        self.handleTextfeld('Radtour_beschreibung',beschreibung)
        self.handleTourenleiter(personen)
        self.handleTextfeldList('Radtour_zusatzinfo',zusatzinfo)

    def handleTermin(self, tour):
        pass
