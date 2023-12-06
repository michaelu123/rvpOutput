# encoding: utf-8

import json
import os
import re

import expand
import markdown
import selektion
import tourRest
from fpdf import FPDF
from myLogger import logger

schwierigkeitMap = {0: "sehr einfach", 1: "sehr einfach", 2: "einfach", 3: "mittel", 4: "schwer", 5: "sehr schwer"}
paramRE = re.compile(r"\${(\w*?)}")
fmtRE = re.compile(r"\.fmt\((.*?)\)")
strokeRE = r'(\~{2})(.+?)\1'
ulRE = r'(\^{2})(.+?)\1'
STX = '\u0002'  # Use STX ("Start of text") for start-of-placeholder
ETX = '\u0003'  # Use ETX ("End of text") for end-of-placeholder
stxEtxRE = re.compile(r'%s(\d+)%s' % (STX, ETX))
headerFontSizes = [0, 24, 18, 14, 12, 10, 8]  # h1-h6 headers have fontsizes 24-8
debug = False


class Style:
    def __init__(self, name: str, typ: str, font: str, fontStyle: str, size: int, color: str, dimen: str):
        self.name = name
        self.type = typ
        self.font = font
        self.fontStyle = fontStyle
        self.size = size
        self.color = color
        self.dimen = dimen

    def copy(self):
        return Style(self.name, self.type, self.font, self.fontStyle, self.size, self.color, self.dimen)

    def __str__(self):
        return self.name


class PDFTreeHandler(markdown.treeprocessors.Treeprocessor):
    def __init__(self, md):
        super().__init__(md)
        self.ancestors = []
        self.states = []
        self.indent = 0
        self.lvl = 0
        self.counter = 0
        self.pdfHandler = None
        self.pdf = None
        self.numbered = False
        self.nodeHandler = {"h1": self.h1, "h2": self.h2, "h3": self.h3, "h4": self.h4, "h5": self.h5, "h6": self.h6,
                            "p": self.p, "strong": self.strong, "em": self.em, "blockquote": self.blockQuote,
                            "stroke": self.stroke,
                            "ul": self.ul, "ol": self.ol, "li": self.li, "a": self.a, "hr": self.hr}

    def run(self, root):
        self.pdfHandler.setStyle(self.pdfHandler.styles.get("body").copy())  # now == curStyle
        self.pdfHandler.align = "L"
        self.indent = 0
        self.pdfHandler.indentX = 0.0
        self.lvl = 4
        self.counter = 0
        for child in root:  # skip <div> root
            self.walkOuter(child)
        root.clear()

    def setDeps(self, pdfHandler):
        self.pdfHandler = pdfHandler
        self.pdf = pdfHandler.pdf

    @staticmethod
    def unescape(m):
        return chr(int(m.group(1)))

    def printLines(self, s):
        s = stxEtxRE.sub(self.unescape, s)  # "STX40ETX" -> chr(40), see markdown/postprocessors/UnescapePostprocessor
        while len(s) > 0:
            x = s.find('\n')
            if x >= 0:
                self.pdfHandler.handleText(s[0:x], None)
                self.pdfHandler.simpleNl()
                s = s[x + 1:]
            else:
                self.pdfHandler.handleText(s, None)
                s = ""

    def walkOuter(self, node):
        global debug
        if debug:
            print(" " * self.lvl, "<<<<")
        try:
            self.nodeHandler[node.tag](node)
            if node.tail is not None:
                self.printLines(node.tail)
        except Exception:
            logger.exception("error in event description")
        if debug:
            print(" " * self.lvl, ">>>>")

    def walkInner(self, node):
        text = node.text
        tail = node.tail
        if text is not None:
            ltext = text.replace("\n", "<nl>")
        else:
            ltext = "None"
        if tail is not None:
            ltail = tail.replace("\n", "<nl>")
        else:
            ltail = "None"
        global debug
        if debug:
            print(" " * self.lvl, "node=", node.tag, ",text=", ltext, "tail=", ltail)
        if text is not None:
            self.printLines(text)
        for dnode in node:
            self.lvl += 4
            self.walkOuter(dnode)
            self.lvl -= 4

    def h1(self, node):
        sav = self.pdfHandler.curStyle.size
        self.pdfHandler.curStyle.size = headerFontSizes[1]
        self.walkInner(node)
        self.pdfHandler.curStyle.size = sav

    def h2(self, node):
        sav = self.pdfHandler.curStyle.size
        self.pdfHandler.curStyle.size = headerFontSizes[2]
        self.walkInner(node)
        self.pdfHandler.curStyle.size = sav

    def h3(self, node):
        sav = self.pdfHandler.curStyle.size
        self.pdfHandler.curStyle.size = headerFontSizes[3]
        self.walkInner(node)
        self.pdfHandler.curStyle.size = sav

    def h4(self, node):
        sav = self.pdfHandler.curStyle.size
        self.pdfHandler.curStyle.size = headerFontSizes[4]
        self.walkInner(node)
        self.pdfHandler.curStyle.size = sav

    def h5(self, node):
        sav = self.pdfHandler.curStyle.size
        self.pdfHandler.curStyle.size = headerFontSizes[5]
        self.walkInner(node)
        self.pdfHandler.curStyle.size = sav

    def h6(self, node):
        sav = self.pdfHandler.curStyle.size
        self.pdfHandler.curStyle.size = headerFontSizes[6]
        self.walkInner(node)
        self.pdfHandler.curStyle.size = sav

    def p(self, node):
        self.pdfHandler.fontStyles = ""
        self.walkInner(node)

    def strong(self, node):
        sav = self.pdfHandler.fontStyles
        self.pdfHandler.fontStyles += "B"
        self.walkInner(node)
        self.pdfHandler.fontStyles = sav

    def stroke(self, node):
        # see below changed code of pyfpdf
        sav = self.pdfHandler.fontStyles
        self.pdfHandler.fontStyles += "U"
        self.walkInner(node)
        self.pdfHandler.fontStyles = sav

    def em(self, node):
        sav = self.pdfHandler.fontStyles
        self.pdfHandler.fontStyles += "I"
        self.walkInner(node)
        self.pdfHandler.fontStyles = sav

    def ul(self, node):
        self.numbered = False
        self.indent += 1
        self.walkInner(node)
        self.indent -= 1

    def ol(self, node):
        self.numbered = True
        sav = self.counter
        self.counter = 1
        self.indent += 1
        self.walkInner(node)
        self.indent -= 1
        self.counter = sav

    def li(self, node):
        if self.numbered:
            text = "  " * (self.indent * 3) + str(self.counter) + ". "
            self.counter += 1
        else:
            text = "  " * (self.indent * 3) + "\u25aa "
        sav = self.pdfHandler.indentX
        self.pdfHandler.indentX = 0.0
        self.printLines(text)
        self.pdfHandler.indentX = self.pdf.get_x()
        self.walkInner(node)
        self.pdfHandler.indentX = sav

    def a(self, node):
        self.pdfHandler.url = node.attrib["href"]
        sav = self.pdfHandler.curStyle.color
        self.pdfHandler.curStyle.color = "238,126,13"
        self.walkInner(node)
        self.pdfHandler.curStyle.color = sav
        self.pdfHandler.url = None

    def blockQuote(self, node):
        node.text = node.tail = None
        sav = self.pdfHandler.align
        if len(node) == 0:  # multi_cell always does a newline et the end
            self.pdfHandler.align = 'J'
        self.walkInner(node)
        self.pdfHandler.align = sav

    def hr(self, _):
        self.pdfHandler.extraNl()
        x = self.pdf.get_x()
        y = self.pdf.get_y()
        self.pdf.line(x, y, self.pdfHandler.pageWidth - self.pdfHandler.margins[2], y)
        self.pdfHandler.extraNl()


class PDFExtension(markdown.Extension):
    def __init__(self):
        super().__init__()
        self.pdfTreeHandler = None

    def extendMarkdown(self, md):
        self.pdfTreeHandler = PDFTreeHandler(md)
        md.treeprocessors.register(self.pdfTreeHandler, "pdftreehandler", 5)
        md.inlinePatterns.register(markdown.inlinepatterns.SimpleTagInlineProcessor(strokeRE, 'stroke'), 'stroke', 40)


class PDFHandler(expand.Expand):
    def __init__(self, gui):
        super().__init__()
        self.gui = gui
        self.styles = {}
        self.terminselections = {}
        self.tourselections = {}
        self.touren = []
        self.termine = []
        self.url = None
        self.margins = None
        self.linespacing = None
        self.linkType = None
        self.ausgabedatei = None
        self.pdf = None
        global debug
        try:
            _ = os.environ["DEBUG"]
            debug = True
        except:
            debug = False
        # testing
        self.gui.pdfTemplateName = "C:/Users/Michael/PycharmProjects/ADFC1/venv/src/template152.json"
        self.pdfExtension = PDFExtension()
        self.md = markdown.Markdown(extensions=[self.pdfExtension])
        if self.gui.pdfTemplateName is None or self.gui.pdfTemplateName == "":
            self.gui.pdfTemplate()
        if self.gui.pdfTemplateName is None or self.gui.pdfTemplateName == "":
            raise ValueError("must specify path to PDF template!")
        try:
            with open(self.gui.pdfTemplateName, "r", encoding="utf-8-sig") as jsonFile:
                self.pdfJS = json.load(jsonFile)
        except Exception as e:
            print(
                "Wenn Sie einen decoding-Fehler bekommen, öffnen Sie " + self.gui.pdfTemplateName + " mit notepad, dann 'Speichern unter' mit Codierung UTF-8")
            raise e
        self.parseTemplate()
        self.selFunctions = selektion.getSelFunctions()

    @staticmethod
    def nothingFound():
        logger.info("Nichts gefunden")
        print("Nichts gefunden")

    def parseTemplate(self):
        for key in ["pagesettings", "fonts", "styles", "selection", "text"]:
            if self.pdfJS.get(key) is None:
                raise ValueError("pdf template " + self.gui.pdfTemplateName + " must have a section " + key)
        pagesettings = self.pdfJS.get("pagesettings")
        leftMargin = pagesettings.get("leftmargin")
        rightMargin = pagesettings.get("rightmargin")
        topMargin = pagesettings.get("topmargin")
        bottomMargin = pagesettings.get("bottommargin")
        self.margins = (leftMargin, topMargin, rightMargin)
        self.linespacing = pagesettings.get("linespacing")  # float
        self.linkType = pagesettings.get("linktype")
        self.ausgabedatei = pagesettings.get("ausgabedatei")
        orientation = pagesettings.get("orientation")[0].upper()  # P or L
        pformat = pagesettings.get("format")
        self.pdf = FPDF(orientation, "mm", pformat)
        self.pageWidth = FPDF.get_page_format(pformat, 1.0)[0] / (72.0 / 25.4)
        self.pdf.add_page()
        self.pdf.set_margins(left=leftMargin, top=topMargin, right=rightMargin)
        self.pdf.set_auto_page_break(True, margin=bottomMargin)
        self.pdfExtension.pdfTreeHandler.setDeps(self)

        self.pdf.add_font("arialuc", "", expand.pyinst("_builtin_fonts/arial.ttf"), True)
        self.pdf.add_font("arialuc", "B", expand.pyinst("_builtin_fonts/arialbd.ttf"), True)
        self.pdf.add_font("arialuc", "BI", expand.pyinst("_builtin_fonts/arialbi.ttf"), True)
        self.pdf.add_font("arialuc", "I", expand.pyinst("_builtin_fonts/ariali.ttf"), True)

        fonts = self.pdfJS.get("fonts")
        for font in iter(fonts):
            family = font.get("family")
            if family is None or family == "":
                raise ValueError("font family not specified")
            file = font.get("file")
            if file is None or file == "":
                raise ValueError("font file not specified")
            fontStyle = font.get("fontstyle")
            if fontStyle is None:
                fontStyle = ""
            unicode = font.get("unicode")
            if unicode is None:
                unicode = True
            self.pdf.add_font(family, fontStyle, file, unicode)
        styles = self.pdfJS.get("styles")
        for style in iter(styles):
            name = style.get("name")
            if name is None or name == "":
                raise ValueError("style name not specified")
            typ = style.get("type")
            if typ is None:
                typ = "text"
            font = style.get("font")
            if font is None and typ != "image":
                raise ValueError("style font not specified")
            fontstyle = style.get("style")
            if fontstyle is None:
                fontstyle = ""
            size = style.get("size")
            if size is None and typ != "image":
                raise ValueError("style size not specified")
            color = style.get("color")
            if color is None:
                color = "0,0,0"  # black
            dimen = style.get("dimen")
            self.styles[name] = Style(name, typ, font, fontstyle, size, color, dimen)
        selection = self.pdfJS.get("selection")
        self.gliederung = selection.get("gliederung")
        if self.gliederung is None or self.gliederung == "":
            self.gliederung = self.gui.getGliederung()
        self.includeSub = selection.get("includesub")
        if self.includeSub is None:
            self.includeSub = self.gui.getIncludeSub()
        self.start = selection.get("start")
        if self.start is None or self.start == "":
            self.start = self.gui.getStart()
        self.end = selection.get("end")
        if self.end is None or self.end == "":
            self.end = self.gui.getEnd()
        sels = selection.get("terminselection")
        for sel in iter(sels):
            self.terminselections[sel.get("name")] = sel
            for key in sel.keys():
                if key != "name" and not isinstance(sel[key], list):
                    sel[key] = [sel[key]]
        sels = selection.get("tourselection")
        for sel in iter(sels):
            self.tourselections[sel.get("name")] = sel
            for key in sel.keys():
                if key != "name" and not isinstance(sel[key], list):
                    sel[key] = [sel[key]]

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

    def handleTour(self, tour):
        self.touren.append(tour)

    def handleTermin(self, termin):
        self.termine.append(termin)

    def handleEnd(self):
        print("Template", self.gui.pdfTemplateName, "wird abgearbeitet")
        if self.linkType is None or self.linkType == "":
            self.linkType = self.gui.getLinkType()
        lines = self.pdfJS.get("text")
        lineCnt = len(lines)
        lineNo = 0
        self.pdf.set_x(self.margins[0])  # left
        self.pdf.set_y(self.margins[1])  # top
        self.setStyle(self.styles.get("body"))
        self.pdf.cell(w=0, h=10, txt="", ln=1)
        while lineNo < lineCnt:
            line = lines[lineNo]
            if line.startswith("/comment"):
                lineNo += 1
                continue
            if line.startswith("/template"):
                t1 = lineNo
                lineNo += 1
                while not lines[lineNo].startswith("/endtemplate"):
                    lineNo += 1
                t2 = lineNo
                lineNo += 1
                tempLines = lines[t1:t2]  # /endtemplate not included
                self.evalTemplate(tempLines)
            else:
                self.evalLine(line, None)
                lineNo += 1
        if self.ausgabedatei is None or self.ausgabedatei == "":
            self.ausgabedatei = self.gui.pdfTemplateName.rsplit(".", 1)[0] + "_" + self.linkType[0] + ".pdf"
        self.pdf.output(dest='F', name=self.ausgabedatei)
        print("Ausgabedatei", self.ausgabedatei, "wurde erzeugt")
        try:
            opath = os.path.abspath(self.ausgabedatei)
            os.startfile(opath)
        except Exception:
            logger.exception("opening " + self.ausgabedatei)

    def simpleNl(self):
        x = self.pdf.get_x()
        if x > self.margins[0]:
            self.pdf.ln()

    def extraNl(self):
        self.simpleNl()
        self.pdf.ln()

    def evalLine(self, line, event):
        if line.strip() == "":
            self.extraNl()
            return
        global debug
        if debug:
            print("line", line)
        text = []
        self.align = "L"
        self.fontStyles = ""
        self.curStyle = self.styles.get("body")
        self.indentX = 0.0
        words = line.split()
        l = len(words)
        last = l - 1
        for i in range(l):
            word = words[i]
            if word.startswith("/"):
                cmd = word[1:]
                if cmd in self.styles.keys():
                    self.handleText("".join(text), event)
                    text = []
                    self.curStyle = self.styles.get(cmd)
                elif cmd in ["right", "left", "center", "block"]:
                    self.handleText("".join(text), event)
                    text = []
                    self.align = cmd[0].upper()
                    if self.align == 'B':
                        self.align = 'J'  # justification
                elif cmd in ["bold", "italic", "underline"]:
                    self.handleText("".join(text), event)
                    text = []
                    self.fontStyles += cmd[0].upper()
                else:
                    if i < last:
                        word = word + " "
                    text.append(word)
            else:
                word = word.replace("\uaffe", "\n")
                if i < last:
                    word = word + " "
                text.append(word)
        self.handleText("".join(text), event)
        self.simpleNl()

    def evalTemplate(self, lines):
        global debug
        if debug:
            print("template:")
        words = lines[0].split()
        typ = words[1]
        if typ != "/tour" and typ != "/termin":
            raise ValueError("second word after /template must be /tour or /termin")
        typ = typ[1:]
        sel = words[2]
        if not sel.startswith("/selection="):
            raise ValueError("third word after /template must start with /selection=")
        sel = sel[11:]
        sels = self.tourselections if typ == "tour" else self.terminselections
        if sel not in sels:
            raise ValueError("selection " + sel + " not in " + typ + "selections")
        sel = sels[sel]
        events = self.touren if typ == "tour" else self.termine
        self.evalEvents(sel, events, lines[1:])

    def evalEvents(self, sel, events, lines):
        selectedEvents = []
        for event in events:
            if selektion.selected(event, sel):
                selectedEvents.append(event)
        if len(selectedEvents) == 0:
            return
        lastEvent = selectedEvents[-1]
        for event in selectedEvents:
            for line in lines:
                if line.startswith("/comment"):
                    continue
                self.evalLine(line, event)
            if event != lastEvent:  # extra line between events, not after the last one
                self.evalLine("", None)

    def handleText(self, s: str, event):
        s = self.expand(s, event)
        if s is None or s == "":
            return
        # print("Text:", s)
        if self.curStyle.type == "image":
            self.drawImage(expand.pyinst(s))
            return
        style = self.curStyle.copy()
        for fs in self.fontStyles:
            if style.fontStyle.find(fs) == -1:
                style.fontStyle += fs
        # self.fontStyles = ""
        self.setStyle(style)
        h = (style.size * 0.35278 + self.linespacing)
        if self.align == 'J':
            self.pdf.multi_cell(w=0, h=h, txt=s, border=0, align=self.align, fill=0)
        elif self.align == 'R':
            self.pdf.cell(w=0, h=h, txt=s, border=0, ln=0, align=self.align, fill=0, link=self.url)
        else:
            try:
                w = self.pdf.get_string_width(s)
            except Exception:
                w = 0
            x = self.pdf.get_x()
            if (x + w) >= (self.pageWidth - self.margins[2]):  # i.e. exceeds right margin
                self.multiline(h, s)
            else:
                self.pdf.cell(w=w, h=h, txt=s, border=0, ln=0, align=self.align, fill=0, link=self.url)
            # x = self.pdf.get_x()
        self.url = None

    def multiline(self, h: float, s: str):
        """ line too long, see if I can split line after blank """
        x = self.pdf.get_x()
        l = len(s)
        # TODO limit l so that we do not    search too long for a near enough blank
        while l > 0:
            w = self.pdf.get_string_width(s)
            if (x + w) < (self.pageWidth - 1 - self.margins[2]):
                self.pdf.cell(w=w, h=h, txt=s, border=0, ln=0, align=self.align, fill=0, link=self.url)
                # x = self.pdf.get_x()
                return
            nlx = s.find("\n", 0, l)
            lb = s.rfind(' ', 0, l)  # last blank
            if 0 <= nlx < lb:
                lb = nlx + 1
            if lb == -1:  # can not split line
                if x > self.margins[0]:
                    self.pdf.ln()
                    if self.indentX > 0.0:
                        self.pdf.set_x(self.indentX)
                    x = self.pdf.get_x()
                    l = len(s)
                    continue
                else:  # emergency, can not split line
                    w = self.pdf.get_string_width(s)
                    self.pdf.cell(w=w, h=h, txt=s, border=0, ln=1, align=self.align, fill=0, link=self.url)
                    return
            sub = s[0:lb]
            w = self.pdf.get_string_width(sub)
            if (x + w) >= (self.pageWidth - 1 - self.margins[2]):
                l = lb
                continue
            self.pdf.cell(w=w, h=h, txt=sub, border=0, ln=0, align=self.align, fill=0, link=self.url)
            x = self.pdf.get_x()
            s = s[lb + 1:]
            w = self.pdf.get_string_width(s)
            if x > self.margins[0] and (x + w) >= (self.pageWidth - 1 - self.margins[2]):
                self.pdf.ln()
                if self.indentX > 0.0:
                    self.pdf.set_x(self.indentX)
                x = self.pdf.get_x()
            l = len(s)

    def setStyle(self, style: Style):
        # print("Style:", style)
        self.pdf.set_font(style.font, style.fontStyle, style.size)
        rgb = style.color.split(',')
        self.pdf.set_text_color(int(rgb[0]), int(rgb[1]), int(rgb[2]))

    def drawImage(self, imgName: str):
        style = self.curStyle
        dimen = style.dimen  # 60x40, wxh
        wh = dimen.split('x')
        w = int(wh[0])
        h = int(wh[1])
        x = self.pdf.get_x()
        y = self.pdf.get_y()
        if self.align == 'R':
            x = self.pageWidth - self.margins[2] - w - 10
        y -= h  # align lower edge of image with baseline of text (or so)
        if y < self.margins[1]:
            y = self.margins[1]
        self.pdf.image(imgName.strip(), x=x, y=y, w=w)  # h=h
        self.pdf.set_y(self.pdf.get_y() + 7)

    def expBeschreibung(self, tour, _):
        desc = tour.getBeschreibung(True)
        # desc = codecs.decode(desc, encoding = "unicode_escape")
        self.md.convert(desc)
        self.md.reset()
        return None

    def expTourLeiter(self, tour, _):
        tl = tour.getPersonen()
        if len(tl) == 0:
            return
        self.evalLine("/bold Tourleiter: /block " + "\uaffe".join(tl), tour)

    def expAbfahrten(self, tour, _):
        afs = tour.getAbfahrten()
        if len(afs) == 0:
            return
        afl = [af[0] + " " + af[1] + " " + af[2] for af in afs]
        self.evalLine("/bold Ort" + ("" if len(afs) == 1 else "e") + ": /block " + "\uaffe".join(afl), tour)

    def expBetreuer(self, termin, _):
        tl = termin.getPersonen()
        if len(tl) == 0:
            return
        self.evalLine("/bold Betreuer: /block " + "\uaffe".join(tl), termin)

    def expZusatzInfo(self, tour, _):
        zi = tour.getZusatzInfo()
        if len(zi) == 0:
            return
        self.evalLine("/bold Zusatzinfo: /block " + "\uaffe".join(zi), tour)

    """
    changed code in fpdf/fpdf.py, to change underline to "stroke through letter" (i.e. line half a fontsize higher and thinner)
    def _dounderline(self, x, y, txt):
        #Underline text
        up=self.current_font['up']
        ut=self.current_font['ut']return
        w=self.get_string_width(txt, True)+self.ws*txt.count(' ')
        y -= self.font_size / 2.0 # MUH this line added to stroke through letter instead underline
        return sprintf('%.2f %.2f %.2f %.2f re f',x*self.k,(self.h-(y-up/1000.0*self.font_size))*self.k,w*self.k,-ut/2000.0*self.font_size_pt)
        # MUH 2000 was 1000, seems to be line thickness
    """
