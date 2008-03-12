# for the S60 LocationRequetor module
# see http://gagravarr.org/code/#nmea_info
# and http://discussion.forum.nokia.com/forum/showthread.php?t=108657

import gpslib.gpsbase
import locationrequestor #@UnresolvedImport
import time, e32         #@UnresolvedImport @UnusedImport

class LocData(tuple):
  NAMES = ["full",  "lat",    "lon", "alt",    "hacc", "vacc", "module", "time",
           "speed", "spdacc", "hdg", "hdgacc", "sattime", "vsat", "nsat" ]

  def __init__(self, data):
    self = data

  def __getattr__(self, name):
    if not name in LocData.NAMES:
      raise AttributeError, "%s instance has no attribute '%s'" %\
                            (self.__class__.__name__, name)
    idx = LocData.NAMES.index(name)
    if idx >= len(self):
      return None
    else:
      if name == "lat" and isinstance(self[idx], (str, unicode)): return None
      if str(self[idx]) == "NaN":  return None
      return self[idx]
    
class LocationRequestorProvider(gpslib.gpsbase.AbstractProvider):
  "S60 Location"
  name  = __doc__
  Super = gpslib.gpsbase.AbstractProvider
  
  HACCURACY_BASE   = 3.5 # 1.25
  VACCURACY_BASE   = 6.0  # 2.2

  # Interface implementation
  position  =  property(lambda self: (self.data.lat, self.data.lon))
  alt       =  property(lambda self: self.data.alt)
  speed     =  property(lambda self: self.data.speed)
  hdg       =  property(lambda self: self.data.hdg)
  time      =  property(lambda self: (self.sattime != None and self.sattime) or\
                                     ((self.data.time != None and (self.data.time/1000.0)) or None))
  localtime =  property(lambda self: time.localtime(self.time))
  gmtime    =  property(lambda self: time.gmtime(self.time))
  fix       =  None
  quality   =  None
  hdop      =  property(lambda self: (self.data.hacc != None and self.data.hacc / self.VACCURACY_BASE) or None)
  vdop      =  property(lambda self: (self.data.vacc != None and self.data.vacc / self.VACCURACY_BASE) or None)
  pdop      =  None # property(lambda self: self.data.pdop)
  hacc      =  property(lambda self: self.data.hacc)
  vacc      =  property(lambda self: self.data.vacc)
  nsat      =  property(lambda self: self.data.nsat)
  vsat      =  property(lambda self: self.data.vsat)
  sat       =  property(lambda self: self.satdata)
  vspeed    =  0.0
  
  # extensions
  sattime   =  property(lambda self: (self.data.sattime != None and self.data.sattime/1000.0) or None)
  
  satdata   = []
  
  def __init__(self, id=None, interval=1, timeout=60):
    gpslib.gpsbase.AbstractProvider.__init__(self)
    
    self.interval = interval
    self.timeout  = timeout
    self.data     = LocData(())
    self.open(id)

  def __del__(self):
    if self.ok:
      self.close()
      
  def open(self, id=None):
    self.lr = locationrequestor.LocationRequestor()
    if id == None:
      id = self.lr.GetDefaultModuleId()
    self.id       = id
    self.info = self.lr.GetModuleInfoById(self.id)
    self.name = self.name + " using " + self.info[1]
    
    try:
      self.lr.SetUpdateOptions(self.interval, self.timeout, 0, 1)
      self.lr.Open(self.id)

      self.lr.InstallPositionCallback(e32.ao_callgate(self.__callback))
      self.ok = True
    except Exception, exc:
      self.lastError = str(exc)
      self.lr.Close()
      del self.lr
      self.lr = None

  def close(self):
    if self.ok:
      self.lr.Close()
      self.ok = False
      del self.lr; self.lr = None

  def __callback(self, data):
    if len(data) == 2:
      self.lastError = "%d: %s)" % data
    self.data = LocData(data)
    try:
      self.satdata = [ self.lr.GetSatelliteData(i) for i in range(self.data.vsat) ]
      self.satdata = [ gpslib.gpsbase.Satellite(s) for s in self.satdata if s != None ]
    except: self.satdata = []
    self.notifyCallbacks()
    
  def dataAvailable(self):
    return len(self.data) != 0 and self.data.time != None
    
  def modules():
    lr = locationrequestor.LocationRequestor()
    mods = [lr.GetModuleInfoByIndex(i) for i in range(lr.GetNumModules())]
    del lr
    return mods

  modules = staticmethod(modules)

