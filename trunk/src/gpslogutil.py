import os, sys, time
from math import *

if sys.platform.startswith("symbian"):
  import e32, e32dbm
  import settings
  SYMBIAN=True
else:
  SYMBIAN=False
from IndentedXMLWriter import XMLWriter

FIXTYPES        = ["none","2D","3D","dgps"]

METERS_TO_FEET	= 3.2808399
DAYS_SINCE_1990	= 25569
SECONDS_PER_DAY = 24*3600

DEF_LOGDIR   = (os.path.isdir("E:\Data") and  "E:\Data\GpsLog") or "C:\Data\GpsLog"
if SYMBIAN and e32.in_emulator(): DEF_LOGDIR = r"c:\python"

def isoformat(ts):
  return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))

def coord(c, sign="NS", dec=False):
  if c == None:
    return "---"
  if not dec:
    sg = sign[0]
    if c < 0: sg = sign[1]; c = abs(c)
    d = int(c); m = (c - d) * 60.0; s = (m - int(m)) * 60.0; m = int(m)
    return u"%-2d\u00b0%02d'%-5.2f %s" % (d, m, s, sg)
  else:
    return u"%.6f" % c

def sorted(itrbl):
  ret =itrbl[:]
  ret.sort()
  return ret
  

def Deg2Rad(x):
    "Degrees to radians."
    return x * (pi/180.0)
    
def Rad2Deg(x):
    return x * 180.0 / pi

def CalcRad(lat):
    "Radius of curvature in meters at specified latitude."
    a = 6378.137
    e2 = 0.081082 * 0.081082
    # the radius of curvature of an ellipsoidal Earth in the plane of a
    # meridian of latitude is given by
    #
    # R' = a * (1 - e^2) / (1 - e^2 * (sin(lat))^2)^(3/2)
    #
    # where a is the equatorial radius,
    # b is the polar radius, and
    # e is the eccentricity of the ellipsoid = sqrt(1 - b^2/a^2)
    #
    # a = 6378 km (3963 mi) Equatorial radius (surface to center distance)
    # b = 6356.752 km (3950 mi) Polar radius (surface to center distance)
    # e = 0.081082 Eccentricity
    sc = sin(lat)
    x = a * (1.0 - e2)
    z = 1.0 - e2 * sc * sc
    y = pow(z, 1.5)
    r = x / y

    r = r * 1000.0	# Convert to meters
    return r

def earthDistance((lat1, lon1), (lat2, lon2)):
    "Distance in meters between two points specified in degrees."
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
    # a should be in [1, -1] but can sometimes fall outside it by
    # a very small amount due to rounding errors in the preceding
    # calculations (this is prone to happen when the argument points
    # are very close together).  Thus we constrain it here.
    if abs(a) > 1: a = 1
    elif a < -1: a = -1
    return CalcRad((lat1+lat2) / 2) * acos(a)

def simpleDistance(p1, p2):
  lat1, lon1 = p1
  lat2, lon2 = p2
  try:
    R = 6367000.0 # meters
    dlon = math.radians(abs(lon1 - lon2))
    dlat = math.radians(abs(lat1 - lat2))
    slat = math.radians(lat1)
    olat = math.radians(lat2)
    a = math.sin(dlat/2.0) ** 2.0 + math.cos(slat) * math.cos(olat) * math.sin(dlon/2.0) ** 2.0
    c = 2.0 * math.asin(min(1.0,math.sqrt(a)))
    d = R * c
  except Exception, exc:
    print "MATH ERROR:", lat1, lon1, dlon, dlat, a, exc
    return 0.0
  return d
  
def simpleMidpoint(p1, p2):
  """http://www.movable-type.co.uk/scripts/latlong.html"""
  dLon = Deg2Rad(p2[1]-p1[1])
  lat1, lon1 = Deg2Rad(p1[0]), Deg2Rad(p1[1])
  lat2, lon2 = Deg2Rad(p2[0]), Deg2Rad(p2[1])
  Bx = cos(lat2) * cos(dLon)
  By = cos(lat2) * sin(dLon)
  lat3 = atan2(sin(lat1)+sin(lat2),
               sqrt((cos(lat1)+Bx)*(cos(lat1)+Bx) +  By*By ) )
  lon3 = lon1 + atan2(By, cos(lat1) + Bx)
  return Rad2Deg(lat3), Rad2Deg(lon3)
  
def simpleDestpoint((lat1, lon1), a, d):
  """http://www.movable-type.co.uk/scripts/latlong.html"""
  R = 6371000.0
  lat1, lon1, a = [Deg2Rad(p) for p in [lat1, lon1, a]]
  
  lat2 = asin(sin(lat1)*cos(d/R) + 
              cos(lat1)*sin(d/R)*cos(a))
  lon2 = lon1 + atan2(sin(a)*sin(d/R)*cos(lat1), 
                      cos(d/R)-sin(lat1)*sin(lat2))

  return (Rad2Deg(lat2), Rad2Deg(lon2))


distance  = earthDistance
midpoint  = simpleMidpoint
destpoint = simpleMidpoint

class Waypoint(list):
  FIELDS = [ "name", "lat", "lon", "alt", "time",
             "speed","hdg", "fix", "hdop","vdop", "pdop",
             "hacc", "vacc", "attr" ]
  
  def __idx(self, name):
    if not name in self.FIELDS:
      raise AttributeError, name
    return self.FIELDS.index(name)

  def __getattr__(self, name):
    return self[self.__idx(name)]

  def __setattr__(self, name, val):
    self[self.__idx(name)] = val

  def distance(self, other):
    d = distance(other, (self.lat, self.lon))
    try: 
      r = self.attr["radius"]
      if d <= r: d = 0.0
      else:      d -= r
    except (KeyError, TypeError): pass
    return d

class GpsLogfile(object):
  def __init__(self, logname=None, logdir=DEF_LOGDIR, ext=".log"):
    self.ts = time.time()
    if logname == None:
      logname = time.strftime("GpsLog-%Y%m%d-%H%M%S", time.gmtime(self.ts))
    logname = os.path.join(logdir, logname)
      
    if ext and not logname.endswith(ext):
      logname += ext

    self.logname  = logname
    self.numtrk   = 0
    self.dist     = 0.0
    self.prev     = None
    self.waypts   = []
    
  def format(self, gps, skipped=0):
    self.numtrk   += 1
    if self.prev:
      self.dist   += distance(gps.position, self.prev)
    self.prev      = gps.position
    
  def waypoint(self, gps, name=None, attr=None):
    if name == None: name = "Waypoint %d" % (len(self.waypts)+1)
    alt = (hasattr(gps, "corralt") and gps.corralt) or gps.alt
    self.waypts += [ Waypoint((name, gps.lat,  gps.lon,  alt,  gps.time,
                              gps.speed,gps.hdg,  gps.fix,
                              gps.hdop, gps.vdop, gps.pdop,
                              gps.hacc, gps.vacc, attr)) ]
    return self.waypts[-1]

  def waypoints(self):
    return self.waypts

  def name(self):
    return self.logname

  def tracks(self):
    return self.numtrk

  def distance(self):
    return self.dist


class OziLogfile(GpsLogfile):
  def __init__(self, logname=None, logdir=DEF_LOGDIR,
               extended=True, comment="", **_rest):
    
    super(OziLogfile, self).__init__(logname=logname, logdir=logdir, ext=".plt")

    if comment: comment = " ("+comment+")"
    
    self.file = file(self.name(), "w")
    self.file.write("""OziExplorer Track Point File Version 2.1
WGS 84
Altitude is in Feet
Reserved 3
0,2,255,S60 GpsLog%s,0,0,2,8421376
<numtrk>
""" % comment)
    self.extended = extended

  def format(self, gps, skipped=0):
    super(OziLogfile, self).format(gps, skipped)
    seg = str(int(skipped != 0))
    if gps.alt != None: alt = int(gps.corralt * METERS_TO_FEET)
    else:               alt = -777
    lat, lon, alt = ("%.6f"%gps.lat, "%.6f"%gps.lon, "%d" % alt)
    ozitime = ("%13.7f" % ((gps.time / SECONDS_PER_DAY) + DAYS_SINCE_1990)).replace(" ","")
    if self.extended:
      ts = gps.gmtime
      fmttime = time.strftime("%H:%M:%S", ts)
      fmtdate = time.strftime("%d-%b-", ts)+ time.strftime("%Y",ts)[-2:]
    else:
      fmttime = fmtdate = ""
    self.file.write(",".join([lat,lon,seg,alt,ozitime,fmtdate,fmttime])+"\n")
    
  def close(self):
    self.file.close()
    
    if self.tracks() == 0:
      os.remove(self.name())
    else:
      f = file(self.name(), "r")
      plt = f.read()
      f.close()
      plt = plt.replace("<numtrk>", str(self.tracks()))
      f = file(self.name(), "w")
      f.write(plt)
      f.close()


class GpxLogfile(GpsLogfile):
  def __init__(self, logname=None, logdir=DEF_LOGDIR,
               extended=True, satellites=True, comment="", **_rest):

    super(GpxLogfile, self).__init__(logname=logname, logdir=logdir, ext=".gpx")
    
    self.extended   = extended
    self.satellites = satellites

    self.file = file(self.name(), "w")

    self.gpx  = XMLWriter(self.file, encoding="utf-8")
      
    self.gpx.declaration()
    
    if comment: comment = " ("+comment+")"

    self.gpx.start("gpx",
      {"version":   "1.1", "creator": "GpsLog for S60%s" % comment,
       "xmlns:xsi":          "http://www.w3.org/2001/XMLSchema-instance",
       "xmlns":              "http://www.topografix.com/GPX/1/1",
       "xmlns:gpslog":       "http://pygpslog.googlecode.com",
       "xsi:schemaLocation": "http://pygpslog.googlecode.com http://pygpslog.googlecode.com/files/gpslog.xsd "\
                             "http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd",
      })
  
    self.gpx.start("metadata")
    self.gpx.start("time")
    self.gpx.data(isoformat(self.ts))
    self.gpx.end("time")
    self.gpx.end("metadata")
    self.gpx.start("trk")
    self.gpx.start("trkseg")

  def format(self, gps, skipped=0, name=None, attr=None):
    super(GpxLogfile, self).format(gps, skipped)
    
    if skipped:
      self.gpx.end("trkseg")
      self.gpx.start("trkseg")

    self.gpx.start("trkpt", lat="%.9f"%gps.lat, lon="%.9f"%gps.lon)
    if gps.alt != None:
      self.gpx.start("ele");  self.gpx.data("%.6f"%gps.corralt); self.gpx.end()
    self.gpx.start("time"); self.gpx.data(isoformat(gps.time)); self.gpx.end()
    if name:
      self.gpx.start("name"); self.gpx.data(name); self.gpx.end()
    if skipped:
      self.gpx.start("cmt"); self.gpx.data("Skipped %d trackpoints!" % skipped); self.gpx.end()

    if self.extended:
      if gps.sat != None:
        self.gpx.start("sat");  self.gpx.data(str(gps.nsat)); self.gpx.end()
      if gps.fix != None:
        self.gpx.start("fix")
        self.gpx.data(FIXTYPES[gps.fix-1])
        self.gpx.end()
      if gps.hdop != None:
        self.gpx.start("hdop");  self.gpx.data("%.1f"%gps.hdop); self.gpx.end()
      if gps.vdop != None:
        self.gpx.start("vdop");  self.gpx.data("%.1f"%gps.vdop); self.gpx.end()
      if gps.pdop != None:
        self.gpx.start("pdop");  self.gpx.data("%.1f"%gps.pdop); self.gpx.end()
    if self.extended or attr:
      self.gpx.start("extensions")
    if self.extended:
      if gps.speed != None:
        self.gpx.start("gpslog:speed"); self.gpx.data("%.2f"%gps.speed); self.gpx.end()
      if gps.hdg != None:
        self.gpx.start("gpslog:hdg"); self.gpx.data("%.4f"%gps.hdg); self.gpx.end()
      if gps.hacc != None:
        self.gpx.start("gpslog:hacc");  self.gpx.data("%.1f"%gps.hacc); self.gpx.end()
      if gps.vacc != None:
        self.gpx.start("gpslog:vacc");  self.gpx.data("%.1f"%gps.vacc); self.gpx.end()
      sat = gps.sat
      if self.satellites and sat != None:
        for s in sat:
          self.gpx.start("gpslog:sat",
                         prn=str(s.prn), az=str(s.azimuth), ele=str(s.elevation),
                         signal=str(s.signal), used=(s.used and "true") or "false")
          self.gpx.end()
    if attr:
      for key in sorted(attr.keys()):
        if type(attr[key]) == tuple:
          xmlatt, data = attr[key]
        else:
          xmlatt, dat  = None, attr[key]
        self.gpx.start(key, **xmlatt);
        if data != None:
          self.gpx.data(data);
        self.gpx.end()
    if self.extended or attr:
      self.gpx.end("extensions")

    self.gpx.end("trkpt")

  def waypoint(self, gps, name=None, attr=None):
    wpt = super(GpxLogfile, self).waypoint(gps, name, attr)
    self.format(gps, name=wpt[0], attr=attr)
    return wpt

  def close(self):
    if self.gpx != None:
      self.gpx.close(0);
      self.gpx.comment("Summary:")
      self.gpx.comment("Trackpoints: %d" % self.tracks())
      self.gpx.comment("Distance:    %.1fkm" % (self.distance()/1000.0))
      del self.gpx; self.gpx = None

    self.file.close()
    if self.tracks() == 0:
      os.remove(self.name())

if SYMBIAN:
  class GpsLogSettings(settings.Settings):
    def __init__(self, desc_list, fname):
      self.ext_desc_list = desc_list
      dl = []; self.hide = {}
      for (nm, tp, ls, vl) in desc_list:
        if type(nm) in [tuple, list] and len(nm) > 2:
          nm, dsp, hide = nm
          if hide: self.hide[nm] = hide
          nm = (nm, dsp)
        dl += [(nm,tp,ls,vl)]
      settings.Settings.__init__(self, dl, fname)

    def execute_dialog(self, menu=None):
      saveDl = self.desc_list[:]
      self.desc_list = [ d for d in self.desc_list if d[0] not in self.hide ]
      settings.Settings.execute_dialog(self, menu)
      self.desc_list = saveDl[:]

    def save(self):
      db = e32dbm.open(self.fname, "c")
      for (name, type, lst, value) in self.desc_list:
        db[name] = str(eval("self." + name))
      db.reorganize()
      db.close()
  

    def areNew(self):
      db = e32dbm.open(self.fname, "c")
      neew = not db.has_key(self.desc_list[0][0])
      db.close()
      return neew

    def reset(self):
      if os.path.exists(self.fname+".e32dbm"):
        os.remove(self.fname+".e32dbm")
      self.__init__(self.ext_desc_list, os.path.basename(self.fname))
    
