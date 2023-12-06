import base64
import contextlib
import json
import locale
import os
from concurrent.futures.thread import ThreadPoolExecutor
from tkinter import *
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import asksaveasfilename
from tkinter.simpledialog import askstring

import adfc_gliederungen
import csvHandler
# import pdfHandler
import eventXml

try:
    import docxHandler
except Exception as e:
    print(e)
    pass
import printHandler
import rawHandler
import textHandler
# textHandler produziert output a la KV München
import tourServer

try:
    from PIL import ImageTk
except:
    pass
from myLogger import logger, logFilePath

def toDate(dmy):  # 21.09.2018
    d = dmy[0:2]
    m = dmy[3:5]
    if len(dmy) == 10:
        y = dmy[6:10]
    else:
        y = "20" + dmy[6:8]
    if y < "2017":
        raise ValueError("Kein Datum vor 2017 möglich")
    if int(d) == 0 or int(d) > 31 or \
            int(m) == 0 or int(m) > 12 or \
            int(y) < 2000 or int(y) > 2100:
        raise ValueError("Bitte Datum als dd.mm.jjjj angeben, nicht als " + dmy)
    return y + "-" + m + "-" + d  # 2018-09-21


class TxtWriter:
    def __init__(self, targ):
        self.txt = targ

    def write(self, s):
        self.txt.insert("end", s)


class Prefs:
    def __init__(self):
        self.isDefault = True
        self.useRest = False
        self.includeSub = True
        self.format = "Text"
        self.linkType = "Frontend"
        self.eventType = "Alles"
        self.radTyp = "Alles"
        self.unitKeys = "152"
        self.start = "01.01.2000"
        self.end = "02.01.2000"
        self.docxTemplateName = ""
        self.xmlFileName = ""

    def set(self, useRest, includeSub, pformat, linkType, eventType, radTyp, unitKeys, start, end, docxTN, xmlFN):
        self.useRest = useRest
        self.includeSub = includeSub
        self.format = pformat
        self.linkType = linkType
        self.eventType = eventType
        self.radTyp = radTyp
        self.unitKeys = unitKeys
        self.start = start
        self.end = end
        self.docxTemplateName = docxTN
        self.xmlFileName = xmlFN
        self.isDefault = False

    def load(self):
        try:
            with open("c:/temp/tpjson/prefs.json", "r") as jsonFile:
                prefJS = json.load(jsonFile)
                self.useRest = prefJS.get("userest", "false")
                self.includeSub = prefJS.get("includesub", "true")
                self.format = prefJS.get("format", "Text")
                self.linkType = prefJS.get("linktype", "Frontend")
                self.eventType = prefJS.get("eventtype", "Alles")
                self.radTyp = prefJS.get("radtyp", "Alles")
                self.unitKeys = prefJS.get("unitkeys", "152")
                self.start = prefJS.get("start", "01.01.2000")
                self.end = prefJS.get("end", "02.01.2000")
                self.docxTemplateName = prefJS.get("docxtemplatename", "")
                self.xmlFileName = prefJS.get("xmlfilename", "")
                self.isDefault = False
        except Exception as e:
            print(e)
            pass

    def save(self):
        prefJS = {"userest": self.useRest, "includesub": self.includeSub, "format": self.format,
                  "linktype": self.linkType, "eventtype": self.eventType, "radtyp": self.radTyp,
                  "unitkeys": ",".join(self.unitKeys), "start": self.start, "end": self.end,
                  "docxtemplatename": self.docxTemplateName, "xmlfilename": self.xmlFileName}
        try:
            os.makedirs("c:/temp/tpjson")
        except:
            pass
        with open("c:/temp/tpjson/prefs.json", "w") as jsonFile:
            json.dump(prefJS, jsonFile, indent=4)

    def getUseRest(self):
        return self.useRest

    def getIncludeSub(self):
        return self.includeSub

    def getFormat(self):
        return self.format

    def getLinkType(self):
        return self.linkType

    def getEventType(self):
        return self.eventType

    def getRadTyp(self):
        return self.radTyp

    def getUnitKeys(self):
        return self.unitKeys

    def getStart(self):
        return self.start

    def getEnd(self):
        return self.end

    def getDocxTemplateName(self):
        return self.docxTemplateName

    def getXmlFileName(self):
        return self.xmlFileName


class LabelEntry(Frame):
    def __init__(self, master, labeltext, stringtext, **kw):
        super().__init__(master)
        self.label = Label(self, text=labeltext)
        self.svar = StringVar()
        self.svar.set(stringtext)
        self.entry = Entry(self, textvariable=self.svar,
                           width=len(stringtext) + 2, borderwidth=2, **kw)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.label.grid(row=0, column=0, sticky="w")
        self.entry.grid(row=0, column=1, sticky="w")

    def get(self):
        return self.svar.get()

    def set(self, s):
        return self.svar.set(s)


class LabelOM(Frame):
    def __init__(self, master, labeltext, options, initVal, **kwargs):
        super().__init__(master)
        self.options = options
        self.label = Label(self, text=labeltext)
        self.svar = StringVar()
        self.svar.set(initVal)
        self.optionMenu = OptionMenu(self, self.svar, *options, **kwargs)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.label.grid(row=0, column=0, sticky="w")
        self.optionMenu.grid(row=0, column=1, sticky="w")

    def get(self):
        return self.svar.get()

    def set(self, s):
        self.svar.set(s)


class ListBoxSB(Frame):
    def __init__(self, master, selFunc, entries):
        super().__init__(master)
        # for the "exportselection" param see
        # https://stackoverflow.com/questions/10048609/how-to-keep-selections-highlighted-in-a-tkinter-listbox
        self.lb = Listbox(self, borderwidth=2, selectmode="extended",
                          exportselection=False, width=50)
        self.lb.bind("<<ListboxSelect>>", selFunc)

        self.entries = sorted(entries)
        self.lb.insert("end", *self.entries)
        self.lbVsb = Scrollbar(self, orient="vertical", command=self.lb.yview)
        self.lb.configure(yscrollcommand=self.lbVsb.set)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.lb.grid(row=0, column=0, sticky="nsew")
        self.lbVsb.grid(row=0, column=1, sticky="ns")

    def disable(self):
        self.lb.config(state=DISABLED)

    def enable(self):
        self.lb.config(state=NORMAL)

    def curselection(self):
        names = [self.entries[i] for i in self.lb.curselection()]
        if "0 Alles" in names:
            return "Alles"
        s = ",".join([name.split(maxsplit=1)[0] for name in names])
        return s

    def clearLB(self):
        self.lb.selection_clear(0, len(self.entries))

    def setEntries(self, entries):
        self.entries = sorted(entries)
        self.lb.delete(0, "end")
        self.lb.insert("end", *self.entries)


class MyApp(Frame):
    def __init__(self, master, *args):
        super().__init__(master)
        logger.debug("main %s", str(args))

        self.scribus = len(args) == 1 and args[0] == "-scribus"
        self.savFile = None
        self.pos = None
        self.searchVal = ""
        self.images = []
        # self.pdfTemplateName = ""
        self.docxTemplateName = ""
        self.xmlFileName = ""
        self.docxHandler = None
        self.scrbHandler = None
        self.eventServer = None
        self.max_workers = 1
        if self.scribus:
            import scrbHandler
            self.scrbHandler = scrbHandler.ScrbHandler(self)
        else:
            menuBar = Menu(master)
            master.config(menu=menuBar)
            menuFile = Menu(menuBar)
            menuFile.add_command(label="Speichern", command=self.store,
                                 accelerator="Ctrl+s")
            master.bind_all("<Control-s>", self.store)
            menuFile.add_command(label="Speichern unter", command=self.storeas)
            # menuFile.add_command(label="PDF Template", command=self.pdfTemplate)
            menuFile.add_command(label="Word Template", command=self.docxTemplate)
            menuFile.add_command(label="XML Datei öffnen", command=self.xmlFile)
            menuFile.add_command(label="XML Datei schließen", command=self.xmlFileClose)
            menuBar.add_cascade(label="Datei", menu=menuFile)

            menuEdit = Menu(menuBar)
            menuEdit.add_command(label="Ausschneiden", command=self.cut,
                                 accelerator="Ctrl+x")
            master.bind_all("<Control-x>", self.cut)
            menuEdit.add_command(label="Kopieren", command=self.copy,
                                 accelerator="Ctrl+c")
            master.bind_all("<Control-c>", self.copy)
            menuEdit.add_command(label="Einfügen", command=self.paste,
                                 accelerator="Ctrl+v")
            master.bind_all("<Control-v>", self.paste)
            menuEdit.add_command(label="Suchen", command=self.search,
                                 accelerator="Ctrl+f")
            master.bind_all("<Control-f>", self.search)
            menuEdit.add_command(label="Erneut suchen", command=self.searchAgain,
                                 accelerator="F3")
            master.bind_all("<F3>", self.searchAgain)
            menuBar.add_cascade(label="Bearbeiten", menu=menuEdit)
        self.prefs = Prefs()
        self.prefs.load()
        self.createWidgets(master)
        if self.scribus:
            self.scrbHandler.setGuiParams()
        else:
            if self.prefs.format == "Scribus":
                self.prefs.format = "Text"

    @staticmethod
    def createPhoto(b64):
        binary = base64.decodebytes(b64.encode())
        photo = ImageTk.PhotoImage(data=binary)
        return photo

    def store(self, *_):
        if self.savFile is None or self.savFile == "":
            self.storeas()
            return
        with open(self.savFile, "w", encoding="utf-8-sig") as savFile:
            s = self.text.get("1.0", END)
            savFile.write(s)

    def storeas(self, *_):
        oformat = self.formatOM.get()
        self.savFile = asksaveasfilename(
            title="Ausgabedatei",
            initialfile="adfc_export",
            defaultextension=".csv" if oformat == "CSV" else ".txt",
            filetypes=[("CSV", ".csv")] if oformat == "CSV" else [("TXT", ".txt")])
        if self.savFile is None or self.savFile == "":
            return
        self.store()

    # def pdfTemplate(self, *args):
    #     self.pdfTemplateName = askopenfilename(title="Choose a PDF Template",
    #         defaultextension=".json",
    #         filetypes=[("JSON", ".json")])

    def docxTemplate(self, *args):
        if self.docxTemplateName is None or self.docxTemplateName == "" or len(args) == 0 or args[0] != "NO":
            self.docxTemplateName = askopenfilename(
                title="Word Template auswählen",
                defaultextension=".docx", filetypes=[("DOCX", ".docx")])
        if self.docxTemplateName is None or self.docxTemplateName == "":
            raise ValueError("Dateipfad des .docx Templates fehlt!")
        self.docxHandler = docxHandler.DocxHandler(self)
        self.startBtn.config(state=DISABLED)
        self.docxHandler.openDocx(self.prefsDefault)  # set GUI from doc params unless obtained from prefs
        self.startBtn.config(state=NORMAL)

    def xmlFile(self, *args):
        self.xmlFileName = askopenfilename(
            title="XML File (XML export aus dem TP) auswählen",
            defaultextension=".xml", filetypes=[("XML", ".xml")])
        self.gliederungLB.disable()
        self.gliederungSvar.set("< durch XML-Datei bestimmt >")

    def xmlFileClose(self, *args):
        self.xmlFileName = ""
        self.gliederungLB.enable()
        self.gliederungSvar.set(self.gliederungLB.curselection())

    def setGliederung(self, gl):
        self.gliederungSvar.set(gl)

    def setIncludeSub(self, b):
        self.includeSubVar.set(b)

    def setStart(self, d):
        self.startDateLE.set(d)

    def setEnd(self, d):
        self.endDateLE.set(d)

    def setEventType(self, s):
        self.eventTypeVar.set(s)

    def setRadTyp(self, s):
        self.radTypVar.set(s)

    def setLinkType(self, s):
        self.linkTypeOM.set(s)

    def cut(self, *_):
        savedText = self.text.get(SEL_FIRST, SEL_LAST)
        self.clipboard_clear()
        self.clipboard_append(savedText)
        self.text.delete(SEL_FIRST, SEL_LAST)

    def copy(self, *_):
        savedText = self.text.get(SEL_FIRST, SEL_LAST)
        self.clipboard_clear()
        self.clipboard_append(savedText)

    def paste(self, *_):
        savedText = self.clipboard_get()
        if savedText is None or savedText == "":
            return
        ranges = self.text.tag_ranges(SEL)
        if len(ranges) == 2:
            self.text.replace(ranges.first, ranges.last, savedText)
        else:
            self.text.insert(INSERT, savedText)

    def search(self, *_):
        self.searchVal = askstring("Suchen", "Bitte Suchstring eingeben",
                                   initialvalue=self.searchVal)
        if self.searchVal is None:
            return
        self.searchAgain()

    def searchAgain(self, *_):
        self.pos = self.text.search(self.searchVal, INSERT + "+1c", END)
        if self.pos != "":
            self.text.mark_set(INSERT, self.pos)
            self.text.see(self.pos)
        self.text.focus_set()

    def eventTypeHandler(self):
        typ = self.eventTypeVar.get()
        for rtBtn in self.radTypBtns:
            if typ == "Termin":
                rtBtn.config(state=DISABLED)
            else:
                rtBtn.config(state=NORMAL)

    def gliederungSel(self, _):
        sel = self.gliederungLB.curselection()
        self.gliederungSvar.set(sel)

    def clearLB(self, _):
        self.gliederungLB.clearLB()

    def lvSelector(self, event):
        kvMap = adfc_gliederungen.getLV(event[0:3])
        entries = [key + " " + kvMap[key] for key in kvMap.keys()]
        self.gliederungLB.setEntries(entries)
        self.gliederungSvar.set("")

    def formatSelektor(self, event):
        if event == "Word":
            self.docxTemplate("NO")

    def createWidgets(self, master):
        self.prefsDefault = self.prefs.isDefault
        self.useRestVar = BooleanVar()
        self.useRestVar.set(self.prefs.useRest)
        useRestCB = Checkbutton(master,
                                text="Aktuelle Daten werden vom Server geholt",
                                variable=self.useRestVar)

        swFrame = Frame(master)
        self.includeSubVar = BooleanVar()
        self.includeSubVar.set(True)
        includeSubCB = Checkbutton(swFrame,
                                   text="Untergliederungen einbeziehen",
                                   variable=self.includeSubVar)

        self.includeImgVar = BooleanVar()
        self.includeImgVar.set(False)
        includeImgCB = Checkbutton(swFrame,
                                   text="Mit Bild",
                                   variable=self.includeImgVar)
        swFrame.grid_rowconfigure(0, weight=1)
        swFrame.grid_columnconfigure(0, weight=1)
        swFrame.grid_columnconfigure(1, weight=0)
        includeSubCB.grid(row=0, column=0, sticky="nsew")
        includeImgCB.grid(row=0, column=1, sticky="ns")

        if self.scribus:
            self.formatOM = LabelOM(master, "Ausgabeformat:",
                                    ["Scribus"], "Scribus", command=self.formatSelektor)
            self.formatOM.optionMenu.config(state=DISABLED)
        else:
            f = self.prefs.getFormat()
            if f == "Scribus":  # not outside scribus
                f = "Text"
            self.formatOM = LabelOM(master, "Ausgabeformat:",
                                    ["München", "Starnberg", "CSV", "Text", "Word"],  # "PDF"
                                    f, command=self.formatSelektor)

        self.linkTypeOM = LabelOM(master, "Links ins:",
                                  ["Frontend", "Backend", ""],
                                  self.prefs.getLinkType())

        eventTypes = ["Radtour", "Termin", "Alles"]
        eventTypesLF = LabelFrame(master)
        eventTypesLF["text"] = "Typen"
        self.eventTypeVar = StringVar()
        self.eventTypeBtns = []
        for typ in eventTypes:
            typRB = Radiobutton(eventTypesLF, text=typ, value=typ,
                                variable=self.eventTypeVar, command=self.eventTypeHandler)
            self.eventTypeBtns.append(typRB)
            if typ == self.prefs.getEventType():
                typRB.select()
            else:
                typRB.deselect()
            typRB.grid(sticky="w")

        radTyps = ["Rennrad", "Tourenrad", "Mountainbike", "Alles"]
        radTypsLF = LabelFrame(master)
        radTypsLF["text"] = "Fahrradtyp"
        self.radTypVar = StringVar()
        self.radTypBtns = []
        for radTyp in radTyps:
            radTypRB = Radiobutton(radTypsLF, text=radTyp, value=radTyp,
                                   variable=self.radTypVar)  # , command=self.radTypHandler)
            self.radTypBtns.append(radTypRB)
            if radTyp == self.prefs.getRadTyp():
                radTypRB.select()
            else:
                radTypRB.deselect()
            radTypRB.grid(sticky="w")
        self.docxTemplateName = self.prefs.getDocxTemplateName()
        self.xmlFileName = self.prefs.getXmlFileName()

        # container for LV selector and Listbox for KVs
        glContainer = Frame(master, borderwidth=2, relief="sunken", width=100)
        # need an eventServer here early for list of LVs
        _ = tourServer.EventServer(True, False, self.max_workers)
        lvMap = adfc_gliederungen.getLVs()
        self.lvList = [key + " " + lvMap[key] for key in lvMap.keys()]
        self.lvList = sorted(self.lvList)
        self.lvOM = LabelOM(glContainer, "Landesverband:", self.lvList,
                            "152", command=self.lvSelector)
        kvMap = adfc_gliederungen.getLV(self.lvOM.get()[0:3])
        entries = [key + " " + kvMap[key] for key in kvMap.keys()]
        self.gliederungLB = ListBoxSB(glContainer, self.gliederungSel, entries)
        self.gliederungSvar = StringVar()
        self.gliederungSvar.set(self.prefs.getUnitKeys())
        self.gliederungEN = Entry(master, textvariable=self.gliederungSvar,
                                  borderwidth=2, width=60)
        self.gliederungEN.bind("<Key>", self.clearLB)
        self.lvOM.grid(row=0, column=0, sticky="nsew")
        self.gliederungLB.grid(row=1, column=0, sticky="nsew")
        glContainer.grid_rowconfigure(0, weight=1)
        glContainer.grid_rowconfigure(1, weight=1)
        glContainer.grid_columnconfigure(0, weight=1)

        self.startDateLE = LabelEntry(master, "Start Datum:", self.prefs.getStart())
        self.endDateLE = LabelEntry(master, "Ende Datum:", self.prefs.getEnd())

        textContainer = Frame(master, borderwidth=2, relief="sunken")
        self.text = Text(textContainer, wrap="none", borderwidth=0,
                         cursor="arrow")  # width=100, height=40,
        textVsb = Scrollbar(textContainer, orient="vertical",
                            command=self.text.yview)
        textHsb = Scrollbar(textContainer, orient="horizontal",
                            command=self.text.xview)
        self.text.configure(yscrollcommand=textVsb.set,
                            xscrollcommand=textHsb.set)
        self.text.grid(row=0, column=0, sticky="nsew")
        textVsb.grid(row=0, column=1, sticky="ns")
        textHsb.grid(row=1, column=0, sticky="ew")
        textContainer.grid_rowconfigure(0, weight=1)
        textContainer.grid_columnconfigure(0, weight=1)

        for x in range(2):
            Grid.columnconfigure(master, x, weight=1 if x == 1 else 0)
        for y in range(7):
            Grid.rowconfigure(master, y, weight=1 if y == 6 else 0)
        useRestCB.grid(row=0, column=0, padx=5, pady=2, sticky="w")
        swFrame.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        includeImgCB.grid(row=0, column=2, padx=5, pady=2, sticky="w")
        self.formatOM.grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.linkTypeOM.grid(row=1, column=1, padx=5, pady=2, sticky="w")
        eventTypesLF.grid(row=2, column=0, padx=5, pady=2, sticky="w")
        radTypsLF.grid(row=2, column=1, padx=5, pady=2, sticky="w")
        glContainer.grid(row=3, column=0, padx=5, pady=2, sticky="w")
        self.gliederungEN.grid(row=3, column=1, padx=5, pady=2, sticky="w")
        self.startDateLE.grid(row=4, column=0, padx=5, pady=2, sticky="w")
        self.endDateLE.grid(row=4, column=1, padx=5, pady=2, sticky="w")

        if self.scribus:
            frm = Frame(master)
            frm.grid_rowconfigure(0, weight=1)
            for i in range(4):
                frm.grid_columnconfigure(i, weight=1)
            self.startBtn = Button(frm, text="Start", bg="red", command=self.starten)
            self.tocBtn = Button(frm, text="InhVerzAktu", bg="red", command=self.makeToc)
            self.startPgNr = LabelEntry(frm, "1.Seitennr:", "1")
            self.rmBtn = Button(frm, text="LöscheEventMarker", bg="red", command=self.rmEventIdMarkers)
            self.startBtn.grid(row=0, column=0, padx=5, pady=2, sticky="w")
            self.tocBtn.grid(row=0, column=1, padx=5, pady=2, sticky="w")
            self.startPgNr.grid(row=0, column=2, padx=5, pady=2, sticky="w")
            self.rmBtn.grid(row=0, column=3, padx=5, pady=2, sticky="w")
            frm.grid(row=5, padx=5, pady=2, sticky="w")
        else:
            self.startBtn = Button(master, text="Start", bg="red", command=self.starten)
            self.startBtn.grid(row=5, padx=5, pady=2, sticky="w")

        textContainer.grid(row=6, columnspan=2, padx=5, pady=2, sticky="nsew")

        self.pos = "1.0"
        self.text.mark_set(INSERT, self.pos)

        if self.xmlFileName is not None and self.xmlFileName != "":
            self.gliederungLB.disable()
            self.gliederungSvar.set("< durch XML-Datei bestimmt >")

    def disableStart(self):
        self.startBtn.config(state=DISABLED)

    def insertImage(self, event):
        img = event.getImagePreview()
        if img is not None:
            print()
            photo = self.createPhoto(img)
            self.images.append(photo)  # see http://effbot.org/pyfaq/why-do-my-tkinter-images-not-appear.htm
            self.text.image_create(INSERT, image=photo)
            print()

    def getLinkType(self):
        return self.linkTypeOM.get()

    def getRadTyp(self):
        return self.radTypVar.get()

    def getEventType(self):
        return self.eventTypeVar.get()

    def getGliederung(self):
        g = self.gliederungSvar.get()
        if g.startswith("<"):
            g = ""
        return g

    def getIncludeSub(self):
        return self.includeSubVar.get()

    def getIncludeImg(self):
        return self.includeImgVar.get()

    @staticmethod
    def checkDate(d):
        dparts = d.split(".")
        if len(dparts) != 3 or len(dparts[0]) != 2 or len(dparts[1]) != 2 or len(dparts[2]) != 4:
            raise ValueError("Datum im Format dd.mm.yyyy")
        return d

    def getStart(self):
        return self.checkDate(self.startDateLE.get().strip())

    def getEnd(self):
        return self.checkDate(self.endDateLE.get().strip())

    def starten(self):
        useRest = self.useRestVar.get()
        includeSub = self.includeSubVar.get()
        typ = self.eventTypeVar.get()
        radTyp = self.radTypVar.get()
        unitKeys = self.gliederungSvar.get().split(",")
        start = toDate(self.getStart())
        end = toDate(self.getEnd())
        if start[0:4] != end[0:4]:
            raise ValueError("Start und Ende in unterschiedlichem Jahr")
        self.images.clear()
        self.text.delete("1.0", END)
        txtWriter = TxtWriter(self.text)

        formatS = self.formatOM.get()
        if formatS == "Starnberg":
            handler = printHandler.PrintHandler()
        elif formatS == "München":
            handler = textHandler.TextHandler()
        elif formatS == "CSV":
            handler = csvHandler.CsvHandler(txtWriter)
        elif formatS == "Text":
            handler = rawHandler.RawHandler()
        elif formatS == "Word":
            if self.docxHandler is None:
                self.docxTemplate("NO")
            handler = self.docxHandler
        elif formatS == "Scribus":
            handler = self.scrbHandler
        elif formatS == "PDF":
            import pdfHandler
            handler = pdfHandler.PDFHandler(self)
        else:
            handler = rawHandler.RawHandler()

        self.prefs.set(useRest, includeSub, formatS, self.getLinkType(), self.getEventType(), self.getRadTyp(),
                       unitKeys, self.getStart(), self.getEnd(), self.docxTemplateName, self.xmlFileName)
        self.prefs.save()

        with contextlib.redirect_stdout(txtWriter):
            try:
                self.eventServer = tourServer.EventServer(useRest, includeSub, self.max_workers)
                if self.xmlFileName is not None and self.xmlFileName != "":
                    self.eventServer = eventXml.EventServer(self.xmlFileName, self.eventServer)
                    useXml = True
                else:
                    useXml = False
                events = []
                for unitKey in unitKeys:
                    if unitKey == "Alles":
                        unitKey = ""
                    events.extend(self.eventServer.getEvents(
                        unitKey.strip(), start, end, typ))

                if len(events) == 0:
                    handler.nothingFound()
                self.eventServer.calcNummern()
                if useXml:
                    events.sort(key=lambda x: x.getDatumRaw())  # sortieren nach Datum, REST: beginning, XML: beginning
                else:
                    events.sort(key=lambda x: x["beginning"])  # sortieren nach Datum, REST: beginning, XML: beginning
                ThreadPoolExecutor(max_workers=self.max_workers).map(self.eventServer.getEvent, events)
                for event in events:
                    event = self.eventServer.getEvent(event)
                    if event is None or event.isExternalEvent():  # add a GUI switch?
                        continue
                    if event.isTermin():
                        if isinstance(handler, rawHandler.RawHandler):
                            self.insertImage(event)
                        handler.handleTermin(event)
                    else:
                        # docx and scrb have own radtyp selections
                        if radTyp != "Alles" and self.docxHandler is None and self.scrbHandler is None and event.getRadTyp() != radTyp:
                            logger.debug("tour %s hat radtyp %s, nicht radtyp %s", event.getTitel(), event.getRadTyp(),
                                         radTyp)
                            continue
                        if isinstance(handler, rawHandler.RawHandler):
                            self.insertImage(event)
                        handler.handleTour(event)
                if hasattr(handler, "handleEnd"):
                    handler.handleEnd()
                self.pos = "1.0"
                self.text.mark_set(INSERT, self.pos)
                self.text.focus_set()
            except Exception as e:
                logger.exception("Error during script evaluation")
                print("Error ", e, ", see ", logFilePath)

    def makeToc(self):
        firstPageNr = self.startPgNr.get()
        self.text.delete("1.0", END)
        txtWriter = TxtWriter(self.text)

        with contextlib.redirect_stdout(txtWriter):
            self.eventServer = tourServer.EventServer(False, False, self.max_workers)
            if self.scrbHandler is None:
                self.scrbHandler = scrbHandler.ScrbHandler(self)
            try:
                self.tocBtn.config(state=DISABLED)
                self.scrbHandler.makeToc(int(firstPageNr))
            except Exception as e:
                logger.exception("Error during script evaluation")
                print("Error ", e, ", see ", logFilePath)
            finally:
                self.tocBtn.config(state=NORMAL)

    def rmEventIdMarkers(self):
        self.text.delete("1.0", END)
        txtWriter = TxtWriter(self.text)
        with contextlib.redirect_stdout(txtWriter):
            self.eventServer = tourServer.EventServer(False, False, self.max_workers)
            if self.scrbHandler is None:
                self.scrbHandler = scrbHandler.ScrbHandler(self)
            try:
                self.rmBtn.config(state=DISABLED)
                self.scrbHandler.rmEventIdMarkers()
            except Exception as e:
                logger.exception("Error during script evaluation")
                print("Error ", e, ", see ", logFilePath)
            finally:
                self.rmBtn.config(state=NORMAL)


def main(args):
    locale.setlocale(locale.LC_TIME, "German")
    root = Tk()
    app = MyApp(root, args)
    app.master.title("ADFC Touren/Termine")
    app.mainloop()
    try:
        root.destroy()  # already destroyed
    except:
        pass


if __name__ == '__main__':
    main(None)
