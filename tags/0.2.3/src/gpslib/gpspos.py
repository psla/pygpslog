import gpslib.gpsbase
import positioning
import time

# HACK ALERT: undocumented, but otherwise bluetooth stays open!
# we'll set it later, in open()
try:    del positioning._positioner
except: pass

class PositioningProvider(gpslib.gpsbase.AbstractProvider):
  "S60 Positioning"
  name  = __doc__
  Super = gpslib.gpsbase.AbstractProvider

  HACCURACY_BASE   = 3.5 # 1.25
  VACCURACY_BASE   = 6.0  # 2.2
  
  IS_DST           = (time.localtime().tm_isdst == 1)

  # Interface implementation
  position  =  property(lambda self: (self.posdata("position", "latitude"), self.posdata("position", "longitude")))
  alt       =  property(lambda self: self.posdata("position", "altitude"))
  speed     =  property(lambda self: self.posdata("course", "speed"))
  hdg       =  property(lambda self: self.posdata("course", "heading"))
  time      =  property(lambda self: self.posdata("satellites", "time"))
  localtime =  property(lambda self: time.localtime(self.time))
  gmtime    =  property(lambda self: time.gmtime(self.time))
  fix       =  None
  quality   =  None
  hdop      =  property(lambda self: (self.hacc != None and self.hacc / self.VACCURACY_BASE) or None)
  vdop      =  property(lambda self: (self.vacc != None and self.vacc / self.VACCURACY_BASE) or None)
  pdop      =  None # property(lambda self: self.data.pdop)
  hacc      =  property(lambda self: self.posdata("position", "horizontal_accuracy"))
  vacc      =  property(lambda self: self.posdata("position", "vertical_accuracy"))
  nsat      =  property(lambda self: self.posdata("satellites", "used_satellites"))
  vsat      =  property(lambda self: self.posdata("satellites", "satellites"))
  sat       =  None
  vspeed    =  0.0

  def __init__(self, id=None, interval=1, timeout=60):
    gpslib.gpsbase.AbstractProvider.__init__(self)
    self.interval = interval
    self.timeout  = timeout
    self.data     = {}
    self.open(id)

  def __del__(self):
    if self.ok:
      self.close()
      
  def open(self, id=None):

    self.id       = id

    if id == None:
      id = positioning.default_module()
    self.id       = id
    self.info = positioning.module_info(self.id)
    self.name = PositioningProvider.name + " using " + self.info["name"]
    # HACK ALERT: undocumented, but otherwise bluetooth stays open!
    # positioning.select_module(self.id)
    positioning._positioner=positioning._pos_serv.positioner(self.id)

    positioning.set_requestors([{"type":"service",
                                 "format":"application",
                                 "data":"test_app"}])
    positioning.position(course=True, satellites=True, callback=self.__callback,
                         interval=int(self.interval*1.0E6), partial=True)
    self.ok = True

  def close(self):
    if self.ok:
      positioning.stop_position()
      self.ok = False
      # HACK ALERT: undocumented, but otherwise bluetooth stays open!
      try:    del positioning._positioner
      except: pass

  def __callback(self, data):
    self.data = data
    self.notifyCallbacks()

  def posdata(self, cat, item):
    if not cat in self.data or not item in self.data[cat]:
      return None
    val = self.data[cat][item]
    if str(val) in ["NaN", "Inf", "1.#INF", "-1.#INF", "Infinity", "None"]: return None
    if (cat, item) == ("satellites", "time"):
      if not self.IS_DST: val -= time.timezone
      else:               val -= time.altzone
    if (cat, item) == ("course", "speed"):
      val = val * 3600 / 1000
    return val
      
  def dataAvailable(self):
    return len(self.data) != 0
    
  def modules():
    return positioning.modules()

  modules = staticmethod(modules)
