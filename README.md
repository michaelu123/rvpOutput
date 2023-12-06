# rvpOutput

Die Dateien zu dem Programm stehen auf https://github.com/michaelu123/rvpOutput . Nachfolgende Pfadangaben beziehen sich auf dieses Verzeichnis.

Dieses Programm liest Events aus dem Radtouren- und Veranstaltungsportal des ADFC (RVP) und gibt sie in verschiedenen Ausgabeformaten aus.
Einige dieser Formate haben nur noch historischen Wert. Mit diesen Formaten wurden früher Dokumente mittels Scribus oder Indesign erstellt, über mehrere Zwischenschritte. Es ist auch noch Code vorhanden, der direkt PDF erstellt. Da sich PDF nur schlecht editieren lässt, war das eine Sackgasse.

Das Ausgabeformat der Wahl ist jetzt Word, bzw. .docx. Dazu muß eine Template-Datei vorhanden sein, die man in Word erstellt. In der stehen dann Platzhalter für die Touren oder Veranstaltungen, die dann mit den Daten aus dem RVP ersetzt werden. Dabei bleiben die Formatierungen erhalten.
Steht also im template z.B. \${titel} als Platzhalter für den Titel der Tour in orange und fett/bold, werden auch die Titel aller Events in der Ausgabedatei in orange und fett/bold ausgegeben.

Ein Beispieltemplate steht in der Datei src/doc-templates/templateMünchen2023Review.docx,
die damit erzeugte Ausgabe steht in src/doc-templates/beispielausgabe.docx. Sie diente dazu, die geplanten Touren vor der Freigabe korrekturzulesen.
Laden Sie beide Dateien herunter, öffnen Sie sie, und Sie sollten leicht erkennen, wie aus dem Template die Ausgabedatei entstanden ist.

Um Druckschriften mit den Touren/Veranstaltungen aus dem RVP zu erstellen, empfehle ich Affinity Publisher, das Word-Dateien importieren kann.

Das Python-Programm hat verschiedene Einstiegspunkte, mit denen z.B. auch CAL-Einträge für Kalender erstellt werden konnten. Für den normalen Benutzer, der i.a. Python nicht kennt, gibt es eine rvpOutput.exe-Datei, also eine Programmdatei, die sich mit Doppelklick leicht starten läßt.

Das Programm sucht erst nach allen Events einer Gliederung in einem bestimmten Zeitraum, holt dann für jeden Event detailliertere Informationen, und gibt diese dann aus.

Eine ausführliche Programmdokumentation finden Sie unter doc/Programmdokumentation.docx .
