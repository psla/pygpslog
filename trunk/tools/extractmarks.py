# -*- coding: cp850 -*-
import sys, os, cStringIO as StringIO, optparse, glob, time, copy
from   calendar import timegm

sys.path += [ os.path.join(os.path.dirname(__file__), "../src") ]

from gpslogutil import midpoint, distance, bearing
try:      import cElementTree as ET, elementtree.ElementTree as _ET
except:
  try:    import elementtree.ElementTree as ET, elementtree.ElementTree as _ET
  except: import xml.etree.cElementTree as ET, xml.etree.ElementTree as _ET

BABEL   = r"F:\UTIL\GPS\gpsbabel\gpsbabel-cvs\build\gpsbabel.exe"

MY_NS   = "http://pygpslog.googlecode.com"
GPX_NS  = "http://www.topografix.com/GPX/1/1"
XMLN_NS = "http://www.w3.org/2001/XMLSchema-instance"
LMX_NS  = "http://www.nokia.com/schemas/location/landmarks/1/0"
LMX_XSD = "http://www.nokia.com/schemas/location/landmarks/1/0 lmx.xsd"

_ET._namespace_map[MY_NS]   = "gpslog"
_ET._namespace_map[GPX_NS]  = "gpx"
_ET._namespace_map[LMX_NS]  = "lm"
_ET._namespace_map[XMLN_NS] = "xsi"

verbose = True

def mkpath(path, dflt=GPX_NS, ns=[("gpslog", MY_NS)]):
  res = []
  for p in path.split('/'):
    for n, uri in ns:
      if    p.startswith(n+':'):          res += [ p.replace(n+':', '{'+uri+'}') ]
      elif  p[0] not in ".*@:[" and dflt: res += [ '{'+dflt+'}' + p ]
      else:                               res += [p]
  return '/'.join(res)

def killNs(elt, namespace=GPX_NS):
  for e in [elt] + elt.findall(".//*"):
    e.tag = e.tag.replace("{"+namespace+"}", "")
  return elt

def center(wpt1, wpt2, name=None):
  mark = wpt1.find(mkpath("extensions/gpslog:mark",dflt=''))
  wptn = wpt1.findtext("name", wpt2.findtext("name"))
  if name == None:
    if mark != None: name = mark.text

    if wptn != None: name = wpt1.findtext("name")
    else:            name = name + " - " + wpt1.find("time").text

  p1 = (float(wpt1.get("lat")), float(wpt1.get("lon")))
  p2 = (float(wpt2.get("lat")), float(wpt2.get("lon")))
  return (name, wpt1.find("time").text,
          midpoint(p1, p2), distance(p1, p2)/2.0, mark)

def addCenterpoints(root, ctr):
  for i in range(len(ctr)):
    name, tim, (lat, lon), r, mrk = ctr[i]
    wpt = ET.Element("wpt", lat="%f"%lat, lon="%f"%lon)
    tm  = ET.SubElement(wpt, "time")
    tm.text = tim
    nm  = ET.SubElement(wpt, "name")
    nm.text = name
    ext = ET.SubElement(wpt, "extensions")
    rad = ET.SubElement(ext, "{%s}hacc"%MY_NS)
    rad.text = "%f"%r; rad.tail = "\n      "
    if mrk != None: ext.append(mrk)
    nm.tail = "\n    ";  tm.tail = "\n    "; ext.tail = "\n  "; ext.text = "\n      ";
    wpt.text = "\n    "; wpt.tail = "\n  "
    root.insert(i, wpt)
    
          
def extractMarks(srcGpx, dstGpx=None):
  if ET.iselement(srcGpx):
    sroot = srcGpx
  else:
    src   = ET.parse(srcGpx)
    sroot = src.getroot()

  
  root = ET.Element("gpx")
  root.attrib = sroot.attrib.copy()
  root.set("xmlns",            GPX_NS)
  root.set("{%s}dummy"%GPX_NS, "true") # dummy to force ns insertion
  root.set("{%s}dummy"%MY_NS,  "true") # dummy to force ns insertion
  root.text = "\n  "
  all    = sroot.findall(mkpath("trk/trkseg/trkpt"))
  
  trk = seg = None
  
  ctr  = []
  open = None
  
  for tpt in all:
    mark = tpt.find(mkpath("extensions/gpslog:mark")) # extensions/gpslog:mark"))
    if mark != None and mark.get("in") == "true":
      trk  = ET.SubElement(root, "trk")
      tnm  = ET.SubElement(trk,  "name")
      tdsc = ET.SubElement(trk,  "desc")
      seg  = ET.SubElement(trk,  "trkseg")
      tnm.text  = mark.text
      tdsc.text = mark.text + " - " + tpt.findtext(mkpath("time"))
      # Formatting in DOM :-(
      tnm.tail = "\n    "; seg.text = "\n      "; seg.tail = "\n    ";
      trk.text = "\n    "; trk.tail = "\n  "
      open = tpt

    if seg != None:
      seg.append(killNs(tpt))

    if mark != None and mark.get("in") != "true":
      assert open != None, "Found closing trackpoint without opener"
      ctr += [ center(open, tpt) ]
      trk = seg = open = None
      

  if open != None:
    ctr += [ center(open, tpt) ]
  
  addCenterpoints(root, ctr)

  return root
  
def writeGpx(root, dstGpx):
  dst  = ET.ElementTree(root)
  out = StringIO.StringIO()
  dst.write(out, "UTF-8")
  out = out.getvalue().replace(' gpslog:dummy="true"','').replace(' gpx:dummy="true"','')
  f = file(dstGpx, "w"); f.write(out); f.close()


def brgname(brg):
  BRGNAMES = [ "N", "NE", "E", "SE", "S", "SW", "W", "NW" ]
  return BRGNAMES[int((brg+22.5+180.0)/45) % 8]
  
def makeLandmarks(gpx, dstLmx=None, addtlCat=["Speed"], maxrad=None, makebidi=False):
  sroot = gpx # gpx.getroot()
  root  = ET.Element("{%s}lmx"%LMX_NS)
  root.set("{%s}schemaLocation"%XMLN_NS,  LMX_XSD)
  root.set("{%s}dummy"%LMX_NS, "true")
  root.text = "\n  "

  coll = ET.SubElement(root, "{%s}landmarkCollection"%LMX_NS)
  coll.text = "\n    "; coll.tail = "\n"

  selfcnt = 1
  
  rtime = sroot.findtext("metadata/time")
  if rtime != None: rtime = rtime.text + " - " 
  else:             rtime = ""

  lm = None
  for trk in sroot.findall("trk"):
    tpts = trk.findall("trkseg/trkpt")
    if len(tpts) == 0: continue
    
    def coor(tpt):
      return float(tpt.get("lat")), float(tpt.get("lon"))
      
    def findnext(idx, dist):
      pt1 = coor(tpts[idx])
      i = 0
      for i in range(idx+1, len(tpts)):
        d = distance(pt1, coor(tpts[i]))
        if d >= dist: break
      if i >= len(tpts)-1:
        return -1
        
      return i
      
    mark = tpts[0].find("extensions/{%s}mark"%MY_NS)
    directional = (mark != None and mark.get("directional") == "true")

    r = distance(coor(tpts[0]), coor(tpts[-1]))/2.0
    if maxrad != None and r > maxrad:
      maxdist = r/(int(r/maxrad)+1)*2
    else:
      maxdist = None
      
    if maxdist == None: prev, next, ctr = 0, -1, 0
    else:               prev, next, ctr = 0, findnext(0, maxdist), 1
    
    while True:
      pt1 , pt2 = coor(tpts[prev]), coor(tpts[next])
      lat, lon = midpoint(pt1, pt2)
      rad      = distance(pt1, pt2) / 2.0
      
      if rad < 1.0:  break
    
      name     = trk.findtext("name").strip().capitalize()
      desc     = trk.find("desc")
      if desc == None: desc = rtime + "%d" % selfcnt; selfcnt += 1
      else:            desc = desc.text
      if not desc.startswith(name):
        desc     = name + " - " + desc.strip()
      if ctr: desc += " - %d" % ctr
      lm = ET.SubElement(coll, "{%s}landmark"%LMX_NS)
      nm = ET.SubElement(lm,   "{%s}name"%LMX_NS)
      nm.text = desc
      co = ET.SubElement(lm,   "{%s}coordinates"%LMX_NS)
      la = ET.SubElement(co,   "{%s}latitude"%LMX_NS)
      lo = ET.SubElement(co,   "{%s}longitude"%LMX_NS)
      la.text, lo.text = "%f" % lat, "%f" % lon
      al = tpts[len(tpts)/2].findtext("ele")
      if al != None: ET.SubElement(co,   "{%s}altitude"%LMX_NS).text=al
      acc= tpts[len(tpts)/2].findtext("extensions/{%s}hacc"%MY_NS)
      if acc!= None: ET.SubElement(co,   "{%s}horizontalAccuracy"%LMX_NS).text=acc
      acc= tpts[len(tpts)/2].findtext("extensions/{%s}vacc"%MY_NS)
      if acc!= None: ET.SubElement(co,   "{%s}verticalAccuracy"%LMX_NS).text=acc
      cr = ET.SubElement(lm,   "{%s}coverageRadius"%LMX_NS)
      cr.text = "%.1f" % rad
      if directional or makebidi:
        ai = ET.SubElement(lm, "{%s}addressInfo"%LMX_NS)
        # HACK ALERT:  lmx format doesn't allow for import or export of heading
        di = ET.SubElement(ai, "{%s}phoneNumber"%LMX_NS)
        brg = int(bearing(pt1, pt2))
        if not directional: nm.text += " %s" % brgname(brg)
        di.text = "hdg:%d" % brg
        ai.tail = "\n      "
      for cat in [ name ] + addtlCat:
        ca = ET.SubElement(lm,   "{%s}category"%LMX_NS);
        cn = ET.SubElement(ca,   "{%s}name"%LMX_NS);
        cn.text = cat
        cn.tail = "\n      "; ca.text = "\n        "; ca.tail = "\n      ";
    
      nm.tail = "\n      "; cn.tail = "\n      ";
      co.tail = "\n      "; co.text = "\n        ";
      cr.tail = "\n      "; ca.tail = "\n    ";
      lm.text = "\n      "; lm.tail = "\n    "
    
      if not directional and makebidi:
        # lm180 = ET.SubElement(coll, "{%s}landmark"%LMX_NS)
        lm180 = copy.deepcopy(lm)
        nm = lm180.find("{%s}name"%LMX_NS)
        brg = int(bearing(pt2, pt1))
        nm.text = desc + (" %s" % brgname(brg))
        di = lm180.find("{%(ns)s}addressInfo/{%(ns)s}phoneNumber"%{"ns":LMX_NS})
        di.text = "hdg:%d" % brg
        coll.append(lm180)

      if next < 0:
        break
      else:
        prev, next = next, findnext(next, maxdist)
      
      ctr += 1

  if lm != None: lm.tail = "\n  "
  
  out = StringIO.StringIO()
  lmk = ET.ElementTree(root)
  
  
  if dstLmx != None:
    out = StringIO.StringIO()
    lmk.write(out, "UTF-8")
    out = out.getvalue().replace(' lm:dummy="true"','')
    f = file(dstLmx, "w"); f.write(out); f.close()
  return lmk
  
def isoparse(iso):
  return timegm(time.strptime(iso+"UTC", "%Y-%m-%dT%H:%M:%SZ%Z"))

def isoformat(tm):
  return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(tm))


def fixTime(root):
  ttime = None
  incr  = 1.0
  for tpt in root.getiterator("trkpt"):
    tm = tpt.find("time")
    if tm != None:
      ttime = isoparse(tm.text)
      continue
    if ttime == None:
      rtime = root.find("metadata/time")
      if rtime != None: ttime = isoparse(rtime.text)
      else:             ttime = time.time(); print "WARNING: no timestamp found in file!"
    else:
      ttime += incr
    if tpt[0].tag == "ele": idx = 1
    else:                   idx = 0
    ptime = ET.Element("time")
    ptime.text = isoformat(ttime)
    tpt.insert(idx, ptime)

def addCenters(root):
  ctr = []
  wptt = [ t.text for t in root.findall("wpt/time")]
  for trk in root.getiterator("trk"):
    tpts = trk.findall("trkseg/trkpt")
    name = trk.find("name").text
    if len(tpts) > 0 and tpts[0].find("time") not in wptt:
      ctr += [ center(tpts[0], tpts[-1], name) ]
  addCenterpoints(root, ctr)

def synthesizeNames(gpx):
  for trk in gpx.getiterator("trk"):
    nm = trk.find("name")
    if nm == None: continue  
    for i in range(len(trk)):
      if trk[i].tag in [ "name", "cmt" ]: idx = i + 1
    dsc = ET.Element("desc")  
    dsc.text = nm.text
    trk.insert(idx, dsc)
    nm.text = nm.text.split("-", 1)[0].strip()
    
def synthesizeDate(gpx, filename):
  sp = os.path.splitext(os.path.basename(filename))[0].split('-')
  if len(sp) != 3 or not sp[1].isdigit() or not sp[2].isdigit():
    return
  ts = isoformat(timegm(time.strptime("".join(sp[1:])+"UTC", "%Y%m%d%H%M%S%Z")))
  gpx.find("metadata/time").text = ts

def loadGpx(fn, postprocess=True):
  gpx = ET.parse(fn)
  root = gpx.getroot()
  if root.get("creator").startswith("GpsLog"):
    root = extractMarks(root)
  else:
    killNs(root)
    root.set("xmlns",            GPX_NS)
    root.set("{%s}dummy"%GPX_NS, "true") # dummy to force ns insertion
    root.set("{%s}dummy"%MY_NS,  "true") # dummy to force ns insertion
    if postprocess:
      addCenters(root)
      synthesizeNames(root)
  return root
  
def extractBabelTrack(fn, fmt="kml"):
  tmpfn = "extract.tmp.gpx"
  rc = os.system(BABEL+' -p "" -w -i %s -f "%s" -o gpx,gpxver=1.1 -F "%s"' %\
                 (fmt, fn, tmpfn))
  if rc != 0: raise SystemError, "'%s', %s rc = %d" % (fn, BABEL, rc)
  try:
    gpx = loadGpx(tmpfn, postprocess=False)
    synthesizeDate(gpx, fn)
    fixTime(gpx)
    addCenters(gpx)
    synthesizeNames(gpx)
    return gpx
  finally:
    os.remove(tmpfn)
    # pass

def appendGpx(lhs, rhs):
  for e in rhs.getchildren():
    lhs.append(e)

def sortedGpx(gpx):
  root = ET.Element("gpx")
  root.attrib = gpx.attrib.copy()
  root.set("xmlns",            GPX_NS)
  root.set("{%s}dummy"%GPX_NS, "true") # dummy to force ns insertion
  root.set("{%s}dummy"%MY_NS,  "true") # dummy to force ns insertion
  root.text = "\n  "
  
  for elt in [ "wpt", "rte", "trk" ]:
    root[len(root):] = gpx.findall(elt)
    
  return root
  
def killDuplicates(gpx, comment):
  trks   = [ e for e in gpx.getchildren() if e.tag == "trk" ]
  wpts   = [ e for e in gpx.getchildren() if e.tag == "wpt" ]
  delelt = []
  
  def tsmark(elts, tspath):
    times  = []
    for elt in elts:
      ts = elt.find(tspath)
      if ts != None:
        if ts.text in times:
          if verbose: print "%s: Duplicate %s: %s %s" % (comment, elt.tag, elt.findtext("name"), elt.findtext("desc",""))
          delelt.append(elt)
        else:
          times.append(ts.text)

  tsmark(trks, "trkseg/trkpt/time")
  tsmark(wpts, "time")
  
  for elt in delelt:
    gpx.remove(elt)

def main(argv=None):
  if argv != None:
    sys.argv[1:] = argv

  op = optparse.OptionParser(usage="extractmarks <input>... [options]")
  op.add_option("-o", "--outfile",   "--gpx", )
  op.add_option("-l", "--landmarks", "--lmx")
  op.add_option("-m", "--maxrad",  type="int", help="maximum coverage radius")
  op.add_option("-b", "--makebidi", action="store_true", default=False, help="Make two directional landmarks from non-directional marks")
  
  opts, args = op.parse_args()

  inp = []
  for a in args:
    inp += glob.glob(a)
    
  if len(inp) == 0:
    print >> sys.stderr, "No input files!"
    op.print_help()
    return 42

  gpxs = []
  fns  = {}
  
  dflt = None
  for fn in inp:
    print fn
    name, ext = os.path.splitext(fn)
    ext = ext.lower()
    if dflt == None: dflt = os.path.basename(name)
    if   ext == ".gpx": gpxs += [ loadGpx(fn) ]
    elif ext == ".lmx": gpxs += [ extractBabelTrack(fn, fmt="lmx") ]
    elif ext == ".kml": gpxs += [ extractBabelTrack(fn, fmt="kml") ]
    else:               raise ValueError, "Unknown input filetype '%s'" % fn
    fns[gpxs[-1]] = fn
  
  for gpx in gpxs[1:]:
    appendGpx(gpxs[0], gpx)
    killDuplicates(gpxs[0], fns[gpx])
  
  out = sortedGpx(gpxs[0])

  out.set("creator", "extractmarks for GpsLog")

  if not opts.outfile and not opts.landmarks:
    opts.outfile = dflt + "-marks.gpx"

  if opts.outfile:
    writeGpx(out, opts.outfile)

  if opts.landmarks:
    makeLandmarks(out, opts.landmarks, maxrad=opts.maxrad, makebidi=opts.makebidi)

  return
  

if __name__ == "__main__":
  sys.exit(main())
