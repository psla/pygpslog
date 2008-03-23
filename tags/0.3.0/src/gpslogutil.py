# -*- coding: latin1 -*-
import os, sys, time
import math
from   math import *

if sys.platform.startswith("symbian"):
  import e32, e32dbm
  import settings
  SYMBIAN=True
  IN_EMU = e32.in_emulator()
  DEBUG  = IN_EMU or __name__ == 'editor' or os.path.exists(r"E:\python\gpslog.dbg")
else:
  SYMBIAN= False
  IN_EMU = False
  DEBUG  = True
from IndentedXMLWriter import XMLWriter

#DEBUG = True
#DEBUG = False


FIXTYPES        = ["none","2D","3D","dgps"]

METERS_TO_FEET	= 3.2808399
DAYS_SINCE_1990	= 25569
SECONDS_PER_DAY = 24*3600

DEF_LOGDIR   = (os.path.isdir("E:\Data") and  "E:\Data\GpsLog") or "C:\Data\GpsLog"
if SYMBIAN and e32.in_emulator(): DEF_LOGDIR = r"c:\python"

###############################################################################
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

def coordFromString(co, sb="NS", rng=(-90.0,90.0)):
  if isinstance(co, unicode): co = co.encode("latin1")
  co = co.strip().upper()
  s = 1.0
  if   co[0]  in sb: s = (co[0]  == sb[0] and 1.0) or -1.0; co = co[1:]
  elif co[-1] in sb: s = (co[-1] == sb[0] and 1.0) or -1.0; co = co[:-1]
  co = co.strip()
  if '°' in co or '*' in co or ' ' in co:
    co = co.replace('°',' ').replace('*',' ').replace("'",' ').replace('"', ' ')
    co = co.split()
    fco = 0.0; f = 1.0
    for c in co: fco += f * float(c); f /= 60.0
    fco = s * fco
  else:
    fco = s * float(co)
  if fco < rng[0] or fco > rng[1]: raise ValueError, "Invalid value"
  return fco
  
def sorted(itrbl):
  ret =itrbl[:]
  ret.sort()
  return ret
  


# there seems to be a problem with S60's math library: let's fix it
if not hasattr(math, "radians"): 
  def radians(x):
      return x * pi / 180.0
  math.radians = radians
if not hasattr(math, "degrees"):
  def degrees(x):
      return x * 180.0 / pi
  math.degrees = degrees

Deg2Rad = radians
Rad2Deg = degrees

###############################################################################
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

###############################################################################
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

###############################################################################
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
  
###############################################################################
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
  
###############################################################################
def simpleDestpoint((lat1, lon1), a, d):
  """http://www.movable-type.co.uk/scripts/latlong.html"""
  R = 6371000.0
  lat1, lon1, a = [Deg2Rad(p) for p in [lat1, lon1, a]]
  
  lat2 = asin(sin(lat1)*cos(d/R) + 
              cos(lat1)*sin(d/R)*cos(a))
  lon2 = lon1 + atan2(sin(a)*sin(d/R)*cos(lat1), 
                      cos(d/R)-sin(lat1)*sin(lat2))

  return (Rad2Deg(lat2), Rad2Deg(lon2))

###############################################################################
def simpleBearing(p1, p2):
  """http://www.movable-type.co.uk/scripts/latlong.html"""
  dLon = Deg2Rad(p2[1]-p1[1])
  lat1, lon1 = Deg2Rad(p1[0]), Deg2Rad(p1[1])
  lat2, lon2 = Deg2Rad(p2[0]), Deg2Rad(p2[1])
  y = sin(dLon) * cos(lat2)
  x = cos(lat1)*sin(lat2) - sin(lat1)*cos(lat2)*cos(dLon)
  return (Rad2Deg(atan2(y, x)) + 360.0) % 360.0

###############################################################################
distance  = earthDistance
midpoint  = simpleMidpoint
destpoint = simpleMidpoint
bearing   = simpleBearing

###############################################################################
class Waypoint(list):
  FIELDS = [ "name", "lat", "lon", "alt", "time",
             "speed","hdg", "fix", "hdop","vdop",
             "pdop", "hacc","vacc","attr" ]
  
  position = property(lambda self: (self.lat, self.lon))

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
    except (KeyError, TypeError, IndexError): pass
    return d

  def bearing(self, other):
    return bearing((self.lat, self.lon), other)


###############################################################################
class GpsLogfile(object):
  def __init__(self, logname=None, logdir=DEF_LOGDIR, ext=".log"):
    self.ts = time.time() - 0.000001 # ;-) so we'll always get a difference > 0
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
    
  def waypoint(self, gps, name=None, attr=None, trkpt=True):
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

  def starttime(self):
    return self.ts

  def close(self):
    pass

###############################################################################
class OziLogfile(GpsLogfile):
  def __init__(self, logname=None, logdir=DEF_LOGDIR,
               extended=True, comment="", **_rest):
    
    super(OziLogfile, self).__init__(logname=logname, logdir=logdir, ext=".plt")

    if comment: comment = " ("+comment+")"
    
    self.file = file(self.name(), "wb")
    self.file.write("""OziExplorer Track Point File Version 2.1\r
WGS 84\r
Altitude is in Feet\r
Reserved 3\r
0,2,255,S60 GpsLog%s,0,0,2,8421376\r
<numtrk>\r
""" % comment)

    self.wpts = file(self.name().replace(".plt", ".wpt"), "wb")
    self.wpts.write("""OziExplorer Waypoint File Version 1.1\r
WGS 84\r
Reserved 2\r
Reserved 3\r
""")

    self.extended = extended

  def format(self, gps, skipped=0):
    super(OziLogfile, self).format(gps, skipped)
    seg = str(int(skipped != 0))
    alt = (hasattr(gps, "corralt") and gps.corralt) or gps.alt
    if gps.alt != None: alt = int(alt * METERS_TO_FEET)
    else:               alt = -777
    lat, lon, alt = ("%.6f"%gps.lat, "%.6f"%gps.lon, "%d" % alt)
    ozitime = ("%13.7f" % ((gps.time / SECONDS_PER_DAY) + DAYS_SINCE_1990)).replace(" ","")
    if self.extended:
      ts = gps.gmtime
      fmttime = time.strftime("%H:%M:%S", ts)
      fmtdate = time.strftime("%d-%b-", ts)+ time.strftime("%Y",ts)[-2:]
    else:
      fmttime = fmtdate = ""
    self.file.write(",".join([lat,lon,seg,alt,ozitime,fmtdate,fmttime])+"\r\n")
    
    
  def waypoint(self, gps, name=None, attr=None, trkpt=True):
    wpt = super(OziLogfile, self).waypoint(gps, name, attr, trkpt)

    if wpt.time != None: ozitime = ("%13.7f" % ((wpt.time / SECONDS_PER_DAY) + DAYS_SINCE_1990)).replace(" ","")
    else:                ozitime = ""
    if wpt.alt  != None: alt = int(wpt.alt * METERS_TO_FEET)
    else:                alt = -777
    self.wpts.write("%d,%s,%.6f,%.6f,%s,219,1,3,0,65535,"\
                    "%s,0,0,0,%d,10,0,17\r\n"% (
                    len(self.waypoints()), wpt.name, wpt.lat, wpt.lon,ozitime,
                    wpt.name, alt))
    return wpt
    
  def close(self):
    
    self.file.close()
    self.wpts.close()

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

    if not self.waypoints():
      os.remove(self.name().replace(".plt", ".wpt"))
      
    super(OziLogfile, self).close()

###############################################################################
class GpxLogfile(GpsLogfile):
  def __init__(self, logname=None, logdir=DEF_LOGDIR,
               extended=True, satellites=True,
               comment="", waypointFile=False, **_rest):

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
       "xsi:schemaLocation": "http://pygpslog.googlecode.com http://pygpslog.googlecode.com/files/gpslog_0_3.xsd "\
                             "http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd",
      })
  
    self.gpx.start("metadata")
    self.gpx.start("time")
    self.gpx.data(isoformat(self.ts))
    self.gpx.end("time")
    self.gpx.end("metadata")
    
    if not waypointFile:
      self.gpx.start("trk")
      self.gpx.start("trkseg")
      self.wptgpx = GpxLogfile(logname=self.name().replace(".gpx","-wpt.gpx"), logdir="", waypointFile=True)
      self.wptgpx.ts = self.ts
    else:
      self.wptgpx = None


  def format(self, gps, skipped=0, name=None, attr=None, isWaypoint=False):
    super(GpxLogfile, self).format(gps, skipped)
    
    if skipped:
      self.gpx.end("trkseg")
      self.gpx.start("trkseg")

    tag = (not isWaypoint and "trkpt") or "wpt"

    self.gpx.start(tag, lat="%.9f"%gps.lat, lon="%.9f"%gps.lon)
    if gps.alt != None:
      alt = (hasattr(gps, "corralt") and gps.corralt) or gps.alt
      self.gpx.start("ele");  self.gpx.data("%.6f"%alt); self.gpx.end()
    self.gpx.start("time"); self.gpx.data(isoformat(gps.time)); self.gpx.end()
    if name:
      self.gpx.start("name"); self.gpx.data(name); self.gpx.end()
    if skipped:
      self.gpx.start("cmt"); self.gpx.data("Skipped %d trackpoints!" % skipped); self.gpx.end()

    if self.extended:
      sat = (hasattr(gps, "sat") and gps.sat) or None
      if sat != None:
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

    self.gpx.end(tag)

  def waypoint(self, gps, name=None, attr=None, trkpt=True):
    wpt = super(GpxLogfile, self).waypoint(gps, name, attr, trkpt)
    if trkpt:
      self.format(gps, name=wpt[0], attr=attr)
    if self.wptgpx:
      self.wptgpx.format(wpt, name=wpt.name, attr=wpt.attr, isWaypoint=True)
    return wpt

  def close(self):
    if self.gpx != None:
      self.gpx.close(0);
      self.gpx.comment("Summary:")
      if self.wptgpx != None:
        self.gpx.comment("Trackpoints: %d" % self.tracks())
      else:
        self.gpx.comment("Waypoints: %d" % self.tracks())
      self.gpx.comment("Distance:    %.1fkm" % (self.distance()/1000.0))
      chklen = "Chklen: %09d"
      chklen = chklen % (self.file.tell() + len(chklen%0) + 10)
      self.gpx.comment(chklen)
      del self.gpx; self.gpx = None

    self.file.close()

    if self.wptgpx != None:
      self.wptgpx.close() # will delete itself if there were no waypoints added!

    if self.tracks() == 0:
      os.remove(self.name())

    super(GpxLogfile, self).close()

###############################################################################
def mergeWaypoints(gpxfile, progresscb=None):
  if gpxfile.lower().endswith("-wpt.gpx"): return False
  if not os.path.exists(gpxfile): return False
  name, ext = os.path.splitext(gpxfile)
  wptfile = name+"-wpt.gpx"
  trkfile = name+"-trk.gpx"
  if not os.path.exists(wptfile): return True 
  if os.path.exists(trkfile): return False
  st = os.stat(gpxfile)
  os.rename(gpxfile, trkfile)
  out = file(gpxfile, "wb"); itk = file(trkfile, "rb"); iwp = file(wptfile, "rb")
  
  try:
    try:
      itk.seek(0,2); tot = itk.tell(); itk.seek(0)
      # K.I.S.S
      for tl in itk:
        if tl.startswith("<!-- Chklen:"): break
        out.write(tl)
        if tl.strip() == "</metadata>":
          skip = True
          for wl in iwp:
            if wl.strip() == "</gpx>":       skip = True
            if not skip:                     out.write(wl)
            if wl.strip() == "</metadata>":  skip = False
        if progresscb and tl.strip().startswith("<trkpt"):
          progresscb(itk.tell() * 100 / tot)
      tlen = itk.tell(); wlen = iwp.tell()
    finally:
      out.close(); itk.close(); iwp.close()
    
    def checkfile(fl, cl):
      if not cl.startswith("<!-- Chklen:"): return False
      try:   l = int(cl.split(':')[1].split()[0].lstrip('0'))
      except: return False
      return l == fl

    # if files have been tampered with, leave the by-products
    if checkfile(tlen, tl) and checkfile(wlen, wl):
      out = file(gpxfile, "ab")
      out.seek(0, 2)
      chklen = "<!-- Chklen: %09d -->\n"
      chklen = chklen % (out.tell() + len(chklen%0))
      out.write(chklen)
      out.close()

      os.remove(trkfile)
      os.remove(wptfile)
      
      # this, unfortunately, doesn't have any effects on symbian!
      os.utime(gpxfile, (st.st_atime, st.st_mtime))

  except:
    os.remove(gpxfile)
    os.rename(trkfile, gpxfile)
    raise
    return False

  return True
    
    
if SYMBIAN:
  import e32, appuifw, graphics, topwindow

  #############################################################################
  class GpsLogBaseSettings(settings.Settings):
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
    
  #############################################################################
  class GpsLogSettings(GpsLogBaseSettings):
      pass

  #############################################################################
  class ProgressDialog(object):
    DEFAULT_FONT = (not e32.in_emulator() and "normal") or "dense"
    
    def __init__(self, title="Please wait...", text="",
                       fgcolor=0xffffff, bgcolor=0x000000, progcolor=0x00ff000,
                       font=DEFAULT_FONT, progbar=True, progtext=False):

      (w, hm), (x, y) = appuifw.app.layout(appuifw.EMainPane)
      w -= 4; x += 2; h  = hm / 3; y  = hm - 20

      self.tw      = topwindow.TopWindow()
      self.__title = graphics.Image.new((w*2/3, h/3))
      self.__text  = graphics.Image.new((w, h/3))
      self.font    = font
      self.fgcolor = fgcolor
      self.bgcolor = bgcolor
      self.progcolor = progcolor
      self.tw.position, self.tw.size        = (x,y), (w,h)
      self.tw.shadow,   self.tw.corner_type = 2, "corner2"
      self.tw.background_color              = bgcolor
      
      self.ctlpos = {}

      mt = self.__title.measure_text(u"MM", font=self.font)[0]
      self.toffs = mt[3] - mt[1] + 4
      
      self.__set(self.__title, title, (0,0))
      self.__set(self.__text,  text,  (0, h/3))

      if progbar:
        self.__prog  = graphics.Image.new((w-6, h/3-6))
        self.__prog.clear(self.bgcolor)
        self.__prog.rectangle(((2,2),(w-6-2,h/3-6-2)), outline=self.fgcolor, fill=self.bgcolor)
        self.tw.add_image(self.__prog, (3, h*2/3+3))
        self.ctlpos[self.__prog] = (3, h*2/3+3)
      else:
        self.__prog  = None

      if progtext:
        self.__ptext = graphics.Image.new((w/3, h/3))
        self.__set(self.__ptext,  "",    (w*2/3, 0))
      else:
        self.__ptext = None
        
    def __set(self, ctl, text, pos=None):
      if pos != None: self.ctlpos[ctl] = cpos = pos
      else:           cpos = self.ctlpos[ctl]
      
      ctl.clear(self.bgcolor)
      ctl.text((2,self.toffs), unicode(text), font=self.font, fill=self.fgcolor)
      if pos == None:
        self.tw.remove_image(ctl)
      self.tw.add_image(ctl, cpos)
      e32.ao_yield()

    def setProgress(self, prog):
      if self.__ptext:
        self.__set(self.__ptext, "%d%%" % prog)
      if self.__prog:
        (w,h) = self.__prog.size
        prog = (w-6) * prog / 100
        self.__prog.rectangle(((3,3),(prog,h-3)), self.progcolor, fill=self.progcolor)
        self.tw.remove_image(self.__prog)
        self.tw.add_image(self.__prog, self.ctlpos[self.__prog])
        e32.ao_yield()

    text      = property(None, lambda self, txt: self.__set(self.__text, txt))
    progress  = property(None, setProgress)

    def show(self):
      self.tw.show()

    def hide(self):
      self.tw.hide()

    def destroy(self):
      self.hide()
      if self.tw != None:
        while self.tw.images:
          self.tw.remove_image(self.tw.images[0][0])
        del self.tw; self.tw = None
    
    def __del__(self):
      self.destroy()
      
  #############################################################################
  def mergeAllGpx(logdir):
    prog = ProgressDialog("Merging...")
    prog.show()

    try:
      dirlist = os.listdir(logdir)
      dirlist.sort() # because S60 ignores os.utime
      for f in dirlist:
        name, ext = os.path.splitext(f)
        if name.lower().endswith("-wpt") or name.lower().endswith("-trk") or\
           ext.lower() != ".gpx":
          continue

        prog.text = name

        success = mergeWaypoints(os.path.join(logdir, f), prog.setProgress)

        if not success:
          prog.hide()
          rc = appuifw.query(u"%s failed to merge! Continue?" % name, "query")
          if not rc: break
          prog.show()
        elif os.path.exists(os.path.join(logdir, name+"-trk.gpx")):
          prog.hide()
          rc = appuifw.query(u"%s has been edited. Original files kept! Continue?" % name, "query")
          if not rc: break
          prog.show()
          
    finally:
      del prog

    appuifw.note(u"All done!")

