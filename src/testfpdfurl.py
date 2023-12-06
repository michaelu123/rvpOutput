from fpdf import FPDF

class PDFHandler:
    def __init__(self):
        orientation = "portrait"
        pformat = "A4"
        topMargin = 20
        leftMargin = 30
        rightMargin = 20
        bottomMargin = 20

        self.pdf = FPDF(orientation, "mm", pformat)
        self.pageWidth = FPDF.get_page_format(pformat, 1.0)[0] / (72.0 / 25.4)
        self.pdf.set_margins(left=leftMargin, top=topMargin, right=rightMargin)
        self.pdf.set_auto_page_break(True, margin=bottomMargin)
        self.linespacing = 1.5
        self.margins = (leftMargin, topMargin, rightMargin)
        self.ptsize = 12
        self.align = "L"
        self.indentX = 0.0
        self.pdf.add_page()
        self.pdf.set_font("ARIAL", '', self.ptsize)

    def handleText(self, s: str, u:str):
        if s.find("27") > 0:
            print("found")
        self.url = u
        h = (self.ptsize * 0.35278 + self.linespacing)
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


def get_me_a_pyfpdf():
    pdfHandler = PDFHandler()
    for i in range(50):
        pdfHandler.handleText("Click this link " + str(i) + " ... ....", "http://www.example.com/" + str(i))
    return pdfHandler.pdf.output(dest='F', name="testfpdf.pdf")

get_me_a_pyfpdf()
pass
