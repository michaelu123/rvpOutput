# encoding: utf-8

# printHandler produziert output a la KV Starnberg
from myLogger import logger


class DatenTest:  # just log data
    def insertText(self, text):
        logger.info(text)
        print(text, end="")


class PrintHandler:
    def __init__(self):
        self.scribus = DatenTest()

    def nothingFound(self):
        logger.info("Nichts gefunden")
        self.scribus.insertText("Nichts gefunden\n")

    def handleAbfahrt(self, abfahrt):
        # abfahrt = (typ, beginning, loc)
        typ = abfahrt[0]
        uhrzeit = abfahrt[1]
        ort = abfahrt[2]
        logger.info("Abfahrt: type=%s uhrzeit=%s ort=%s", typ, uhrzeit, ort)
        self.scribus.insertText(typ + (': ' + uhrzeit if uhrzeit != "" else "") + ', ' + ort + '\n')

    def handleTextfeld(self, textelement):
        logger.info("Textfeld: text=%s", textelement)
        if textelement is not None:
            self.scribus.insertText(textelement + '\n')

    def handleTextfeldList(self, textList):
        logger.info("TextfeldList: text=%s", str(textList))
        for text in textList:
            if len(text) == 0:
                continue
            logger.info("Text: text=%s", text)
            self.scribus.insertText(text + '\n')

    def handleBeschreibung(self, textelement):
        self.handleTextfeld(textelement)

    def handleTel(self, Name):
        telfestnetz = Name.getElementsByTagName("TelFestnetz")
        telmobil = Name.getElementsByTagName("TelMobil")
        if len(telfestnetz) != 0:
            logger.info("Tel: festnetz=%s", telfestnetz[0].firstChild.data)
            self.scribus.insertText(' (' + telfestnetz[0].firstChild.data + ')')
        if len(telmobil) != 0:
            logger.info("Tel: mobil=%s", telmobil[0].firstChild.data)
            self.scribus.insertText(' (' + telmobil[0].firstChild.data + ')')

    def handleName(self, name):
        logger.info("Name: name=%s", name)
        self.scribus.insertText(name)
        # self.handleTel(name) ham wer nich!

    def handleTourenleiter(self, TLs):
        self.scribus.insertText('Tourenleiter: ')
        names = ", ".join(TLs)
        self.scribus.insertText(names)
        self.scribus.insertText('\n')

    def handleTitel(self, tt):
        logger.info("Titel: titel=%s", tt)
        self.scribus.insertText(tt + '\n')

    def handleKopfzeile(self, dat, kat, schwierig, strecke):
        logger.info("Kopfzeile: dat=%s kat=%s schwere=%s strecke=%s", dat, kat, schwierig, strecke)
        self.scribus.insertText(dat + ':	' + kat + '	' + schwierig + '	' + strecke + '\n')

    def handleKopfzeileMehrtage(self, anfang, ende, kat, schwierig, strecke):
        logger.info("Mehrtage: anfang=%s ende=%s kat=%s schwere=%s strecke=%s", anfang, ende, kat, schwierig, strecke)
        self.scribus.insertText(anfang + ' bis ' + ende + ':\n')
        self.scribus.insertText('	' + kat + '	' + schwierig + '	' + strecke + '\n')

    def handleTour(self, tour):
        try:
            self.scribus.insertText('\n')
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
                if "1" <= schwierigkeit <= "5":
                    schwierigkeit = "*" * int(schwierigkeit)
            logger.info("schwierigkeit %s", schwierigkeit)
            strecke = tour.getStrecke()
            if strecke == "0 km":
                logger.error("Fehler: Tour %s hat keine Tourlänge", titel)
            else:
                logger.info("strecke %s", strecke)

            if kategorie == 'Mehrtagestour':
                enddatum = tour.getEndDatum()[0]
                logger.info("enddatum %s", enddatum)
            personen = tour.getPersonen()

            logger.info("personen %s", str(personen))
            if len(personen) == 0:
                logger.error("Tour %s hat keinen Tourleiter", titel)

        except Exception as e:
            logger.error("Fehler in der Tour %s: %s", titel, e)
            return

        if kategorie == 'Mehrtagestour':
            self.handleKopfzeileMehrtage(datum, enddatum, kategorie, schwierigkeit, strecke)
        else:
            self.handleKopfzeile(datum, kategorie, schwierigkeit, strecke)
        self.handleTitel(titel)
        for abfahrt in abfahrten:
            self.handleAbfahrt(abfahrt)
        self.handleTextfeld(beschreibung)
        self.handleTourenleiter(personen)
        self.handleTextfeldList(zusatzinfo)

    def handleTermin(self, _):
        # print("Scribus für Termine nicht implementiert") #TODO
        pass
