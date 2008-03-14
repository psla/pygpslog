import sys, traceback

if not sys.platform.startswith("symbian"):
  callgate = lambda f: f
else:
  import e32 #@UnresolvedImport
  callgate = e32.ao_callgate


class Satellite(tuple):
  def __init__(self, t):
    self = t

  def __str__(self):
    return "<Sat%02d:%s(%03d,%02d,%02d)>" %\
      (self.prn, (self.used and "a") or "i", self.azimuth, self.elevation, self.signal)

  def __repr__(self):
    return str(self)

  prn       = property(lambda self: self[0])
  azimuth   = property(lambda self: self[1])
  elevation = property(lambda self: self[2])
  signal    = property(lambda self: self[3])
  used      = property(lambda self: self[4])
  
  
class AbstractProvider(object):
  "Abstract GPS Class"
  name = __doc__

  # This is an abstract class, allmost all of it's interface must be implemented
  def __abstract(self):
    raise NotImplementedError
    
  # Interface

  position = property(lambda self: self.getPosition())
  lat      = property(lambda self: self.position[0])
  lon      = property(lambda self: self.position[1])
  alt      = property(__abstract)
  speed    = property(__abstract)
  vspeed   = property(__abstract)
  hdg      = property(__abstract)
  time     = property(__abstract)
  gmtime   = property(__abstract)
  localtime= property(__abstract)
  
  fix      = property(__abstract) # 1: no, 2: 2D, 3: 3D
  quality  = property(__abstract) # see http://www.gpsinformation.org/dale/nmea.htm#GGA

  vdop     = property(__abstract)
  hdop     = property(__abstract)
  pdop     = property(__abstract)
  hacc     = property(__abstract)
  vacc     = property(__abstract)
  
  nsat     = property(__abstract)
  vsat     = property(__abstract)
  sat      = property(__abstract)

  # aliases
  altitude = property(lambda self: self.alt)
  heading  = property(lambda self: self.hdg)
  track    = property(lambda self: self.hdg)
  
  ok       = False
  lastError= None

  def __init__(self):
    self.callbacks = []
    
  def __del__(self):
    while self.callbacks != []:
      del self.callbacks[0]
    del self.callbacks

  def new(cls, *args, **kwargs):
    return cls(*args, **kwargs)
  new = classmethod(new)

  def close(self):
    pass

  def getPosition(self):
    raise NotImplementedError

  def registerCallback(self, callback):
    cg = callgate(callback)
    self.callbacks.append(cg)
    return cg
    
  def notifyCallbacks(self):
    for cb in self.callbacks:
      try:
        cb(self)
      except:
        traceback.print_exc() # TODO callback error handling
        pass 

