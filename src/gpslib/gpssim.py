# for the S60 LocationRequetor module
# see http://gagravarr.org/code/#nmea_info
# and http://discussion.forum.nokia.com/forum/showthread.php?t=108657
import sys, os, glob, time

import gpslib.gpsbase
import gpslib.gpsstream
    
from xmldata import XMLData, isoformat #@UnresolvedImport

sleep = gpslib.gpsstream.sleep

class XMLSimulator(gpslib.gpsbase.AbstractProvider, gpslib.gpsstream.AbstractStreamProvider):
  "XML Simulator"
  name  = __doc__
  Super = gpslib.gpsbase.AbstractProvider
  
  HACCURACY_BASE   = 3.5 # 1.25
  VACCURACY_BASE   = 6.0  # 2.2

  # Interface implementation
  position  =  property(lambda self: (self.data.lat, self.data.lon))
  alt       =  property(lambda self: self.data.alt)
  speed     =  property(lambda self: self.data.speed)
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

    if type(sources) not in [list, tuple]: sources = [ sources ]
    
    for patt in sources:
      self.sources  += glob.glob(patt)

    assert len(self.sources) > 0, "No input files found"
    
    self.tpl = os.path.join(os.path.dirname(self.sources[0]), "template.kml")
    if os.path.isfile(self.tpl):
      f = file(self.tpl, "r")
      self.kml = f.read()
      f.close()
    else:
      self.kml = None

    self.settings = {}
    cfg = os.path.join(os.path.dirname(self.sources[0]), "XMLSimulator.cfg")
    if os.path.isfile(cfg):
      f = file(cfg, "r"); cfg = f.read(); f.close()
      try:    self.settings = eval(cfg)
      except: pass

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
    return self.data.rec != None
    
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

  def next(self):
    if not self.data.next():
      self.current += 1
      if self.current >= len(self.sources): self.current = 0
      del self.data
      self.data = XMLData(self.sources[self.current], map=self.map)
      self.data.next()
      self.name = os.path.basename(self.sources[self.current])
    self.count += 1
    
  def makeKml(self):
    if not self.kml or not self.dataAvailable():
      return
    kml = self.kml % dict([(n, getattr(self, n, None)) for n in dir(self) if n[0] != '_'  and not callable(getattr(self, n, None))])
    try:
      f = file(os.path.join(os.path.dirname(self.tpl), "XMLSimulator.kml"), "w")
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
    
  def close(self):
    gpslib.gpsstream.AbstractStreamProvider.close(self)
    gpslib.gpsbase.AbstractProvider.close(self)
    if self.data:
      del self.data

    
