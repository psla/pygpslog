import gpslib.gpsstream
import gpslib.gpsbase
import gpslib
import sys, SiRF

if not sys.platform.startswith("symbian"):
  import time
  sleep =  time.sleep
else:
  import e32 #@UnresolvedImport
  sleep = e32.ao_sleep

CALLBACK_TRIGGER = "$GPRMC"

class AbstractSiRFProvider(gpslib.gpsbase.AbstractProvider):
  "Abstract SiRF GPS"
  name  = __doc__
  Super = gpslib.gpsbase.AbstractProvider
  
  HACCURACY_BASE   = 1.25
  VACCURACY_BASE   = 2.2
  DEFAULT_SERSPEED = 57600

  # Interface implementation
  alt       =  property(lambda self: self.sirf.alt)
  speed     =  property(lambda self: self.sirf.speed)
  hdg       =  property(lambda self: self.sirf.hdg)
  time      =  property(lambda self: self.sirf.time)
  localtime =  property(lambda self: self.sirf.localtime)
  gmtime    =  property(lambda self: self.sirf.gmtime)
  fix       =  property(lambda self: self.sirf.fix)
  quality   =  property(lambda self: self.sirf.quality)
  hdop      =  property(lambda self: self.sirf.hdop)
  # vdop      =  None # property(lambda self: self.sirf.vdop)
  pdop      =  None # property(lambda self: self.sirf.pdop)
  # hacc      =  property(lambda self: (self.sirf.hdop != None and self.sirf.hdop * self.HACCURACY_BASE) or None)
  # vacc      =  property(lambda self: (self.sirf.vdop != None and self.sirf.vdop * self.VACCURACY_BASE) or None)
  vdop      =  property(lambda self: (self.sirf.vacc != None and self.sirf.vacc / self.VACCURACY_BASE) or None)
  hacc      =  property(lambda self: self.sirf.hacc)
  vacc      =  property(lambda self: self.sirf.vacc)
  nsat      =  property(lambda self: self.sirf.nsat)
  vsat      =  property(lambda self: self.sirf.vsat)
  sat       =  property(lambda self: self.getSatellites())
  vspeed    =  0.0
  
  # SiRF control parameters
  serspeed  = 57600

  def __init__(self, switch=False):
    self.switchNMEA = switch
    gpslib.gpsbase.AbstractProvider.__init__(self)
    self.sirf    = SiRF.SiRF(self)

  def __del__(self):
    gpslib.gpsbase.AbstractProvider.__del__(self)
    del self.sirf

  def close(self):
    gpslib.gpsbase.AbstractProvider.close(self)
    
  def read(self, n=0):
    if not self.stream:
      raise NotImplementedError
    # We have to do this, because in SiRF mode, serial comm seems less stable
    elif isinstance(self, gpslib.gpsstream.AbstractSocketProvider):
      return gpslib.gpsstream.AbstractSocketProvider.read(self, n)
    else:
      retry = 5
      buf = ""
      ni = n
      while len(buf) < ni and retry > 0:
        buf += self.stream.read(n)
        retry -= 1
        n = ni - len(buf)
      return buf

  def process(self):
    try:
      complete = self.sirf.process()
      if complete and self.dataAvailable():
        self.notifyCallbacks()
    except SiRF.ProtocolError, exc:
      self.lastError = str(exc)
    except EOFError:
      return False
    except Exception, exc:
      self.lastError = str(exc)
      return False
    return True

  def dataAvailable(self):
    return (self.sirf.lat, self.sirf.lon) != (0.0, 0.0) # highly unlikely WTF, TODO:
    
  def threadInit(self):
    if self.switchNMEA:
      self.sirf.switchToSiRF(self.serspeed)

  def threadExit(self):
    if self.switchNMEA:
      self.sirf.switchToNMEA(self.serspeed)

  def checkStatus(self):
    if not self.ok:
      raise SystemError, "GPS acquisition terminated unexpectedly"
    if not self.dataAvailable: 
      raise SystemError, "Position not acquired"
      
  def getPosition(self):
    self.checkStatus()
    return (self.sirf.lat, self.sirf.lon)

  def getSatellites(self):
    sat = zip(self.sirf.prn, self.sirf.azimuth, self.sirf.elevation, self.sirf.sigs, [(s in self.sirf.used) for s in self.sirf.prn])
    return [ gpslib.gpsbase.Satellite(s) for s in sat if s[0] != 0]
  
class SiRFSerialProvider(AbstractSiRFProvider, gpslib.gpsstream.AbstractStreamProvider):
  "SiRF GPS over Serial port"
  name = __doc__

  def __init__(self, serial, speed=57600, timeout=5, switch=False):
    self.serport    = serial
    self.serspeed   = speed
    self.sertimeout = timeout
    AbstractSiRFProvider.__init__(self, switch)
    gpslib.gpsstream.AbstractStreamProvider.__init__(self)
  
  def reopen(self):  
    import serial #@UnresolvedImport
    self.stream.close()
    sleep(0.33)
    self.stream = serial.Serial(self.serport, self.serspeed, self.sertimeout)
    sleep(0.33)
    
  def threadInit(self):
    import serial #@UnresolvedImport
    if type(self.serport) in [str, unicode] and self.serport.lower().startswith("com"):
      self.serport = int(self.serport[3:])-1
    self.stream = serial.Serial(self.serport, self.serspeed, self.sertimeout)

    AbstractSiRFProvider.threadInit(self)
    gpslib.gpsstream.AbstractStreamProvider.threadInit(self)

  def threadExit(self):
    AbstractSiRFProvider.threadExit(self)
    gpslib.gpsstream.AbstractStreamProvider.threadExit(self)
    
  def close(self):
    gpslib.gpsstream.AbstractStreamProvider.close(self)
    AbstractSiRFProvider.close(self)
    
class SiRFFileProvider(AbstractSiRFProvider, gpslib.gpsstream.AbstractStreamProvider):
  "SiRF GPS from dump file"
  name  = __doc__
  Super = AbstractSiRFProvider
  
  def __init__(self, filename, delay=0.0):
    self.filename   = filename
    self.delay      = delay
    AbstractSiRFProvider.__init__(self)
    gpslib.gpsstream.AbstractStreamProvider.__init__(self)
    
  def read(self, n=0):
    if self.delay > 0.0: time.sleep(self.delay)
    return AbstractSiRFProvider.read(self, n)

  def write(self, buf):
    raise SystemError, "Writing not supported ;-)"

  def threadInit(self):
    self.stream = file(self.filename, "rb")
    AbstractSiRFProvider.threadInit(self)
    gpslib.gpsstream.AbstractStreamProvider.threadInit(self)

  def threadExit(self):
    AbstractSiRFProvider.threadExit(self)
    gpslib.gpsstream.AbstractStreamProvider.threadExit(self)
    
  def close(self):
    AbstractSiRFProvider.close(self)
    gpslib.gpsstream.AbstractStreamProvider.close(self)
    
class SiRFGPSDProvider(AbstractSiRFProvider, gpslib.gpsstream.AbstractGPSDProvider):
  "SiRF GPS using gpsd server"
  name = __doc__

  def __init__(self, addr=gpslib.gpsstream.GPSD_DEFAULT, switch=False):
    AbstractSiRFProvider.__init__(self, switch=switch)
    gpslib.gpsstream.AbstractGPSDProvider.__init__(self, addr=addr, init=gpslib.gpsstream.GPSD_INIT_RAW)
    
  def threadInit(self):
    gpslib.gpsstream.AbstractGPSDProvider.threadInit(self)
    AbstractSiRFProvider.threadInit(self)
    
  def threadExit(self):
    AbstractSiRFProvider.threadExit(self)
    gpslib.gpsstream.AbstractGPSDProvider.threadExit(self)
    
  def close(self):
    gpslib.gpsstream.AbstractGPSDProvider.close(self)
    AbstractSiRFProvider.close(self)
    
class SiRFBluetoothProvider(AbstractSiRFProvider, gpslib.gpsstream.AbstractBluetoothProvider):
  "SiRF GPS over Bluetooth sockets"
  name = __doc__

  def __init__(self, addr=None, switch=False):
    AbstractSiRFProvider.__init__(self, switch=switch)
    gpslib.gpsstream.AbstractBluetoothProvider.__init__(self, addr=addr)

  def threadInit(self):
    gpslib.gpsstream.AbstractBluetoothProvider.threadInit(self)
    AbstractSiRFProvider.threadInit(self)

  def threadExit(self):
    AbstractSiRFProvider.threadExit(self)
    gpslib.gpsstream.AbstractBluetoothProvider.threadExit(self)
    
  def close(self):
    AbstractSiRFProvider.close(self)
    gpslib.gpsstream.AbstractBluetoothProvider.close(self)
    