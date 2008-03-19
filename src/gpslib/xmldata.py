from   __future__ import generators

import sys, os, time, re
import gpslib.gpsbase

# we need cElementTree, everything else will kill a smartphone :-)
import cElementTree as ET, elementtree.ElementTree as _ET

if not sys.platform.startswith("symbian"): from   calendar import timegm
else:                                      timegm = time.mktime

GPX11_NS   = "http://www.topografix.com/GPX/1/1"
GPSLOG_NS  = "http://pygpslog.googlecode.com"
KML21_NS   = "http://earth.google.com/kml/2.1"
KML22_NS   = "http://earth.google.com/kml/2.2"

IS_DST           = (time.localtime().tm_isdst == 1)
  

if not sys.platform.startswith("symbian"):
  def isoparse(iso):
    return float(timegm(time.strptime(iso+"UTC", "%Y-%m-%dT%H:%M:%SZ%Z")))
else:
  def isoparse(iso):
    dt, tm = iso[:-1].split("T")
    tm = timegm(tuple([ int(i) for i in dt.split("-") + tm.split(":") + [0,0,0] ]))
    if not IS_DST: tm -= time.timezone
    else:          tm -= time.altzone
    return tm

def isoformat(ts):
  return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))
    
def babelExtract(text, patt):
  m = patt.search(text)
  if m: return float(m.group(1))
  return None

class XMLData(object):
  GPX_MAP = {
    "root":   "gpx",
    "record": "trkpt",
    "lat":    "@lat",
    "lon":    "@lon",
    "alt":    ("ele", float), # for example
    "hdg":    "extensions/{%s}hdg"%GPSLOG_NS,
    "speed":  "extensions/{%s}speed"%GPSLOG_NS,
    "hacc":   "extensions/{%s}hacc"%GPSLOG_NS,
    "vacc":   "extensions/{%s}vacc"%GPSLOG_NS,
    "hdop":   "hdop",
    "vdop":   "vdop",
    "pdop":   "pdop",
    "satmap": {
      "record":    "extensions/{%s}sat"%GPSLOG_NS,
      "prn":       ("@prn", int),
      "azimuth":   "@az",
      "elevation": "@ele",
      "signal":    ("@signal", int),
      "used":      ("@used", lambda u: u == "true"),
    },
    "time":    ("time", isoparse),
    "sattime": ("time", isoparse),
    "namespaces": GPX11_NS
  }
  BABELKML_MAP = {
    "root":   "kml",
    "record": "Placemark",
    "lat":    ("Point/coordinates", lambda c: float(c.split(",")[1])),
    "lon":    ("Point/coordinates", lambda c: float(c.split(",")[0])),
    "alt":    ("Point/coordinates", lambda c: float(c.split(",")[2])),
    "hdg":    ("description", lambda d: babelExtract(d, re.compile(r"Heading:\s*([0-9.]*)\s"))),
    "speed":  ("description", lambda d: babelExtract(d, re.compile(r"Speed:\s*([0-9.]*)\s"))),
    "hacc":   None,
    "vacc":   None,
    "hdop":   None,
    "vdop":   None,
    "pdop":   None,
    "satmap": None,
    "time":    ("TimeStamp/when", isoparse),
    "sattime": ("TimeStamp/when", isoparse),
    "namespaces": [ KML21_NS, KML22_NS ]
  }
  MAPS    = { "gpx": GPX_MAP, "kml": BABELKML_MAP }

  def __init__(self, fname, map=None):
    # self.xml = ET.parse(fname).getroot()
    self.inp = file(fname, "r")
    self.ext = os.path.splitext(fname)[1][1:]
    if map != None: self.map = map
    else: self.map = ( self.ext in XMLData.MAPS and XMLData.MAPS[self.ext]) or XMLData.GPX_MAP
    if type(self.map["namespaces"]) not in [list, tuple]:
      self.map["namespaces"] = [ self.map["namespaces"] ]
    # self.__killNs()
    # self.records = self.xml.findall(self.map["record"])
    self.context = None
    self.recIter = self.getiterator(self.map["record"])
    self.rec     = None
    self.reset()
    
  def __del__(self):
    self.close()
    
  def __killNs(self, elt=None):
    if elt == None: elt = self.rec
    for e in [elt] + elt.findall(".//*"):
      for ns in self.map["namespaces"]:
        e.tag = e.tag.replace("{"+ns+"}", "")
    
  def close(self):
    if self.rec:
      del self.rec;     self.rec     = None
    if self.inp:
      self.inp.close()
      del self.inp;     self.inp     = None
    if self.recIter:
      try: self.recIter.next()
      except: pass
      del self.recIter; self.recIter = None
    if self.context:
      del self.context; self.context = None

  def reset(self):
    self.sat     = None
    self.cache   = {}
    self._nsat   = 0
    self._vsat   = 0
    
  def getiterator(self, tag=None):
    rootTag       = self.map["root"]
    self.context  = iter(ET.iterparse(self.inp, events=("start", "end")))
    evt, root     = self.context.next()
    
    for evt, elt in self.context:
      self.__killNs(elt)
      if (tag == None or elt.tag == tag) and evt == "end":
        yield elt
        elt.clear()
        root.clear()
    del root
    self.close()

  def next(self):
    if not self.recIter:
      return False
    try:
      del self.cache
      self.reset()
      self.rec = self.recIter.next()
      return True
    except StopIteration:
      del self.recIter; self.recIter = None
      return False

  def getSatdata(self):
    if self.sat != None:
      return self.sat
    satmap = self.map["satmap"]
    self.sat = []
    self._nsat = self._vsat = 0
    if satmap != None:
      xmlsat = self.rec.findall(satmap["record"])
      for sat in xmlsat:
        raw = [ self.getmapped(n, sat, satmap, "sat:%d:" % self._vsat)
                for n in "prn", "azimuth", "elevation", "signal", "used"]
        if raw[-1]: self._nsat += 1
        self.sat   += [ gpslib.gpsbase.Satellite(tuple(raw)) ]
        self._vsat += 1

    return self.sat
  
  def getNSat(self):
    if self.sat == None: self.getSatdata()
    return self._nsat
    
  def getVSat(self):
    if self.sat == None: self.getSatdata()
    return self._vsat
    
  nsat    = property(getNSat)
  vsat    = property(getVSat)
  satdata = property(getSatdata)
  
  def __getattr__(self, name):
    return self.getmapped(name)
    
  def getmapped(self, name, rec=None, map=None, pfx=""):
    if pfx+name in self.cache:
      return self.cache[pfx+name]

    if rec == None: rec = self.rec
    if map == None: map = self.map
    
    if not name in map:
      raise AttributeError, "'%s' has no attribute '%s'" % (self.ext, pfx+name)

    if self.rec == None:
      return None

    path, cast = map[name],  float
    if path == None:
      return None

    if type(path) == tuple: path, cast = path
    path = path.split('@',1)
    if len(path) > 1: path, attr = path
    else:             path, attr = path[0], None

    if attr != None and path != '':
      rec = rec.find(path)
    
    if attr != None:
      val = rec.get(attr)
    else:
      val = rec.findtext(path)
    # print "\n", rec, path, attr, val
    if val == None:
      self.cache[pfx+name] = None
      return None
    try:
      self.cache[pfx+name] = val = cast(val)
      return val
    except:
      print "cannot cast", `val`, "in", name
      raise
