import sys, os, stat
sys.path += [ "..\util" ]
# !!! assert sys.version_info < (2,3,0), "Please run under Python 2.2!"

from ensutil import setup, mergesis, findUid, findVersion

appname = "PyGpsLog"
srcdir  = "src"
caps    = "ReadUserData+WriteUserData+NetworkServices+"\
          "LocalServices+UserEnvironment"
scaps   = caps + "+Location+SwEvent+ReadDeviceData+WriteDeviceData"

SYMBIAN_UID=0xEDED0AF2

copy = [
  ("../../GPS/gpslib/*.py", "src/gpslib"),
  ("../Doc/pygpslog/README.wiki", "doc/README"),
]
references = [ # a few reminders
  (r"Z:\epoc32\winscw\c\python\gpslog\gpslog.py", r"src\gpslog.py"),
  (r"Z:\epoc32\winscw\c\python\gpslog\gpslib\gpssim.py", r"E:\Develop\Python\Proj\GPS\gpslib\gpssim.py"),
  (r"Z:\epoc32\winscw\c\python\gpslog\gpslib\gpsloc.py", r"E:\Develop\Python\Proj\GPS\gpslib\gpsloc.py"),
  (r"Z:\epoc32\winscw\c\python\gpslog\gpslib\gpsnmea.py", r"E:\Develop\Python\Proj\GPS\gpslib\gpsnmea.py"),
  (r"Z:\epoc32\winscw\c\python\gpslog\gpslib\gpspos.py", r"E:\Develop\Python\Proj\GPS\gpslib\gpspos.py"),
  (r"Z:\epoc32\winscw\c\python\gpslog\gpslib\gpsstream.py", r"E:\Develop\Python\Proj\GPS\gpslib\gpsstream.py"),
  (r"Z:\epoc32\winscw\c\python\gpslog\gpslib\gpsbase.py", r"E:\Develop\Python\Proj\GPS\gpslib\gpsbase.py"),
]
unneeded  =  [ "gpslib/SIRF.py", "gpslib/gpssirf.py", "gpslib/gpssim.py", "gpslib/xmldata.py" ]

setup_opts = {
  "caps":    caps,
  "scaps":   scaps,                     # signed caps
  "uid":     SYMBIAN_UID,               # open uid
  "suid":    findUid(appname, srcdir),  # signed uid
  "version": findVersion(appname, srcdir),
  "copy":    copy,
  "text":    "src/disclaimer.txt",
  "cert":    sys.argv[1], "key":   sys.argv[2], "pwd":   sys.argv[3],
  "icon":    "icons\%s.svg" % appname,
  "src" :    None, # don't build sis with python sources
  "ignore":  unneeded,
# "bin":  None,
# "drive": "C",  # sorry!
# "keep":  True,
# "slf": None, "uns": None,
}
merges = [ r"E:\Develop\Python\Proj\S60\Carbide\modules\LocationRequestor\sis\LocationReq_3rd.sisx",
           r"E:\Develop\Python\Proj\S60\Carbide\modules\Landmarks\sis\Landmarks_3rd.sisx" ]
mergeu = [ m.replace(".sisx", "_unsigned.sis") for m in merges ]

for src, dst in references:
  rc = os.system('diff "%s" "%s" > nul:' % (src, dst))
  if rc != 0:
    rc = os.system('diff "%s" "%s"' % (src, dst))
    print "WARNING: %s and %s differ" % (src, dst)
  
for src, dst in setup_opts["copy"]: os.chmod(dst, stat.S_IWRITE|stat.S_IREAD)

sisfiles = setup(appname, srcdir, **setup_opts)

mergesis(sisfiles["Signed - Binary"],   merges, sisfiles["Signed - Binary"].replace(".sis","-bundled.sis"), **setup_opts)
# Embedded sis files don't get signed :-(
# mergesis(sisfiles["Unsigned - Binary"], mergeu, sisfiles["Unsigned - Binary"].replace(".sis","-bundled.sis"))

for src, dst in setup_opts["copy"]: os.chmod(dst, stat.S_IREAD)
