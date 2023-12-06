rem pyinstaller -y  -F adfc_rest2.py myLogger.py printHandler.py textHandler.py tourRest.py tourServer.py
rem pyinstaller -y -F --debug --log-level DEBUG -p  ..\lib\site-packages --add-data "fonts/*.ttf;fonts" --add-data "ADFC_LOGO.png;." adfc_gui.py myLogger.py printHandler.py textHandler.py rawHandler.py pdfHandler.py tourRest.py tourServer.py
rem pyinstaller -y -F                           -p  ..\lib\site-packages --add-data "_builtin_fonts/*.ttf;_builtin_fonts" --add-data "ADFC_MUENCHEN.png;." adfc_gui.py myLogger.py printHandler.py textHandler.py rawHandler.py pdfHandler.py tourRest.py tourServer.py
rem pyinstaller -y -F --debug all --log-level TRACE -p  ..\lib\site-packages adfc_gui.py myLogger.py printHandler.py textHandler.py rawHandler.py docxHandler.py tourRest.py tourServer.py event.py eventXml.py
rem pyinstaller -y --debug=imports -F -p  ..\lib\site-packages adfc_gui2.spec
pyinstaller -y -F -p  ..\lib\site-packages adfc_gui.py myLogger.py printHandler.py textHandler.py rawHandler.py docxHandler.py tourRest.py tourServer.py event.py eventXml.py

