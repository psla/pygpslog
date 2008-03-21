# Copyright: see http://www.iconarchive.com/icons/milosz-wlazlo/boomy/license.txt
import os, appuifw

ICONFILE   = "gpslogico.jpg"
ICONMIF    = "gpslogico.mbm"

__ICONDEST = r"C:\Data\Others"
for d in [".", os.path.dirname(__file__), r"E:\Python", r"C:\Python"]:
  __thisdir = os.path.normcase(os.path.abspath(d))
  if os.path.exists(os.path.join(__thisdir, ICONFILE)): break
__ICONMIF = os.path.join(__ICONDEST, ICONMIF.replace(".", "_%s."%appuifw.app.uid()))

# the MIF/MBM file must be publicly accessible
if not os.path.exists(__ICONMIF) or\
   os.stat(os.path.join(__thisdir, ICONMIF)).st_mtime > os.stat(__ICONMIF).st_mtime:
  import shutil
  shutil.copy2(os.path.join(__thisdir, ICONMIF), __ICONMIF)

ICONFILE   = os.path.abspath(os.path.join(__thisdir, ICONFILE))
ICONMIF    = __ICONMIF
ICONDEF    = [ "Accommodation",  "Businesses",    "Telecommunicat.",
               "Education",     "Entertainment", "Food & drink",
               "Geographical locat.", "Outdoor activities", "People",
               "Public services", "Places of worship", "Shopping",
               "Sightseeing", "Sports", "Transport", "User" ]

del __ICONMIF
del __ICONDEST
