import math, time, struct

# from http://janszoon.sourceforge.net/
F  = (1/298.257223563)
A  = 6378137.0
B  = 6356752.31424518
E2 = (A*A-B*B)/(A*A)
ED2= (A*A-B*B)/(B*B)

# from gpsd
GPS_EPOCH      = 315964800    # epoch in Unix time
SECS_PER_WEEK  = (60*60*24*7)
GPS_ROLLOVER   = (1024*SECS_PER_WEEK)

COMPLETE_ID = 2

# Python 2.2 :-(
def summ(l):
  s = 0
  for e in l:
    s += e
  return s

if not hasattr(math, "degrees"):
  math.degrees = lambda x: x / 2.0 / math.pi * 360.0
if not hasattr(math, "radians"):
  math.radians = lambda x: x / 360.0 * 2.0 * math.pi
 
  
class ProtocolError(ValueError):
  pass
  
class SiRF(object):
  MAX_READ = 1024
  
  def __init__(self, stream):
    self.stream = stream
    
    self.lat    = 0.0
    self.lon    = 0.0
    self.alt    = 0.0
    self.speed  = 0.0
    self.hdg    = 0.0
    self.hdop   = None
    self.vdop   = None
    self.hacc   = None
    self.vacc   = None
    self.time      = None
    self.gmtime    = None
    self.localtime = None
    self.prn       = []
    self.azimuth   = []
    self.elevation = []
    self.sigs      = []
    self.used      = []
    self.vsat      = 0
    self.nsat      = 0
    
    self.clockSeen   = False
    self.visibleSeen = False
    self.geoSeen     = False
    self.trackerSeen = False

    self.completeId  = COMPLETE_ID

    self.__seq = 0

    self.__buf = ""

  def __read(self, n):
    if len(self.__buf) >= n:
      ret = self.__buf[:n]
      self.__buf = self.__buf[n:]
      return ret
    else:
      return self.stream.read(n)

  def __putBack(self, packet, chksum, marker):
    self.__buf  = struct.pack(">H", len(packet))
    self.__buf += packet
    self.__buf += struct.pack(">H", chksum)
    self.__buf += marker
    
  def readPacket(self):
    b = 0
    n = 0
    while True:
      while b != '\xA0':
        b = self.__read(1)
        n += 1
        if not b:
          return EOFError, None, 0
        if n >= SiRF.MAX_READ:
          return EOFError, None, 0
      b = self.__read(1)
      n += 1
      if b != '\xA2':
        continue

      addr   = 0
      if hasattr(self.stream, "tell"): addr = self.stream.tell()-2
      
      lgth   = struct.unpack(">H", self.__read(2))[0]
      packet = self.__read(lgth)
      chksum = struct.unpack(">H", self.__read(2))[0]
      marker = self.__read(2)
      
      mysum = 0;
      for c in packet: mysum += ord(c)
      mysum &= 0x7FFF
  
      if marker != '\xB0\xB3':
        self.__putBack(packet, chksum, marker)
        continue
        # return ProtocolError("Invalid Marker, id = %d, seq = %d" % (ord(packet[0]), self.__seq)),\
        #        packet, addr
  
      if chksum != mysum:
        return ProtocolError("Invalid Checksum (%04X != %04X), id = %d, seq = %d" %\
                             (chksum, mysum, ord(packet[0]), self.__seq)),\
               packet, addr
  
      self.__seq += 1
      return None, packet, addr

  def gpstime2time(week, tow):
    if (week >= 1024):
      fixtime = GPS_EPOCH + (week * SECS_PER_WEEK) + tow
    else:
      now = time.time()
      last_rollover = GPS_EPOCH+int((now-GPS_EPOCH)/GPS_ROLLOVER)*GPS_ROLLOVER
      fixtime = last_rollover + (week * SECS_PER_WEEK) + tow
    return fixtime
  # Python 2.2!
  gpstime2time = staticmethod(gpstime2time)

  def ecef2lla(x, y, z):
    p     = math.sqrt(x*x + y*y)
    sigma = math.atan((z*A)/(p*B))
    lon   = math.atan2(y, x)
    if 0:
      lat   = math.atan((z+ED2*p*math.pow(math.sin(sigma),3))/(p-E2*A*pow(math.cos(sigma),3)))
      n     = A/math.sqrt(1.0-E2*math.pow(math.sin(lat), 2))
      h     = p/math.cos(lat) - n
      return (math.degrees(lat), math.degrees(lon), h)
    else:
      h = 0.0
      lat = math.atan(z/(p*(1.0-E2)))
      for i in range(10):
        n   = A/math.sqrt(1.0-E2*math.pow(math.sin(lat), 2))
        h   = p/math.cos(lat)-n
        lat = math.atan(z/(p*(1.0-E2*(n/(n+h)))))
      return (math.degrees(lat), math.degrees(lon), h)
  ecef2lla = staticmethod(ecef2lla)
  
  def ecefv2sh(vx, vy, vz, lat, lon):
    vx, vy, vz = [ float(v) / 8.0 for v in (vx, vy, vz) ]
    lat, lon   = math.radians(lat), math.radians(lon)
    vn = -vx * math.sin(lat) * math.cos(lon) - \
          vy * math.sin(lat) * math.sin(lon) + vz * math.cos(lat)
    ve = -vx * math.sin(lon) + vy * math.cos(lon)
    vd = -vx * math.cos(lat) * math.cos(lon) - \
          vy * math.cos(lat) * math.sin(lon) - vz * math.sin(lat)
    speed = math.sqrt(vn*vn + ve*ve)
    hdg   = math.atan2(ve, vn)
    if hdg < 0.0: hdg += 2 * math.pi
    return (speed * 3.6, math.degrees(hdg), -vd)
  ecefv2sh = staticmethod(ecefv2sh)

  def __makeFixQuality(self, pmode, dgps):
    if dgps:
      self.quality = 2
      self.fix     = 3
    else:
      self.quality = [ 0, 1, 1, 1, 1, 1, 1, 6][pmode]
      if   pmode == 0:     self.fix = 1
      elif pmode in [4,6]: self.fix = 3
      else:                self.fix = 2
    
  def handleNav(self, packet):
    if not self.geoSeen:
      x, y, z = struct.unpack(">3l", packet[:12])
      self.lat, self.lon, self.alt = SiRF.ecef2lla(x, y, z)
      packet = packet[12:]
      x, y, z = struct.unpack(">3h", packet[:6])
      self.speed, self.hdg, self.vspeed = SiRF.ecefv2sh(x, y, z, self.lat, self.lon)
      packet = packet[6:]
      mode1, hdop, mode2 = struct.unpack("3b", packet[:3])
      packet = packet[3:]
      pmode  = mode1 & 0x07
      dgps   = (mode1 & 0x80) != 0
      self.__makeFixQuality(pmode, dgps)
    
      self.hdop = hdop / 5.0
      gpsweek, gpstow, inuse = struct.unpack(">HLB", packet[:7])
      packet = packet[7:]
      if not self.clockSeen:
        self.time = SiRF.gpstime2time(gpsweek, gpstow / 100.0)
        self.localtime = time.localtime(self.time)
        self.gmtime    = time.gmtime(self.time)
      self.nsat = inuse
      
    if not self.trackerSeen and not self.visibleSeen:
      self.prn       = list(struct.unpack("12B", packet[-12:]))
      self.azimuth   = [ 0 ] * len(self.prn)
      self.elevation = [ 0 ] * len(self.prn)
      self.vsat      = len([s for s in self.prn if s != 0])

  def __makeTime(self, yr, mo, dy, h, m, s):
    tzoffs = time.mktime(time.localtime()) - time.mktime(time.gmtime())
    t  = time.struct_time((yr,mo,dy, h, m, 0, 0, 0, -1))
    t  = time.mktime(t) + float(s)
    lt = time.localtime()
    if lt.tm_isdst != 0: tzoffs = -time.altzone 
    t += tzoffs
    self.time      = t
    self.localtime = time.localtime(self.time)
    self.gmtime    = time.gmtime(self.time)

  def handleGeo(self, packet):
    val, type, week, tow    = struct.unpack(">HHHL", packet[:10])
    pmode = type & 0x00000007
    dgps  = (type & 0x00000080) != 0
    self.__makeFixQuality(pmode, dgps)
    packet = packet[10:]
    yr, mo, dy, h, m, s, _satmap  = struct.unpack(">H4BHL", packet[:12])
    packet = packet[12:]
    self.__makeTime(yr, mo, dy, h, m, s / 1000.0)
    self.lat, self.lon  = [c / 1e7 for c in struct.unpack(">2l", packet[0:8])]
    _alt_el,  self.alt  = [a / 1e2 for a in struct.unpack(">2l", packet[8:16])]
    packet = packet[16:]
    _mdtm, speed, hdg, _magvar, vspeed, _hdgrte, hacc, vacc =\
      struct.unpack(">BHHHHHLL", packet[:19])
    packet = packet[19:]
    self.speed  = speed  / 100.0 * 3.6
    self.hdg    = hdg    / 100.0
    self.vspeed = vspeed / 100.0
    self.nsat, hdop = struct.unpack("2B", packet[-3:-1])
    self.hdop = hdop / 5.0
    self.hacc = hacc / 100.0
    self.vacc = vacc / 100.0
    self.geoSeen = True
    self.completeId = 41

  def handleClock(self, packet):
    if self.geoSeen:
      return
    gpsweek, gpstow, inuse = struct.unpack(">HLB", packet[:7])
    # drift, bias, tm = struct.unpack(">3L", packet[7:])
    self.time = SiRF.gpstime2time(gpsweek, gpstow / 100.0)
    self.localtime = time.localtime(self.time)
    self.gmtime    = time.gmtime(self.time)

    self.clockSeen = True

  def handleVisible(self, packet):
    if self.trackerSeen:
      return
    self.vsat = struct.unpack("B", packet[:1])[0]
    packet = packet[1:]
    self.used = []
    if not self.trackerSeen:
      self.prn = []; self.azimuth = []; self.elevation = []
    for i in range(self.vsat):
      id, az, el = struct.unpack(">BHH", packet[:5])
      self.used.append(id)
      if not self.trackerSeen:
        self.prn.append(id)
        self.azimuth.append(az)
        self.elevation.append(el)
      packet = packet[5:]

    self.visibleSeen = True
    
  def handleTracker(self, packet):
    nchan = struct.unpack(">B", packet[6:7])[0]
    packet = packet[7:]

    self.prn = []; self.azimuth = []; self.elevation = []; self.sigs = []
    self.used = []
    self.vsat = 0
    
    for i in range(nchan):
      id, az, el, st = struct.unpack(">3BH", packet[:5])
      packet = packet[5:]
      self.prn.append(id)
      self.azimuth.append(az * 3.0 / 2.0)
      self.elevation.append(el / 2.0)
      if (st & 0x0001 != 0) and (st & 0x0040 == 0):
        self.used.append(id)
      sigs = struct.unpack("10B", packet[:10])
      packet = packet[10:]
      self.sigs.append(summ(sigs)/len(sigs))
      if id != 0:
        self.vsat += 1

    self.trackerSeen = True

  def handleError(self, packet):
    self.lastError = "Error"
    
  def addNMEAChecksum(sentence):
      csum = 0
      for c in sentence:
          csum = csum ^ ord(c)
      return "$" + sentence + "*%02X" % csum + "\r\n"
  addNMEAChecksum = staticmethod(addNMEAChecksum)
  
  def checksum(payload):
    csum = 0
    for c in payload:
        csum += ord(c)
    return struct.pack(">H", csum & 0x7FFF)
  checksum = staticmethod(checksum)
  
  def sirfMessage(payload):
    return ('\xA0\xA2' + struct.pack(">H", len(payload)) + payload +
            SiRF.checksum(payload) + '\xB0\xB3')
  sirfMessage = staticmethod(sirfMessage)
  
  def switchToNMEA(self, baud):
    mode = '\x02'
        # 0 = Enable NMEA debug messages
        # 1 = Disable NMEA debug messages
        # 2 = Do not change NMEA debug setting
    gga_rate = '\x01' # numer of GGA messages per second; 0 = off
    gga_checksum = '\x01' # 0 = off, 1 = on
    gll_rate = '\x00' # numer of GLL messages per second; 0 = off
    gll_checksum = '\x01' # 0 = off, 1 = on
    gsa_rate = '\x01' # numer of GSA messages per second; 0 = off
    gsa_checksum = '\x01' # 0 = off, 1 = on
    gsv_rate = '\x05' # numer of GSV messages per second; 0 = off
    gsv_checksum = '\x01' # 0 = off, 1 = on
    rmc_rate = '\x01' # numer of RMC messages per second; 0 = off
    rmc_checksum = '\x01' # 0 = off, 1 = on
    vtg_rate = '\x00' # numer of VTG messages per second; 0 = off
    vtg_checksum = '\x01' # 0 = off, 1 = on
    mss_rate = '\x00' # numer of MSS messages per second; 0 = off
    mss_checksum = '\x01' # 0 = off, 1 = on
    zda_rate = '\x01' # numer of ZDA messages per second; 0 = off
    zda_checksum = '\x01' # 0 = off, 1 = on
    baud_rate = struct.pack(">H", baud)
    msg = SiRF.sirfMessage('\x81' + mode + gga_rate + gga_checksum +
                           gll_rate + gll_checksum +
                           gsa_rate + gsa_checksum +
                           gsv_rate + gsv_checksum +
                           rmc_rate + rmc_checksum +
                           vtg_rate + vtg_checksum +
                           mss_rate + mss_checksum +
                           '\x00\x00' +
                           zda_rate + zda_checksum +
                           '\x00\x00' +
                           baud_rate)
    self.stream.write(msg)
    
  def switchToSiRF(self, baud):
    msg = SiRF.addNMEAChecksum("PSRF100,0,%d,8,1,0" % baud)
    self.stream.write(msg)
    self.stream.reopen()   # If a stream doesn't implement this: Bummer!
    try: self.readPacket() # synchronize and skip
    except: pass

  def process(self):
    error, packet, _addr = self.readPacket()
    if error != None:
      raise error

    id = ord(packet[0])
    packet = packet[1:]
    
    # print hex(addr),

    if id == -1:
      raise "Impossible!"
      
    elif id == 2:
      # Measure Navigation Data Out - Message ID 2
      self.handleNav(packet)
      
    elif id == 4:
      # Measured Tracker Data Out - Message ID 4
      self.handleTracker(packet)
      
    elif id == 7:
      # Response: Clock Status Data - Message ID 7
      self.handleClock(packet)

    elif id == 10:
      # Error ID Data - Message ID 10
      self.handleError(packet)

    elif id == 13:
      # Visible List - Message ID 13
      self.handleVisible(packet)
      
    elif id == 41:
      # Geodetic Navigation Data - Message ID 41
      self.handleGeo(packet)

    elif id in [ 8, 9, 27, 28, 30 ]:
      pass # ignored packets
      # 50 BPS Data - Message ID 8
      # CPU Throughput - Message ID 9
      # DGPS status (undocumented) - Message ID 27
      # Navigation Library Measurement Data - Message ID 28
      # Navigation Library SV State Data - Message ID 30
    else:
      raise ProtocolError("Unkown packet, id = %d, seq = %s" %  (id, self.__seq))

    return id == self.completeId
