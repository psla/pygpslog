import sys, NMEA
import gpslib.gpsstream
import gpslib.gpsbase

if not sys.platform.startswith("symbian"):
  import time
  sleep    =  time.sleep
  callgate = lambda f: f
else:
  import e32 #@UnresolvedImport
  sleep    = e32.ao_sleep
  callgate = e32.ao_callgate


KNOTS_TO_KPH     = 1.852
CALLBACK_TRIGGER = "$GPRMC"

class AbstractNMEAProvider(gpslib.gpsbase.AbstractProvider):
  "Abstract NMEA GPS"
  name  = __doc__
  Super = gpslib.gpsbase.AbstractProvider
  
  HACCURACY_BASE = 8.0
  VACCURACY_BASE = 12.0

  # Interface implementation
  alt       =  property(lambda self: self.nmea.altitude)
  speed     =  property(lambda self: self.nmea.speed * KNOTS_TO_KPH)
  hdg       =  property(lambda self: self.nmea.track)
  time      =  property(lambda self: self.nmea.time)
  localtime =  property(lambda self: self.nmea.localtime)
  gmtime    =  property(lambda self: self.nmea.gmtime)
  fix       =  property(lambda self: self.nmea.mode)
  quality   =  property(lambda self: self.nmea.status)
  hdop      =  property(lambda self: self.nmea.hdop)
  vdop      =  property(lambda self: self.nmea.vdop)
  pdop      =  property(lambda self: self.nmea.pdop)
  hacc      =  property(lambda self: (self.nmea.hdop != None and self.nmea.hdop * self.HACCURACY_BASE) or None)
  vacc      =  property(lambda self: (self.nmea.vdop != None and self.nmea.vdop * self.VACCURACY_BASE) or None)
  nsat      =  property(lambda self: self.nmea.satellites)
  vsat      =  property(lambda self: self.nmea.in_view)
  sat       =  property(lambda self: self.getSatellites())

  vspeed    =  0.0

  def __init__(self):
    self.exc     = None
    self.nmea    = NMEA.NMEA()
    
    gpslib.gpsbase.AbstractProvider.__init__(self)
    

  def __del__(self):
    gpslib.gpsbase.AbstractProvider.__del__(self)
    del self.nmea

  def readline(self):
    line = None
    while 1:
      char = self.read(1)
      if not char: break
      if line == None: line = ""
      line += char
      if char == "\n": break
    return line.replace("\r\n", "\n")

  def process(self):
    try:
      line = self.readline()
      if line == None:
        return False
      
      err = self.nmea.handle_line(line)

      if err:
        self.lastError = err
      
      if line.startswith(CALLBACK_TRIGGER) and self.dataAvailable():
        self.notifyCallbacks()

    except EOFError:
      return False
    except Exception, exc:
      self.lastError = str(exc)
      self.ok = False
      self.notifyCallbacks()
      return False
    return True
    
  def dataAvailable(self):
    return self.nmea.in_view != 0
    # return (self.nmea.lat, self.nmea.lon) != (0.0, 0.0) # highly unlikely to sail african equatorial waters
    
  def threadInit(self):
    pass

  def checkStatus(self):
    if not self.ok:
      raise SystemError, "GPS acquisition terminated unexpectedly"
    if not self.dataAvailable: 
      raise SystemError, "Position not acquired"
      
  def getPosition(self):
    self.checkStatus()
    return (self.nmea.lat, self.nmea.lon)

  def getSatellites(self):
    sat = zip(self.nmea.prn, self.nmea.azimuth, self.nmea.elevation, self.nmea.ss, [(s in self.nmea.in_use) for s in self.nmea.prn])
    return [ gpslib.gpsbase.Satellite(s) for s in sat if s[0] != 0]

class NMEASerialProvider(AbstractNMEAProvider, gpslib.gpsstream.AbstractStreamProvider):
  "Generic NMEA GPS over Serial port"
  name = __doc__

  DEFAULT_PORT = "COM6"
  
  def __init__(self, serial=DEFAULT_PORT, speed=57600, timeout=5):
    self.serport    = serial
    self.serspeed   = speed
    self.sertimeout = timeout
    gpslib.gpsstream.AbstractStreamProvider.__init__(self)
    AbstractNMEAProvider.__init__(self)
    
  def threadInit(self):
    import serial #@UnresolvedImport
    if type(self.serport) in [str, unicode] and self.serport.lower().startswith("com"):
      self.serport = int(self.serport[3:].strip(":"))-1
    self.stream = serial.Serial(self.serport, self.serspeed, self.sertimeout)
    _skip = self.readline()
    gpslib.gpsstream.AbstractStreamProvider.threadInit(self)
    AbstractNMEAProvider.threadInit(self)

  def close(self):
    AbstractNMEAProvider.close(self)
    gpslib.gpsstream.AbstractStreamProvider.close(self)
    
class NMEAGPSDProvider(AbstractNMEAProvider, gpslib.gpsstream.AbstractGPSDProvider):
  "NMEA GPS using gpsd server"
  name = __doc__

  def __init__(self, addr=gpslib.gpsstream.GPSD_DEFAULT, init=gpslib.gpsstream.GPSD_INIT_NMEA):
    AbstractNMEAProvider.__init__(self)
    gpslib.gpsstream.AbstractGPSDProvider.__init__(self, addr=addr, init=init)

  def threadInit(self):
    gpslib.gpsstream.AbstractGPSDProvider.threadInit(self)
    AbstractNMEAProvider.threadInit(self)
    
  def close(self):
    AbstractNMEAProvider.close(self)
    gpslib.gpsstream.AbstractGPSDProvider.close(self)
    
class NMEABluetoothProvider(AbstractNMEAProvider, gpslib.gpsstream.AbstractBluetoothProvider):
  "NMEA GPS over Bluetooth sockets"
  name = __doc__

  def __init__(self, addr=None):
    AbstractNMEAProvider.__init__(self)
    gpslib.gpsstream.AbstractBluetoothProvider.__init__(self, addr=addr)

  def threadInit(self):
    gpslib.gpsstream.AbstractBluetoothProvider.threadInit(self)
    AbstractNMEAProvider.threadInit(self)
    
  def close(self):
    AbstractNMEAProvider.close(self)
    gpslib.gpsstream.AbstractBluetoothProvider.close(self)
    
