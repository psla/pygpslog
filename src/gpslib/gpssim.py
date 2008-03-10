# for the S60 LocationRequetor module
# see http://gagravarr.org/code/#nmea_info
# and http://discussion.forum.nokia.com/forum/showthread.php?t=108657
import sys, os, glob, time

import gpslib.gpsbase
import gpslib.gpsstream
    
from xmldata import XMLData, isoformat #@UnresolvedImport

sleep = gpslib.gpsstream.sleep

KML_TPL = "template.kml"
KML_OUT = "XMLSimulator.kml"

# Copied from gpslogutil.py !!!!
from math import *

def Deg2Rad(x):
    return x * (pi/180.0)
def Rad2Deg(x):
    return x * 180.0 / pi
def CalcRad(lat):
    a = 6378.137
    e2 = 0.081082 * 0.081082
    sc = sin(lat)
    x = a * (1.0 - e2)
    z = 1.0 - e2 * sc * sc
    y = pow(z, 1.5)
    r = x / y
    r = r * 1000.0	# Convert to meters
    return r
def distance((lat1, lon1), (lat2, lon2)):
    if (lat1, lon1) == (lat2, lon2): return 0.0
    lat1, lon1, lat2, lon2 = [ Deg2Rad(a) for a in [lat1, lon1, lat2, lon2]]
    r1, r2 = CalcRad(lat1), CalcRad(lat2)
    pi2 = pi/2
    x1 = r1 * cos(lon1) * sin(pi2-lat1)
    x2 = r2 * cos(lon2) * sin(pi2-lat2)
    y1 = r1 * sin(lon1) * sin(pi2-lat1)
    y2 = r2 * sin(lon2) * sin(pi2-lat2)
    z1 = r1 * cos(pi2-lat1)
    z2 = r2 * cos(pi2-lat2)
    a = (x1*x2 + y1*y2 + z1*z2)/pow(CalcRad((lat1+lat2)/2),2)
    if abs(a) > 1: a = 1
    elif a < -1: a = -1
    return CalcRad((lat1+lat2) / 2) * acos(a)

class XMLSimulator(gpslib.gpsbase.AbstractProvider, gpslib.gpsstream.AbstractStreamProvider):
  "XML Simulator"
  name  = __doc__
  Super = gpslib.gpsbase.AbstractProvider
  
  HACCURACY_BASE   = 3.5 # 1.25
  VACCURACY_BASE   = 6.0  # 2.2
  
  # Interface implementation
  position  =  property(lambda self: (self.data.lat, self.data.lon))
  alt       =  property(lambda self: self.data.alt)
  speed     =  None # will be set later
  hdg       =  property(lambda self: self.data.hdg)
  time      =  property(lambda self: self.sattime) # see below
  localtime =  property(lambda self: time.localtime(self.time))
  gmtime    =  property(lambda self: time.gmtime(self.time))
  fix       =  None
  quality   =  None
  hdop      =  property(lambda self: self.data.hdop)
  vdop      =  property(lambda self: self.data.vdop)
  pdop      =  property(lambda self: self.data.pdop)
  hacc      =  property(lambda self: self.data.hacc)
  vacc      =  property(lambda self: self.data.vacc)
  nsat      =  property(lambda self: self.data.nsat)
  vsat      =  property(lambda self: self.data.vsat)
  sat       =  property(lambda self: self.data.satdata)
  vspeed    =  0.0
  
  # extensions
  # sattime =  property(gettime) # see below
  isotime   =  property(lambda self: isoformat(self.time))
  gpsspeed  =  None

  def __init__(self, interval=-1, sources=["*.gpx"], xmlmap=None, skip=None):
    self.sources  = []
    self.interval = interval
    self.data     = None
    self.current  = 0
    self.map      = None
    self.count    = 0
    self.skip     = skip
    self.ptime    = None
    self.name    += " - Reading..."
    self.prev     = None

    if type(sources) not in [list, tuple]: sources = [ sources ]
    
    for patt in sources:
      self.sources  += [ fn for fn in glob.glob(patt) if not os.path.basename(fn).lower() in [ KML_OUT.lower(), KML_TPL.lower()] ]

    assert len(self.sources) > 0, "No input files found"
    
    self.tpl = os.path.join(os.path.dirname(self.sources[0]), KML_TPL)
    if os.path.isfile(self.tpl):
      f = file(self.tpl, "r")
      self.kml = f.read()
      f.close()
    else:
      self.kml = None

    self.settings = {}
    cfg = os.path.join(os.path.dirname(self.sources[0]), "XMLSimulator.cfg")
    if os.path.isfile(cfg):
      f = file(cfg, "r")
      cfg = " ".join([l.strip() for l in f if l.strip()[0] != '#'])
      f.close()
      if not cfg[0] == "{": cfg = "{%s}" % cfg
      try:    self.settings = eval(cfg)
      except: print cfg; raise

    if self.skip == None and "skip" in self.settings:
      self.skip = self.settings["skip"]
    else:
      self.skip = skip

    if "interval" in self.settings: self.interval = self.settings["interval"]

    gpslib.gpsbase.AbstractProvider.__init__(self)
    gpslib.gpsstream.AbstractStreamProvider.__init__(self)

  def gettime(self):
    if "hosttime" in self.settings and self.settings["hosttime"]:
      return time.time()
    if self.data.time != None: tm = self.data.time
    else:                      tm = time.time()
    if self.interval < 0 and self.ptime: # add realtime difference
      tm += time.time() - self.ptime[1]
    return tm

  sattime  =  property(gettime) # see below
                                     
  def dataAvailable(self):
    return self.data and self.data.rec != None
    
  def process(self):
    upd = self.wait()
    if upd:
      self.next()
    if self.dataAvailable():
      self.notifyCallbacks()
      self.makeKml()
    return True

  def wait(self):
    if self.interval >= 0 or not self.dataAvailable() or self.data.time == None: # not realtime
      sleep(abs(self.interval))
      return True
    if self.ptime == None:
      self.ptime = (self.data.time, time.time())
    prev, cpu = self.ptime
    satdiff = self.data.time - prev
    cpudiff = time.time() - cpu
    if satdiff > cpudiff:
      sleep(min(abs(self.interval), satdiff-cpudiff))
    satdiff = self.data.time - prev
    cpudiff = time.time() - cpu
    if satdiff <= cpudiff:
      self.ptime = (self.data.time, time.time())
      return True
    return False

  def setSpeed(self):
    self.gpsspeed = self.data.speed
    if "calcspeed" not in self.settings or not self.settings["calcspeed"]:
      self.speed = self.data.speed; return
    if self.prev == None or self.prev[0] == (None,None): return None
    dt = self.time - self.prev[1]
    if dt <= 0: self.speed = None; return
    self.speed = round(3.6 * distance(self.position, self.prev[0]) / dt, 2)

  def next(self):
    self.prev = (self.position, self.time) # xml data gets cleared for memory efficiency!
    if not self.data.next():
      self.current += 1
      if self.current >= len(self.sources): self.current = 0
      deldata, self.data = self.data, None; del deldata
      self.data = XMLData(self.sources[self.current], map=self.map)
      self.data.next()
    self.count += 1
    self.name = "%s - %d" % (os.path.basename(self.sources[self.current]), self.count)
    self.setSpeed()

  def makeKml(self):
    if not self.kml or not self.dataAvailable():
      return
    kml = self.kml % dict([(n, getattr(self, n, None)) for n in dir(self) if n[0] != '_'  and not callable(getattr(self, n, None))])
    try:
      f = file(os.path.join(os.path.dirname(self.tpl), KML_OUT), "w")
      f.write(kml)
      f.close()
    except:
      pass

  def threadInit(self):
    self.data = XMLData(self.sources[self.current], self.map)
    
    while self.count < self.skip:
      self.next()

    self.name = os.path.basename(self.sources[self.current])

    gpslib.gpsstream.AbstractStreamProvider.threadInit(self)

  def threadExit(self):
    gpslib.gpsstream.AbstractStreamProvider.threadExit(self)
    if self.data:
      del self.data
    
  def close(self):
    gpslib.gpsstream.AbstractStreamProvider.close(self)
    gpslib.gpsbase.AbstractProvider.close(self)

    
