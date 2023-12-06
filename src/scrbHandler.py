# encoding: utf-8

import copy
import os
import re
import sys

import adfc_gui
import expand
import markdown
import markdown.extensions.tables
import selektion
import styles
import tourRest
from myLogger import logger

try:
    import scribus
except ImportError:
    print("Unable to import the 'scribus' module. This script will only run within")
    print("the Python interpreter embedded in Scribus. Try Script->Execute Script.")
    sys.exit(1)

schwierigkeitMap = {0: "sehr einfach",
                    1: "sehr einfach",
                    2: "einfach",
                    3: "mittel",
                    4: "schwer",
                    5: "sehr schwer"}
# schwarzes Quadrat = Wingdings 2 0xA2, weißes Quadrat = 0xA3
schwierigkeitMMap = {0: "\u00a3\u00a3\u00a3\u00a3\u00a3",
                     1: "\u00a2\u00a3\u00a3\u00a3\u00a3",
                     2: "\u00a2\u00a2\u00a3\u00a3\u00a3",
                     3: "\u00a2\u00a2\u00a2\u00a3\u00a3",
                     4: "\u00a2\u00a2\u00a2\u00a2\u00a3",
                     5: "\u00a2\u00a2\u00a2\u00a2\u00a2"}
paramRE = re.compile(r"(?u)\${(\w*?)}")
fmtRE = re.compile(r"(?u)\.fmt\((.*?)\)")
strokeRE = r'(\~{2})(.+?)\1'
ulRE = r'(\^{2})(.+?)\1'
STX = '\u0002'  # Use STX ("Start of text") for start-of-placeholder
ETX = '\u0003'  # Use ETX ("End of text") for end-of-placeholder
stxEtxRE = re.compile(r'%s(\d+)%s' % (STX, ETX))
nlctr = 0
debug = False
adfc_blue = 0x004b7c  # CMYK=90 60 10 30
adfc_yellow = 0xee7c00  # CMYK=0 60 100 0
noPStyle = 'Default Paragraph Style'
noCStyle = 'Default Character Style'
lastPStyle = ""
lastCStyle = ""


def str2hex(s):
    return ":".join("{:04x}".format(ord(c)) for c in s)


# add_hyperlink and insertHR can not be done in Scribus, as they are not related to the text, but to page
# coordinates. I.e. if the text changes, lines and boxes stay where they are. I cannot even draw a line after a line
# of text or draw a box around a word for a hyperlink, because I can't find out what the coordinates of the text are.
# see http://forums.scribus.net/index.php/topic,3487.0.html
def add_hyperlink(pos, url):
    pass


def insertHR():
    pass


class ScrbTreeProcessor(markdown.treeprocessors.Treeprocessor):
    def __init__(self, md):
        super().__init__(md)
        self.scrbHandler = None
        self.fontStyles = ""
        self.ctr = 0
        self.pIndent = 0
        self.numbered = False
        self.nodeHandler = {
            "h1": self.h1,
            "h2": self.h2,
            "h3": self.h3,
            "h4": self.h4,
            "h5": self.h5,
            "h6": self.h6,
            "p": self.p,
            "strong": self.strong,
            "em": self.em,
            "blockquote": self.blockQuote,
            "stroke": self.stroke,
            "underline": self.underline,
            "ul": self.ul,
            "ol": self.ol,
            "li": self.li,
            "a": self.a,
            "img": self.img,
            "hr": self.hr,
            "table": self.table,
            "thead": self.thead,
            "tbody": self.tbody,
            "tr": self.tr,
            "th": self.th,
            "td": self.td,
        }

    def run(self, root):
        self.tpRun = ScrbRun("", "MD_P_BLOCK", "MD_C_REGULAR")
        self.fontStyles = ""
        self.lvl = 4
        for child in root:  # skip <div> root
            self.walkOuter(child)
        root.clear()

    def setDeps(self, scrbHandler):
        self.scrbHandler = scrbHandler

    def unescape(self, m):
        return chr(int(m.group(1)))

    def checkStylesExi(self, r):
        if not styles.checkCStyleExi(r.cstyle):
            r.cstyle = noCStyle
        if not styles.checkPStyleExi(r.pstyle):
            r.pstyle = noPStyle

    def printLines(self, s):
        s = stxEtxRE.sub(self.unescape, s)  # "STX40ETX" -> chr(40), see markdown/postprocessors/UnescapePostprocessor
        sav = self.tpRun.cstyle
        self.tpRun.cstyle = styles.modifyFont(self.tpRun.cstyle, self.fontStyles)
        self.scrbHandler.insertText(s, self.tpRun)
        self.tpRun.cstyle = sav

    def walkOuter(self, node):
        global nlctr
        if debug:
            if node.text is not None:
                ltext = node.text.replace("\n", "<" + str(nlctr) + "nl>")
                # node.text = node.text.replace("\n", str(nlctr) + "\n")
                nlctr += 1
            else:
                ltext = "None"
            if node.tail is not None:
                ltail = node.tail.replace("\n", "<" + str(nlctr) + "nl>")
                # node.tail = node.tail.replace("\n", str(nlctr) + "\n")
                nlctr += 1
            else:
                ltail = "None"
            self.lvl += 4
            logger.debug("MD:%s<<<<", " " * self.lvl)
            logger.debug("MD:%snode=%s,text=%s,tail=%s", " " * self.lvl, node.tag, ltext, ltail)
        try:
            self.nodeHandler[node.tag](node)
            if node.tail is not None:
                self.printLines(node.tail)
        except Exception:
            msg = "Fehler während der Behandlung der Beschreibung des Events " + \
                  self.scrbHandler.eventMsg
            logger.exception(msg)
        if debug:
            logger.debug("MD:%s>>>>", " " * self.lvl)
            self.lvl -= 4

    def walkInner(self, node):
        if node.tag == "li":
            node.text += node.tail
            node.tail = None
        if node.text is not None:
            self.printLines(node.text)
        for dnode in node:
            self.walkOuter(dnode)

    def h(self, pstyle, cstyle, node):
        savP = self.tpRun.pstyle
        savC = self.tpRun.cstyle
        self.tpRun.pstyle = pstyle
        self.tpRun.cstyle = cstyle
        self.checkStylesExi(self.tpRun)
        self.walkInner(node)
        self.tpRun.pstyle = savP
        self.tpRun.cstyle = savC

    def h1(self, node):
        self.h("MD_P_H1", "MD_C_H1", node)

    def h2(self, node):
        self.h("MD_P_H2", "MD_C_H2", node)

    def h3(self, node):
        self.h("MD_P_H3", "MD_C_H3", node)

    def h4(self, node):
        self.h("MD_P_H4", "MD_C_H4", node)

    def h5(self, node):
        self.h("MD_P_H5", "MD_C_H5", node)

    def h6(self, node):
        self.h("MD_P_H6", "MD_C_H6", node)

    def p(self, node):
        self.tpRun.cstyle = "MD_C_REGULAR"
        self.checkStylesExi(self.tpRun)
        self.walkInner(node)

    def strong(self, node):
        sav = self.fontStyles
        self.fontStyles += "B"
        self.walkInner(node)
        self.fontStyles = sav

    def stroke(self, node):
        sav = self.fontStyles
        self.fontStyles += "X"
        self.walkInner(node)
        self.fontStyles = sav

    def underline(self, node):
        sav = self.fontStyles
        self.fontStyles += "U"
        self.walkInner(node)
        self.fontStyles = sav

    def em(self, node):
        sav = self.fontStyles
        self.fontStyles += "I"
        self.walkInner(node)
        self.fontStyles = sav

    def plist(self, node, numbered):
        node.text = node.tail = None
        savCtr = self.ctr
        savP = self.tpRun.pstyle
        savN = self.numbered
        self.ctr = 1
        self.pIndent += 1
        self.numbered = numbered
        self.tpRun.pstyle = styles.listStyle(savP, self.pIndent)
        self.walkInner(node)
        self.pIndent -= 1
        self.ctr = savCtr
        self.tpRun.pstyle = savP
        self.numbered = savN

    def ul(self, node):  # bullet
        self.plist(node, False)

    def ol(self, node):  # numbered
        self.plist(node, True)

    def li(self, node):
        if self.numbered:
            self.scrbHandler.insertText(str(self.ctr) + ".\t", self.tpRun)
        else:
            savC = self.tpRun.cstyle
            self.tpRun.cstyle = styles.bulletStyle()
            self.scrbHandler.insertText(styles.BULLET_CHAR + "\t", self.tpRun)
            self.tpRun.cstyle = savC
        self.ctr += 1
        self.walkInner(node)

    def a(self, node):
        url = node.attrib["href"]
        # pos = self.insertPos
        self.walkInner(node)
        # add_hyperlink(pos, url)
        # scribus.selectText(pos, self.insertPos - pos, self.textbox)
        # scribus.setTextColor("ADFC_Yellow", self.textbox)

    def blockQuote(self, node):
        node.text = node.tail = None
        savP = self.tpRun.pstyle
        self.tpRun.pstyle = "MD_P_BLOCK"
        self.checkStylesExi(self.tpRun)
        self.walkInner(node)
        self.tpRun.pstyle = savP

    def hr(self, node):
        node.tail = None
        insertHR()
        self.walkInner(node)

    def img(self, node):
        self.walkInner(node)

    def table(self, node):
        node.text = node.tail = None
        savP = self.tpRun.pstyle
        self.tpRun.pstyle = "MD_P_REGULAR"
        self.checkStylesExi(self.tpRun)
        self.walkInner(node)
        self.tpRun.pstyle = savP

    def thead(self, node):
        pass

    def tbody(self, node):
        node.text = node.tail = ""
        self.walkInner(node)

    def tr(self, node):
        node.text = ""
        l = len(node) - 1
        # separate td's by \t, that's all I can do at the moment
        for i, dnode in enumerate(node):
            if i != l:
                dnode.text += "\t"
        self.walkInner(node)

    def th(self, node):
        pass

    def td(self, node):
        node.tail = ""
        self.walkInner(node)


class ScrbExtension(markdown.Extension):
    def __init__(self):
        super(ScrbExtension, self).__init__()
        self.scrbTreeProcessor = None

    def extendMarkdown(self, md, globals):
        self.scrbTreeProcessor = ScrbTreeProcessor(md)
        md.treeprocessors.register(self.scrbTreeProcessor, "scrbTreeProcessor", 5)
        md.inlinePatterns.register(
            markdown.inlinepatterns.SimpleTagInlineProcessor(
                strokeRE, 'stroke'), 'stroke', 40)
        md.inlinePatterns.register(
            markdown.inlinepatterns.SimpleTagInlineProcessor(
                ulRE, 'underline'), 'underline', 41)


class ScrbRun:
    def __init__(self, text, pstyle, cstyle):
        self.text = text
        self.pstyle = pstyle
        self.cstyle = cstyle

    def __str__(self):
        return "\n{ text:" + self.text + ",type:" + str(type(self.text)) + ",pstyle:" + str(
            self.pstyle) + ",cstyle:" + str(self.cstyle) + "}"

    def __repr__(self):
        return "\n{ text:" + self.text + ",type:" + str(type(self.text)) + ",pstyle:" + str(
            self.pstyle) + ",cstyle:" + str(self.cstyle) + "}"


class ScrbHandler(expand.Expand):
    def __init__(self, gui):
        super().__init__()
        if not scribus.haveDoc():
            scribus.messageBox('Scribus - Script Error', "No document open", scribus.ICON_WARNING, scribus.BUTTON_OK)
            sys.exit(1)

        self.gui = gui
        self.terminselections = {}
        self.tourselections = {}
        self.touren = []
        self.termine = []
        self.url = None
        self.run = None
        self.textbox = None
        self.linkType = "Frontend"
        self.gliederung = None
        self.includeSub = False
        self.start = None
        self.end = None
        self.pos = None
        self.ausgabedatei = None
        self.toBeDelPosParam = None
        self.toBeDelPosToc = None
        self.pageNr = None
        self.frameLinks = {}
        self.selecter = selektion.Selektion()

        global debug
        try:
            _ = os.environ["DEBUG"]
            debug = True
        except:
            debug = True  # False

        self.openScrb()
        self.scrbExtension = ScrbExtension()
        self.md = markdown.Markdown(extensions=[self.scrbExtension, markdown.extensions.tables.makeExtension()],
                                    enable_attributes=True, logger=logger)
        self.scrbExtension.scrbTreeProcessor.setDeps(self)

    def openScrb(self):
        paraStyles = scribus.getParagraphStyles()
        charStyles = scribus.getCharStyles()
        logger.debug("paraStyles: %s\ncharStyles:%s", str(paraStyles), str(charStyles))
        self.parseParams()
        scribus.defineColor("ADFC_Yellow_", 0, 153, 255, 0)
        # scribus.defineColor("ADFC_Blue_", 230, 153, 26, 77)
        WD2_Y_ = {"name": "WD2_Y_", "font": "Wingdings 2 Regular", "fillcolor": "ADFC_Yellow_"}
        styles.cstyles["WD2_Y_"] = WD2_Y_
        styles.checkPStyleExi("MD_P_REGULAR")
        styles.checkPStyleExi("MD_P_BLOCK")
        styles.checkCStyleExi("MD_C_REGULAR")
        styles.checkCStyleExi("MD_C_BOLD")
        styles.checkCStyleExi("WD2_Y_")
        styles.checkCStyleExi("MD_C_TOC")

    def nothingFound(self):
        logger.info("Nichts gefunden")
        print("Nichts gefunden")

    def makeRuns(self, pos1, pos2):
        runs = []

        scribus.selectText(pos1, pos2 - pos1, self.textbox)
        txtAll = scribus.getAllText(self.textbox)

        scribus.selectText(pos1, 1, self.textbox)
        last_pstyle = scribus.getStyle(self.textbox)
        last_cstyle = scribus.getCharacterStyle(self.textbox)

        text = ""
        changed = False
        for c in range(pos1, pos2):
            scribus.selectText(c, 1, self.textbox)
            # does not work for text in overflown area, see https://bugs.scribus.net/view.php?id=15911
            # char = scribus.getText(self.textbox)
            char = txtAll[c - pos1]

            pstyle = scribus.getStyle(self.textbox)
            if pstyle != last_pstyle:
                changed = True

            cstyle = scribus.getCharacterStyle(self.textbox)
            if cstyle != last_cstyle:
                changed = True

            # ff = scribus.getFontFeatures(self.textbox)
            # if ff != last_ff:
            #     # ff mostly "", for Wingdins chars ="-clig,-liga" !?!?
            #     logger.debug("fontfeature %s", ff)
            #     last_ff = ff

            if changed:
                runs.append(ScrbRun(text, last_pstyle, last_cstyle))
                last_pstyle = pstyle
                last_cstyle = cstyle
                text = ""
                changed = False
            text = text + char
        if text != "":
            runs.append(ScrbRun(text, last_pstyle, last_cstyle))
        return runs

    def insertText(self, text, run):
        if text is None or text == "":
            return
        pos = self.insertPos
        scribus.insertText(text, pos, self.textbox)
        tlen = len(text)
        logger.debug("insert pos=%d len=%d npos=%d text='%s' style=%s cstyle=%s",
                     pos, tlen, pos + tlen, text, run.pstyle, run.cstyle)
        global lastPStyle, lastCStyle
        if run.pstyle != lastPStyle:
            scribus.selectText(pos, tlen, self.textbox)
            scribus.setParagraphStyle(noPStyle if run.pstyle is None else run.pstyle, self.textbox)
            lastPStyle = run.pstyle
        if run.cstyle != lastCStyle:
            scribus.selectText(pos, tlen, self.textbox)
            scribus.setCharacterStyle(noCStyle if run.cstyle is None else run.cstyle, self.textbox)
            lastCStyle = run.cstyle
        if False and self.url is not None:  # TODO
            logger.debug("URL: %s", self.url)
            scribus.selectText(pos, tlen, self.textbox)
            frame = None  # see http://forums.scribus.net/index.php/topic,3487.0.html
            scribus.setURIAnnotation(self.url, frame)
            self.url = None
        self.insertPos += tlen

    def createNewPage(self, tbox):
        curPage = scribus.currentPage()
        if curPage < scribus.pageCount() - 1:
            where = curPage + 1
        else:
            where = -1
        logger.debug("cur=%d name=%s pc=%d wh=%d", curPage, tbox, scribus.pageCount(), where)
        cols = scribus.getColumns(tbox)
        colgap = scribus.getColumnGap(tbox)
        x, y = scribus.getPosition(tbox)
        w, h = scribus.getSize(tbox)
        mp = scribus.getMasterPage(curPage)
        scribus.newPage(where, mp)  # return val?
        scribus.gotoPage(curPage + 1)
        newBox = scribus.createText(x, y, w, h)
        scribus.setColumns(cols, newBox)
        scribus.setColumnGap(colgap, newBox)
        scribus.linkTextFrames(tbox, newBox)
        logger.debug("link from %s to %s", tbox, newBox)
        return newBox

    def parseParams(self):
        pagenum = scribus.pageCount()
        lines = []
        for page in range(1, pagenum + 1):
            scribus.gotoPage(page)
            pageitems = scribus.getPageItems()
            for item in pageitems:
                if item[1] != 4:
                    continue
                self.textbox = item[0]
                textlen = scribus.getTextLength(self.textbox)
                if textlen == 0:
                    continue
                scribus.selectText(0, textlen, self.textbox)
                alltext = scribus.getAllText(self.textbox)
                pos1 = alltext.find("/parameter")
                if pos1 < 0:
                    continue
                pos2 = alltext.find("/endparameter")
                if pos2 < 0:
                    raise ValueError("kein /endparameter nach /parameter")
                pos2 += 13  # len("/endparameter")
                lines = alltext[pos1:pos2].split('\r')[1:-1]
                logger.debug("parsePar lines:%s %s", type(lines), str(lines))
                self.toBeDelPosParam = (pos1, pos2, self.textbox)
                break
            if len(lines) != 0:
                break

        if len(lines) == 0:
            return
        self.includeSub = True
        lx = 0
        selections = {}
        while lx < len(lines):
            line = lines[lx]
            words = line.split()
            if len(words) == 0:
                lx += 1
                continue
            word0 = words[0].lower().replace(":", "")
            if len(words) > 1:
                if word0 == "linktyp":
                    self.linkType = words[1].lower().capitalize()
                    lx += 1
                elif word0 == "ausgabedatei":
                    self.ausgabedatei = words[1]
                    lx += 1
                else:
                    raise ValueError(
                        "Unbekannter Parameter " + word0 +
                        ", erwarte linktyp oder ausgabedatei")
            elif word0 not in ["selektion", "terminselektion", "tourselektion"]:
                raise ValueError(
                    "Unbekannter Parameter " + word0 +
                    ", erwarte selektion, terminselektion oder tourselektion")
            else:
                lx = self.parseSel(word0, lines, lx + 1, selections)

        selection = selections.get("selektion")
        self.gliederung = selection.get("gliederungen")
        self.includeSub = selection.get("mituntergliederungen") == "ja"
        self.start = selection.get("beginn")
        self.end = selection.get("ende")

        sels = selections.get("terminselektion")
        if sels is not None:
            for sel in sels.values():
                self.terminselections[sel.get("name")] = sel
                for key in sel.keys():
                    if key != "name" and not isinstance(sel[key], list):
                        sel[key] = [sel[key]]

        sels = selections.get("tourselektion")
        if sels is not None:
            for sel in sels.values():
                self.tourselections[sel.get("name")] = sel
                for key in sel.keys():
                    if key != "name" and not isinstance(sel[key], list):
                        sel[key] = [sel[key]]

    def setGuiParams(self):
        if self.gui is None:
            return
        self.gui.setLinkType(self.linkType)
        if self.gliederung is not None and self.gliederung != "":
            self.gui.setGliederung(self.gliederung)
        self.gui.setIncludeSub(self.includeSub)
        if self.start is not None and self.start != "":
            self.gui.setStart(self.start)
        if self.end is not None and self.end != "":
            self.gui.setEnd(self.end)
        self.setEventType()
        self.setRadTyp()
        if self.toBeDelPosParam is None:
            self.gui.disableStart()
            logger.error("No /parameter - /endparameter section in document, Start Button disabled")

    def setEventType(self):
        typ = ""
        if len(self.terminselections) != 0 and len(self.tourselections) != 0:
            typ = "Alles"
        elif len(self.terminselections) != 0:
            typ = "Termin"
        elif len(self.tourselections) != 0:
            typ = "Radtour"
        if typ != "":
            self.gui.setEventType(typ)

    def setRadTyp(self):
        rts = set()
        for sel in self.tourselections.values():
            l = sel.get("radtyp")
            if l is None or len(l) == 0:
                l = [self.gui.getRadTyp()]
            for elem in l:
                rts.add(elem)
        if "Alles" in rts:
            typ = "Alles"
        elif len(rts) == 1:
            typ = rts.pop()
        else:
            typ = "Alles"
        self.gui.setRadTyp(typ)

    def getIncludeSub(self):
        return self.includeSub

    def getEventType(self):
        if len(self.terminselections) != 0 and len(self.tourselections) != 0:
            return "Alles"
        if len(self.terminselections) != 0:
            return "Termin"
        if len(self.tourselections) != 0:
            return "Radtour"
        return self.gui.getEventType()

    def getRadTyp(self):
        rts = set()
        for sel in self.tourselections.values():
            l = sel.get("radtyp")
            if l is None or len(l) == 0:
                l = [self.gui.getRadTyp()]
            for elem in l:
                rts.add(elem)
        if "Alles" in rts:
            return "Alles"
        if len(rts) == 1:
            return rts[0]
        return "Alles"

    def getUnitKeys(self):
        return self.gliederung

    def getStart(self):
        return self.start

    def getEnd(self):
        return self.end

    def parseSel(self, word, lines, lx, selections):
        selections[word] = sel = sel2 = {}
        while lx < len(lines):
            line = lines[lx]
            if line.strip() == "":
                lx += 1
                continue
            if not line[0].isspace():
                return lx
            words = line.split()
            word0 = words[0].lower().replace(":", "")
            if word0 == "name":
                word1 = words[1].lower()
                sel[word1] = sel2 = {}
                sel2["name"] = word1
            else:
                lst = ",".join(words[1:]).split(",")
                sel2[word0] = lst[0] if len(lst) == 1 else lst
            lx += 1
        return lx

    def handleTour(self, tour):
        self.touren.append(tour)

    def handleTermin(self, termin):
        self.termine.append(termin)

    def handleEnd(self):
        self.linkType = self.gui.getLinkType()
        self.gliederung = self.gui.getGliederung()
        self.includeSub = self.gui.getIncludeSub()
        self.start = self.gui.getStart()
        self.end = self.gui.getEnd()

        pos1, pos2, tbox = self.toBeDelPosParam
        scribus.selectText(pos1, pos2 - pos1, tbox)
        scribus.deleteText(tbox)

        pagenum = scribus.pageCount()
        for page in range(1, pagenum + 1):
            scribus.gotoPage(page)
            pageitems = scribus.getPageItems()
            for item in pageitems:
                if item[1] != 4:
                    continue
                self.textbox = item[0]
                self.evalTemplate()

        # hyphenate does not work
        # pagenum = scribus.pageCount()
        # for page in range(1, pagenum + 1):
        #     scribus.gotoPage(page)
        #     pageitems = scribus.getPageItems()
        #     for item in pageitems:
        #         if item[1] != 4:
        #             continue
        #         self.textbox = item[0]
        #         b = scribus.hyphenateText(self.textbox) # seems to have no effect!

        pagenum = scribus.pageCount()
        for page in range(1, pagenum + 1):
            scribus.gotoPage(page)
            pageitems = scribus.getPageItems()
            for item in pageitems:
                if item[1] != 4:
                    continue
                tbox = item[0]
                tbox2 = tbox
                while scribus.textOverflows(tbox2):
                    tbox2 = self.createNewPage(tbox2)
                    self.frameLinks[tbox2] = tbox  # frame tbox2 has tbox as root

        scribus.redrawAll()
        ausgabedatei = self.ausgabedatei
        if ausgabedatei is None or ausgabedatei == "":
            ausgabedatei = "ADFC_" + self.gliederung + (
                "_I_" if self.includeSub else "_") + self.start + "-" + self.end + "_" + self.linkType[0] + ".sla"
        try:
            scribus.saveDocAs(ausgabedatei)
        except Exception as e:
            print("Ausgabedatei", ausgabedatei, "konnte nicht geschrieben werden")
            raise e
        finally:
            self.touren = []
            self.termine = []
            # self.gui.destroy()
            # self.gui.quit()
            self.gui.disableStart()

    def evalTemplate(self):
        pos2 = 0
        while True:
            textlen = scribus.getTextLength(self.textbox)
            if textlen == 0:
                return
            scribus.selectText(0, textlen, self.textbox)
            alltext = scribus.getAllText(self.textbox)
            # logger.debug("alltext: %s %s", type(alltext), alltext)

            pos1 = alltext.find("/template", pos2)
            logger.debug("pos /template=%d", pos1)
            if pos1 < 0:
                return
            pos2 = alltext.find("/endtemplate", pos1)
            if pos2 < 0:
                raise Exception("kein /endtemplate nach /template")
            pos2 += 12  # len("/endtemplate")
            lines = alltext[pos1:pos2].split('\r')
            logger.debug("lines:%s %s", type(lines), str(lines))
            line0 = lines[0]
            lineN = lines[-1]
            # logger.debug("lineN: %s %s", type(lineN), lineN)
            if lineN != "/endtemplate":
                raise ValueError("Die letzte Zeile des templates darf nur /endtemplate enthalten")
            words = line0.split()
            typ = words[1]
            if typ != "/tour" and typ != "/termin" and typ != "/toc":
                raise ValueError("Zweites Wort nach /template muß /tour, /termin  oder /toc sein")
            typ = typ[1:]
            if typ == "toc":
                continue

            sel = words[2]
            if not sel.startswith("/selektion="):
                raise ValueError("Drittes Wort nach /template muß mit /selektion= beginnen")
            sel = sel[11:].lower()
            sels = self.tourselections if typ == "tour" else self.terminselections
            if not sel in sels:
                raise ValueError("Selektion " + sel + " nicht in " + typ + "selektion")
            sel = sels[sel]
            events = self.touren if typ == "tour" else self.termine
            self.insertPos = pos1
            runs = self.makeRuns(pos1, pos2)
            logger.debug("runs:%s", str(runs))
            # can now remove template
            scribus.selectText(pos1, pos2 - pos1, self.textbox)
            scribus.deleteText(self.textbox)
            pos2 = pos1
            self.insertPos = pos1
            self.evalEvents(sel, events, runs)

    def evalEvents(self, sel, events, runs):
        selectedEvents = []
        logger.debug("events: %d", len(events))
        for event in events:
            if self.selecter.selected(event, sel):
                selectedEvents.append(event)
        logger.debug("selEvents: %d", len(selectedEvents))
        if len(selectedEvents) == 0:
            return
        for event in selectedEvents:
            self.eventMsg = event.getTitel() + " vom " + event.getDatum()[0]
            logger.debug("eventMsg: %s", self.eventMsg)
            for run in runs:
                self.run = run
                self.evalRun(event)

    def evalRun(self, event):
        # logger.debug("evalRun1 %s", self.run.text)
        lines = self.run.text.split('\r')
        nl = ""
        for line in lines:
            if not line.startswith("/template") and \
                    not line.startswith("/endtemplate"):
                self.insertText(nl, self.run)
                self.expandLine(line, event)
                nl = "\n"

    def expandLine(self, s, event):
        logger.debug("expand1 <%s>", s)
        spos = 0
        while True:
            mp = paramRE.search(s, spos)
            if mp is None:
                logger.debug("noexp %s", s[spos:])
                self.insertText(s[spos:], self.run)
                return
            gp = mp.group(1).lower()
            # logger.debug("expand2 %s", gp)
            sp = mp.span()
            self.insertText(s[spos:sp[0]], self.run)
            mf = fmtRE.search(s, pos=spos)
            if mf is not None and sp[1] == mf.span()[0]:  # i.e. if ${param] is followed immediately by .fmt()
                gf = mf.group(1)
                sf = mf.span()
                spos = sf[1]
                expanded = self.expandParam(gp, event, gf)
            else:
                expanded = self.expandParam(gp, event, None)
                spos = sp[1]
            # logger.debug("expand3 <%s>", str(expanded))
            if expanded is None:  # special case for beschreibung, handled as markdown
                return
            if isinstance(expanded, list):  # list is n runs + 1 string
                for run in expanded:
                    if isinstance(run, ScrbRun):
                        self.insertText(run.text, run)
                    else:
                        self.insertText(run, self.run)
            else:
                self.insertText(expanded, self.run)

    def expandParam(self, param, event, format):
        try:
            f = self.expFunctions[param]
            return f(event, format)
        except Exception as e:
            err = 'Fehler mit dem Parameter "' + param + \
                  '" des Events ' + self.eventMsg
            logger.exception(err)
            return param

    def expTitel(self, event, _):
        if self.linkType == "Frontend":
            self.url = event.getFrontendLink()
        elif self.linkType == "Backend":
            self.url = event.getBackendLink()
        else:
            self.url = None
        titel = event.getTitel()
        if self.pageNr is not None:
            return titel  # called from evalToc
        logger.info("Titel: %s URL: %s", titel, self.url)
        run = copy.copy(self.run)
        run.pstyle = "MD_P_REGULAR"
        run.cstyle = "MD_C_TOC"  # put the eventId in an invisble font before the titel, for the toc
        run.text = "_evtid_:" + event.getEventItemId() + STX + titel + ETX
        return [run, titel]

    def expBeschreibung(self, event, _):
        desc = event.getBeschreibung(True)
        # did I ever need this?
        # desc = codecs.decode(desc, encoding = "unicode_escape")
        # logger.debug("desc type:%s <<<%s>>>", type(desc), desc)
        self.md.convert(desc)
        self.md.reset()
        return None

    def expSchwierigkeitM(self, tour, _):
        self.run.cstyle = "WD2_Y_"
        return schwierigkeitMMap[tour.getSchwierigkeit()]

    def expPersonen(self, bezeichnung, event):
        tl = event.getPersonen()
        if len(tl) == 0:
            return ""
        run = copy.copy(self.run)
        run.cstyle = "MD_C_BOLD"
        run.text = bezeichnung + ": "
        return [run, ", ".join(tl)]

    def expTourLeiter(self, tour, _):
        return self.expPersonen("Tourleiter", tour)

    def expBetreuer(self, termin, _):
        return self.expPersonen("Betreuer", termin)

    def expAbfahrten(self, tour, _):
        afs = tour.getAbfahrten()
        if len(afs) == 0:
            return ""
        afl = []
        for af in afs:
            if af[1] == "":
                afl.append(af[2])
            else:
                afl.append(af[0] + " " + af[1] + " " + af[2])

        run = copy.copy(self.run)
        run.cstyle = "MD_C_BOLD"
        run.text = "Ort" + ("" if len(afs) == 1 else "e") + ": "
        return [run, ", ".join(afl)]

    def expZusatzInfo(self, tour, _):
        zi = tour.getZusatzInfo()
        if len(zi) == 0:
            return None
        runs = []
        for z in zi:
            x = z.find(':') + 1
            run = copy.deepcopy(self.run)
            run.cstyle = "MD_C_BOLD"
            run.text = z[0:x] + " "
            runs.append(run)
            run = copy.deepcopy(self.run)
            run.text = z[x + 1:] + "\n"
            runs.append(run)
        return runs

    def makeToc(self, firstPageNr):
        pagenum = scribus.pageCount()
        for page in range(1, pagenum + 1):
            scribus.gotoPage(page)
            pageitems = scribus.getPageItems()
            for item in pageitems:
                if item[1] != 4:
                    continue
                self.textbox = item[0]
                self.evalTocTemplate(firstPageNr)
        scribus.redrawAll()

    def evalTocTemplate(self, firstPageNr):
        textlen = scribus.getTextLength(self.textbox)
        if textlen == 0:
            return
        scribus.selectText(0, textlen, self.textbox)
        alltext = scribus.getAllText(self.textbox)
        # logger.debug("alltext: %s %s", type(alltext), alltext)
        pos2 = 0
        while True:
            pos1 = alltext.find("/template", pos2)
            logger.debug("pos /template=%d", pos1)
            if pos1 < 0:
                return
            pos2 = alltext.find("/endtemplate", pos1)
            if pos2 < 0:
                raise Exception("kein /endtemplate nach /template")
            pos2 += 12  # len("/endtemplate")
            lines = alltext[pos1:pos2].split('\r')
            logger.debug("lines:%s %s", type(lines), str(lines))
            line0 = lines[0]
            lineN = lines[-1]
            # logger.debug("lineN: %s %s", type(lineN), lineN)
            if lineN != "/endtemplate":
                raise ValueError("Die letzte Zeile des templates darf nur /endtemplate enthalten")
            words = line0.split()
            typ = words[1]
            if typ != "/tour" and typ != "/termin" and typ != "/toc":
                raise ValueError("Zweites Wort nach /template muß /tour, /termin  oder /toc sein")
            typ = typ[1:]
            if typ != "toc":
                continue
            self.insertPos = pos1
            runs = self.makeRuns(pos1, pos2)
            logger.debug("runs:%s", str(runs))
            # remember template
            self.toBeDelPosToc = (pos1, pos2, self.textbox)
            self.insertPos = pos2
            self.evalTocEvents(runs, firstPageNr)

    def evalTocEvents(self, runs, firstPageNr):
        toc = []
        pagenum = scribus.pageCount()
        foundEvents = 0
        for page in range(1, pagenum + 1):
            scribus.gotoPage(page)
            self.pageNr = firstPageNr + page - 1
            pageitems = scribus.getPageItems()
            for item in pageitems:
                if item[1] != 4:
                    continue
                tbox = item[0]
                tlen = scribus.getTextLength(tbox)
                logger.debug("tbox %s length %d", tbox, tlen)
                if tlen == 0:
                    continue
                scribus.selectText(0, tlen, tbox)
                allText = scribus.getText(tbox)  # getAllText returns text of complete link chain!
                z = 0
                while True:
                    x = allText.find("_evtid_:", z)
                    if x < 0:
                        break
                    y = allText.find(STX, x)
                    evtId = allText[x + 8:y]
                    z = allText.find(ETX, y)
                    titel = allText[y + 1:z]
                    logger.debug("eventid %s, titel %s on page %d", evtId, titel, self.pageNr)
                    event = self.gui.eventServer.getEventById(evtId, titel)
                    toc.append((self.pageNr, event))
                    foundEvents += 1
        logger.debug("sorting")
        toc.sort(key=lambda t: t[1].getDatumRaw())  # sortieren nach Datum
        for (pageNr, event) in toc:
            self.eventMsg = event.getTitel() + " vom " + event.getDatum()[0]
            logger.debug("event %s on page %d", self.eventMsg, self.pageNr)
            self.pageNr = pageNr
            for run in runs:
                self.run = run
                self.evalRun(event)
            self.insertText("\n", self.run)
        self.pageNr = None
        if foundEvents == 0:
            print("Noch keine Events gefunden")
        else:
            # remove template
            pos1, pos2, tbox = self.toBeDelPosToc
            scribus.selectText(pos1, pos2 - pos1, tbox)
            scribus.deleteText(tbox)
            scribus.redrawAll()

    def rmEventIdMarkers(self):
        pagenum = scribus.pageCount()
        for page in range(1, pagenum + 1):
            scribus.gotoPage(page)
            pageitems = scribus.getPageItems()
            for item in pageitems:
                if item[1] != 4:
                    continue
                tbox = item[0]
                # frameLinks nonempty only if starten called from same gui
                if self.frameLinks.get(tbox) is not None:  # i.e. if tbox is not the root of a link chain
                    continue
                # TODO find out if tbox is a linked frame
                tlen = scribus.getTextLength(tbox)
                if tlen == 0:
                    continue
                scribus.selectText(0, tlen, tbox)
                allText = scribus.getAllText(tbox)  # getAllText returns text of complete link chain!
                z = 0
                xl = []
                while True:
                    x = allText.find("_evtid_:", z)
                    if x < 0:
                        break
                    y = allText.find(STX, x)
                    evtId = allText[x + 8:y]
                    z = allText.find(ETX, y)
                    titel = allText[y + 1:z]
                    xl.append((x, z + 1 - x))
                for (x, l) in reversed(xl):  # the reversed is important!
                    scribus.selectText(x, l, tbox)
                    scribus.deleteText(tbox)
        scribus.redrawAll()


def main():
    try:
        scribus.statusMessage('Running script...')
        # scribus.progressReset()
        adfc_gui.main("-scribus")
    finally:
        if scribus.haveDoc() > 0:
            scribus.redrawAll()
        scribus.statusMessage('Done.')
        # scribus.progressReset()


if __name__ == "__main__":
    import cProfile

    cProfile.run("main()", "cprof.prf")
    import pstats

    with open("cprof.txt", "w") as cprf:
        p = pstats.Stats("cprof.prf", stream=cprf)
        p.strip_dirs().sort_stats("cumulative").print_stats(20)
