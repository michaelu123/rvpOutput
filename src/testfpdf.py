from fpdf import FPDF

def get_me_a_pyfpdf():
    title = "This The Doc Title"
    heading = "First Paragraph"
    #text = 'blö ' * 10000
    text = u"""
    English: Hello World 
    Greek: Γειά σου κόσμος 
    Polish: Witaj świecie
    Portuguese: Olá mundo
    Russian: Здравствуй, Мир
    Vietnamese: Xin chào thế giới
    Arabic: مرحبا العالم
    Hebrew: שלום עולם
    """
    text = "abcdefghijklmnopqrstuvwxyzäöüABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜ!§$&/()=?@ß€"  # € crasht!?!?

    font = "arial"
    ptsize=12 # 1 mm = 2.83465 points, 1 point = 0.35278 mm
    cwidth=0 # up to right margin
    cHeight=9 # default=0


    pdf = FPDF('P',"mm", "A4")

    pdf.add_font('ARIAL', '', '_builtin_fonts/ARIAL.ttf', uni=True)
    pdf.add_font('ARIAL', 'B', '_builtin_fonts/ARIALBD.ttf', uni=True)
    pdf.add_font('ARIAL', 'BI', '_builtin_fonts/ARIALBI.ttf', uni=True)
    pdf.add_font('ARIAL', 'I', '_builtin_fonts/ARIALI.ttf', uni=True)

    pdf.add_page()

    pdf.set_font(font, 'B', 36)
    pdf.set_text_color(15,74,124)
    pdf.cell(w=cwidth, h=cHeight, txt="Medieninformation", border=0, ln=1, align='L', fill=0)
    pdf.image("ADFC_MUENCHEN.PNG",x=130, y=0, w=60,h=30)
    pdf.set_text_color(0,0,0)
    pdf.set_y(40) # image height + some more

    for t in text.split("\n"):
        pdf.set_font(font, '', ptsize)
        pdf.cell(w=cwidth, h=cHeight, txt=t, border=0, ln=1, align='L', fill=0)
        pdf.set_font(font, 'B', ptsize)
        pdf.cell(w=cwidth, h=cHeight, txt="B_" + t, border=0, ln=1, align='L', fill=0)
        pdf.set_font(font, 'I', ptsize)
        pdf.cell(w=cwidth, h=cHeight, txt="I_" + t, border=0, ln=1, align='L', fill=0)
        pdf.set_font(font, 'U', ptsize)
        pdf.cell(w=cwidth, h=cHeight, txt="U_" + t, border=0, ln=1, align='L', fill=0)
        pdf.set_font(font, 'BI', ptsize)
        pdf.cell(w=cwidth, h=cHeight, txt="BI_" + t, border=0, ln=1, align='L', fill=0)
        pdf.set_font(font, 'IU', ptsize)
        pdf.cell(w=cwidth, h=cHeight, txt="IU_" + t, border=0, ln=1, align='L', fill=0)
        pdf.set_font(font, 'BIU', ptsize)
        pdf.cell(w=cwidth, h=cHeight, txt="BIU_" + t, border=0, ln=1, align='L', fill=0)


    pdf.set_font(font, '', ptsize)
    pdf.cell(w=cwidth, h=cHeight, txt="C_Hallo", border=0, ln=1, align='C', fill=0)
    pdf.set_font(font, '', ptsize)
    pdf.cell(w=cwidth, h=cHeight, txt="R_Hallo", border=0, ln=1, align='R', fill=0)
    pdf.set_font(font, '', ptsize)
    pdf.cell(w=cwidth, h=cHeight, txt="L_Hallo", border=0, ln=1, align='L', fill=0)
    pdf.set_font(font, '', ptsize)
    pdf.multi_cell(w=cwidth, h=cHeight, txt="B_Hallo " * 100, border=0, align='B', fill=0)

    for ptsz in range(6,20,1):
        pdf.set_font(font, '', ptsz)
        pdf.multi_cell(w=cwidth, h=ptsz * 0.35278 + 2.0, txt="B_Hallo " * 100, border=0, align='B', fill=0)


    """
    pdf.set_font(font, 'B', 15)
    pdf.cell(w=cwidth, h=cHeight, txt=title, border=0, ln=1, align='C', fill=0)
    pdf.set_font(font, 'B', 15)
    pdf.cell(w=0, h=6, txt=heading, border=0, ln=1, align='L', fill=0)
    pdf.set_font(font, '', ptsize)
    pdf.multi_cell(w=0, h=5, txt=text)
    #response.headers['Content-Type'] = 'application/pdf'
    """
    return pdf.output(dest='F', name="testfpdf.pdf")

get_me_a_pyfpdf()
pass
