# encoding: utf-8

from myLogger import logger


class TextHandler:
    def nothingFound(self):
        logger.info("Nichts gefunden")
        print("Nichts gefunden")

    def handleTour(self, tour):
        try:
            titel = tour.getTitel()
            logger.info("Title %s", titel)
            tourNummer = tour.getNummer()
            radTyp = tour.getRadTyp()[0]  # T,R,M
            kategorie = tour.getKategorie()[0]
            if kategorie == "T":  # Tagestour
                kategorie = "G"  # Ganztagstour...
            datum = tour.getDatum()[0]
            logger.info("tourNummer %s radTyp %s kategorie %s datum %s", tourNummer, radTyp, kategorie, datum)

            abfahrten = tour.getAbfahrten()
            if len(abfahrten) == 0:
                raise ValueError("kein Startpunkt in tour %s", titel)
            logger.info("abfahrten %s ", str(abfahrten))

            beschreibung = tour.getBeschreibung(False)
            logger.info("beschreibung %s", beschreibung)
            zusatzinfo = tour.getZusatzInfo()
            logger.info("zusatzinfo %s", str(zusatzinfo))
            schwierigkeit = str(tour.getSchwierigkeit())
            if schwierigkeit == "0":
                schwierigkeit = "1"
            logger.info("schwierigkeit %s", schwierigkeit)
            strecke = tour.getStrecke()
            if strecke == "0 km":
                logger.error("Fehler: Tour %s hat keine Tourlänge", titel)
            else:
                logger.info("strecke %s", strecke)
            hoehenmeter = tour.getHoehenmeter()
            anstiege = tour.getAnstiege()
            character = tour.getCharacter()

            if kategorie == 'Mehrtagestour':
                enddatum = tour.getEndDatum()[0]
                logger.info("enddatum %s", enddatum)

            personen = tour.getPersonen()
            logger.info("personen %s", str(personen))
            if len(personen) == 0:
                logger.error("Fehler: Tour %s hat keinen Tourleiter", titel)

        except Exception as e:
            logger.exception("Fehler in der Tour '%s': %s", titel, e)
            return

        print("{} ${} {} {}".format(titel, radTyp, tourNummer, kategorie))
        print("{} ${}$ ${}".format(datum, strecke, schwierigkeit))
        if hoehenmeter != "0" and len(character) > 0:
            print("${} m; {}".format(hoehenmeter, character))
        elif hoehenmeter != "0":
            print("${} m".format(hoehenmeter))
        elif len(character) > 0:
            print(character)
        for abfahrt in abfahrten:
            if abfahrt[1] != "":
                # print("${}: {} Uhr; {}".format(abfahrt[0], abfahrt[1], abfahrt[2]))
                print("${} Uhr; {}".format(abfahrt[1], abfahrt[2]))
            else:
                # print("${}: {}".format(abfahrt[0], abfahrt[2]))
                print("${}".format(abfahrt[2]))

        print(beschreibung)
        for info in zusatzinfo:
            if len(info) == 0:
                continue
            print(info)
        print("Leitung: {}".format(", ".join(personen)))
        print()

    def handleTermin(self, termin):
        try:
            titel = termin.getTitel()
            logger.info("Title %s", titel)
            kategorie = termin.getKategorie()
            datum = termin.getDatum()[0]
            logger.info("terminTyp %s datum %s", kategorie, datum)

            zeiten = termin.getAbfahrten()
            if len(zeiten) == 0:
                raise ValueError("keine Anfangszeit für Termin %s", titel)
            logger.info("zeiten %s ", str(zeiten))

            beschreibung = termin.getBeschreibung(False)
            logger.info("beschreibung %s", beschreibung)
            zusatzinfo = termin.getZusatzInfo()
            logger.info("zusatzinfo %s", str(zusatzinfo))

        except Exception as e:
            logger.exception("Fehler im Termin '%s': %s", titel, e)
            return

        print("{} - {}".format(titel, kategorie))  # terminTyp z.B. Stammtisch, entbehrlich?
        print("{}".format(datum))
        for zeit in zeiten:
            if zeit[1] != "":
                # print("${}: {} Uhr; {}".format(zeit[0], zeit[1], zeit[2]))
                print("{} Uhr; {}".format(zeit[1], zeit[2]))
            else:
                # print("${}: {}".format(zeit[0], zeit[2]))
                print("{}".format(zeit[2]))
        print(beschreibung)
        for info in zusatzinfo:
            if len(info) == 0:
                continue
            print(info)
        print()
