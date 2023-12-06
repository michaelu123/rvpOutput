import sys

try:
    import scribus
except ModuleNotFoundError:
    raise ImportError

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

textbox = scribus.getSelectedObject()
ftype = scribus.getObjectType(textbox)

if ftype != "TextFrame":
    scribus.messageBox('Scribus - Script Error', "This is not a textframe. Try again.", scribus.ICON_WARNING,
                       scribus.BUTTON_OK)
    sys.exit(2)

scribus.insertText("12345", 0, textbox, url="http://www.heise.de")
scribus.messageBox('Done', "DOne", scribus.ICON_WARNING, scribus.BUTTON_OK)
