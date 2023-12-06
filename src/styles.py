# encoding: utf-8

import copy

from myLogger import logger

try:
    import scribus
except ImportError:
    import scribusTest

# change here
BASE_FONT = "Cambria Regular"
BASE_FONTSIZE = 8.0
BASE_COLOR = "Black"
LANG_CODE = "de_DE"
INDENT = 12  # indentation of (bulleted, numbered) list, in Points (!?)
BULLET_FONT = "Symbol Regular"
BULLET_CHAR = "\xB7"
HYPHEN_FONT = "Symbol"
HYPhEN_CHAR = "\x2D"

MD_P_REGULAR = {"name": "MD_P_REGULAR", "linespacingmode": 1, "alignment": 0, "charstyle": "MD_C_REGULAR"}
MD_P_BLOCK = {"name": "MD_P_BLOCK", "linespacingmode": 1, "alignment": 3, "charstyle": "MD_C_REGULAR"}

MD_C_REGULAR = {"name": "MD_C_REGULAR", "font": BASE_FONT, "fontsize": BASE_FONTSIZE, "fillcolor": BASE_COLOR,
                "language": LANG_CODE}
MD_C_BOLD = {"name": "MD_C_BOLD", "font": BASE_FONT, "fontsize": BASE_FONTSIZE, "fillcolor": BASE_COLOR,
             "features": "bold", "language": LANG_CODE}
MD_C_ITALIC = {"name": "MD_C_ITALIC", "font": BASE_FONT, "fontsize": BASE_FONTSIZE, "fillcolor": BASE_COLOR,
               "features": ["italic"], "language": LANG_CODE}
MD_C_UNDERLINE = {"name": "MD_C_UNDERLINE", "font": BASE_FONT, "fontsize": BASE_FONTSIZE, "fillcolor": BASE_COLOR,
                  "features": ["underline"], "language": LANG_CODE}
MD_C_STRIKE = {"name": "MD_C_STRIKE", "font": BASE_FONT, "fontsize": BASE_FONTSIZE, "fillcolor": BASE_COLOR,
               "features": ["strike"], "language": LANG_CODE}
MD_C_BULLET = {"name": "MD_C_BULLET", "font": BULLET_FONT, "fontsize": BASE_FONTSIZE, "fillcolor": BASE_COLOR,
               "language": LANG_CODE}
MD_C_TOC = {"name": "MD_C_TOC", "font": "Arial Regular", "fontsize": 1, "fillcolor": "None", "scaleh": 0.1}
# MD_C_TOC should display Fontsize 1, Tracking 0%, Horizontal Scaling 10%, units seem to be confused

MD_P_H1 = {"name": "MD_P_H1", "linespacingmode": 0, "linespacing": 24, "charstyle": "MD_C_H1"}
MD_C_H1 = {"name": "MD_C_H1", "font": BASE_FONT, "fontsize": 24, "fillcolor": BASE_COLOR, "language": LANG_CODE}
MD_P_H2 = {"name": "MD_P_H2", "linespacingmode": 0, "linespacing": 18, "charstyle": "MD_C_H2"}
MD_C_H2 = {"name": "MD_C_H2", "font": BASE_FONT, "fontsize": 18, "fillcolor": BASE_COLOR, "language": LANG_CODE}
MD_P_H3 = {"name": "MD_P_H3", "linespacingmode": 0, "linespacing": 14, "charstyle": "MD_C_H3"}
MD_C_H3 = {"name": "MD_C_H3", "font": BASE_FONT, "fontsize": 14, "fillcolor": BASE_COLOR, "language": LANG_CODE}
MD_P_H4 = {"name": "MD_P_H4", "linespacingmode": 0, "linespacing": 12, "charstyle": "MD_C_H4"}
MD_C_H4 = {"name": "MD_C_H4", "font": BASE_FONT, "fontsize": 12, "fillcolor": BASE_COLOR, "language": LANG_CODE}
MD_P_H5 = {"name": "MD_P_H5", "linespacingmode": 0, "linespacing": 10, "charstyle": "MD_C_H5"}
MD_C_H5 = {"name": "MD_C_H5", "font": BASE_FONT, "fontsize": 10, "fillcolor": BASE_COLOR, "language": LANG_CODE}
MD_P_H6 = {"name": "MD_P_H6", "linespacingmode": 0, "linespacing": 8, "charstyle": "MD_C_H6"}
MD_C_H6 = {"name": "MD_C_H6", "font": BASE_FONT, "fontsize": 8, "fillcolor": BASE_COLOR, "language": LANG_CODE}

pstyleList = [MD_P_REGULAR, MD_P_BLOCK, MD_P_H1, MD_P_H2, MD_P_H3, MD_P_H4, MD_P_H5, MD_P_H6]
cstyleList = [MD_C_REGULAR, MD_C_BOLD, MD_C_ITALIC, MD_C_UNDERLINE, MD_C_STRIKE, MD_C_BULLET, MD_C_TOC, MD_C_H1,
              MD_C_H2, MD_C_H3, MD_C_H4, MD_C_H5, MD_C_H6]
pstyles = {}
cstyles = {}
pstylesConfigured = {}
cstylesConfigured = {}

for st in pstyleList:
    pstyles[st["name"]] = st
for st in cstyleList:
    cstyles[st["name"]] = st


def checkPStyleExi(style):
    logger.debug("checkPExi %s", style)
    if style in pstyles:
        if style not in pstylesConfigured:
            logger.debug("createParagraphStyle %s", str(pstyles[style]))
            scribus.createParagraphStyle(**pstyles[style])
            pstylesConfigured[style] = style
        return True
    raise ValueError("Paragraph Style " + style + " not defined")


def checkCStyleExi(style):
    logger.debug("checkCExi %s", style)
    if style in cstyles:
        if style not in cstylesConfigured:
            logger.debug("createCharStyle %s", str(cstyles[style]))
            scribus.createCharStyle(**cstyles[style])
            cstylesConfigured[style] = style
        return True
    raise ValueError("Character Style " + style + " not defined")


def modifyFont(cStyle, fontStyles):
    if fontStyles is None or fontStyles == "":
        return cStyle

    # normalize fontStyles
    nfs = ""
    if 'B' in fontStyles:
        nfs += "B"
    if 'I' in fontStyles:
        nfs += "I"
    if 'U' in fontStyles:
        nfs += "U"
    if 'X' in fontStyles:
        nfs += "X"
    fontStyles = nfs

    nStyle = cStyle + "_" + fontStyles
    if nStyle in cstylesConfigured:
        return nStyle
    style = copy.deepcopy(cstyles[cStyle])
    style["name"] = nStyle
    features = []
    if 'B' in fontStyles:
        style["font"] = style["font"].replace(" Regular", "") + " Bold"  # Arial Regular -> Arial Bold
    if 'I' in fontStyles:
        style["font"] = style["font"].replace(" Regular", "") + " Italic"
    for c in fontStyles:
        # does not work
        # if c == 'B':
        #     features.append("bold")
        # elif c == 'I':
        #     features.append("italic")
        # elif c == 'U':
        if c == 'U':
            features.append("underline")
        elif c == 'X':
            features.append("strike")
    style["features"] = ",".join(features)
    logger.debug("createCharStyle %s", str(style))
    scribus.createCharStyle(**style)
    cstylesConfigured[nStyle] = style
    cstyles[nStyle] = style
    return nStyle


# see https://wiki.scribus.net/canvas/Bullets_and_numbered_lists
def listStyle(pstyle, pIndent):  # pstyle could be MD_P_REGULAR or MD_P_BLOCK
    nStyle = pstyle + "_" + str(pIndent)
    if nStyle in pstylesConfigured:
        return nStyle
    style = copy.deepcopy(pstyles[pstyle])
    style["name"] = nStyle
    style["tabs"] = [(pIndent * INDENT, 0, "")]
    style["leftmargin"] = pIndent * INDENT
    style["firstindent"] = INDENT * -1
    logger.debug("createParagraphStyle %s", str(style))
    scribus.createParagraphStyle(**style)
    pstylesConfigured[nStyle] = style
    pstyles[nStyle] = style
    return nStyle


def bulletStyle():
    checkCStyleExi("MD_C_BULLET")
    return "MD_C_BULLET"


"""
FUNCTION:
createParagraphStyle
"name" [required] -> specifies the name of the paragraphstyle to create
linespacingmode [optional] -> specifies the linespacing mode; possible modes are:
fixed linespacing:          0
automatic linespacing:      1
baseline grid linespacing:  2
linespacing [optional] -> specifies the linespacing if using fixed linespacing
alignment [optional] -> specifies the alignment of the paragraph
-> left:     0
-> center:   1
-> right:    2
-> justify:  3
-> extend:   4
leftmargin [optional], rightmargin [optional] -> specify the margin
gapbefore [optional], gapafter [optional] -> specify the gaps to the heading and following paragraphs
firstindent [optional] -> the indent of the first line
hasdropcap [optional] -> specifies if there are caps (1 = yes, 0 = no)
dropcaplines [optional] -> height (in lines) of the caps if used
dropcapoffset [optional] -> offset of the caps if used
"charstyle" [optional] -> char style to use


createCharStyle(...)
"name" [required] -> name of the char style to create
"font" [optional] -> name of the font to use
fontsize [optional] -> font size to set (double)
"features" [optional] -> nearer typographic details can be defined by a string that might contain the following phrases comma-seperated (without spaces!):
-> inherit
-> bold
-> italic
-> underline
-> underlinewords
-> strike
-> superscript
-> subscript
-> outline
-> shadowed
-> allcaps
-> smallcaps
"fillcolor" [optional], "fillshade" [optional] -> specify fill options
"strokecolor" [optional], "strokeshade" [optional] -> specify stroke options
baselineoffset [optional] -> offset of the baseline
shadowxoffset [optional], shadowyoffset [optional] -> offset of the shadow if used
outlinewidth [optional] -> width of the outline if used
underlineoffset [optional], underlinewidth [optional] -> underline options if used
strikethruoffset [optional], strikethruwidth [optional] -> strikethru options if used
scaleh [optional], scalev [optional] -> scale of the chars
tracking [optional] -> tracking of the text
"language" [optional] -> language code
"""

"""
Scribus script commands may be produced with this code. Paste it into Scribus Console and enter F9

def printScribusCommands():
    d = dir(scribus)
    for j in d:
        try:
            res = eval(j+'.__doc__')
            if res[0:5] == 'float':
                print('\nCONSTANT:\n',j,'\nVALUE: float')
                exec('print('+j+')')
            elif res[0:5] == 'int([':
                print('\nCONSTANT:\n',j,'\nVALUE: integer')
                exec('print('+j+')')
            elif res[0:5] == 'Built':
                print('\nTUPLE:\n',j,'\nVALUE:')
                exec('print(repr('+j+'))')
            elif res[0:4] == 'str(':
                print('\nSTRING:\n',j,'\nVALUE:')
                exec('print(repr('+j+'))')
            else:
                print('\nFUNCTION:\n'+j+'\n\nSYNTAX:')
                print( res)
        except: pass

printScribusCommands()
"""

if __name__ == '__main__':
    import scribusTest as scribus

    checkCStyleExi("MD_C_REGULAR")
    checkPStyleExi("MD_P_REGULAR")
