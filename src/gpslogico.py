# Copyright: see http://www.iconarchive.com/icons/milosz-wlazlo/boomy/license.txt
import os

ICONFILE   = "gpslogico.jpg"

for d in [".", os.path.dirname(__file__), r"E:\Python", r"C:\Python"]:
  __thisdir = os.path.normcase(os.path.abspath(d))
  if os.path.exists(os.path.join(__thisdir, ICONFILE)): break

ICONFILE   = os.path.abspath(os.path.join(__thisdir, ICONFILE))
ICONCAT    = [ "Accomodation",  "Businesses",    "Telecommunicat.",
               "Education",     "Entertainment", "Food & drink",
               "Geographical locat.", "Outdoor activities", "People",
               "Public services", "Places of worship", "Shopping",
               "Sightseeing", "Sports", "Transport" ]
