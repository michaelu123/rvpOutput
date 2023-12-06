# adfc2
read bicycle events from "ADFC Tourenportal" and convert to text 
or Word (.docx) or something else.

This is a Python program running in a UI, if started from adfc_gui.py.
Other entry points let it run in a command line, or produce cal records.

There was support to run as a Scribus script, when Scribus is told to run the script 
adfc_rest2.py or scrbHandler.py. Scribus at the time of programming used 
Python2, and had to be modified a bit. Currently it will not work. 
The preferred approach is to generate a .docx file and import it to 
Affinity Publisher.

It searches first for all tours belonging to a "Gliederung", i.e. ADFC
sub organization, then gets detailed info about each tour, and outputs
them in various formats, including MSWord/.docx, or produces other output.

When tp2vadb.py is called, the program creates either an XML file 
that is used to publish events to the "Veranstaltungsdatenbank Hamburg",
or CALDAV entries.

