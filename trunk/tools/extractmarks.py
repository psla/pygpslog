import sys, cStringIO as StringIO
sys.path += [ "../src" ]
from gpslogutil import midpoint, distance
try:      import cElementTree as ET, elementtree.ElementTree as _ET
except:
  try:    import ElementTree as ET, elementtree.ElementTree as _ET
  except: import xml.etree.cElementTree as ET, xml.etree.ElementTree as _ET
from elementtree import XMLTreeBuilder

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

def mkpath(path, dflt=GPX_NS, ns=[("gpslog", MY_NS)]):
  res = []
  for p in path.split('/'):
    for n, uri in ns:
      if    p.startswith(n+':'):          res += [ p.replace(n+':', '{'+uri+'}') ]
      elif  p[0] not in ".*@:[" and dflt: res += [ '{'+dflt+'}' + p ]
      else:                               res += [p]
  return '/'.join(res)

def killNs(elt):
  for e in [elt] + elt.findall(".//*"):
    e.tag = e.tag.replace("{"+GPX_NS+"}", "")
  return elt

def center(wpt1, wpt2):
  mark = wpt1.find(mkpath("extensions/gpslog:mark",dflt=''))
  p1 = (float(wpt1.get("lat")), float(wpt1.get("lon")))
  p2 = (float(wpt2.get("lat")), float(wpt2.get("lon")))
  return (mark.text + " - " +\
          wpt1.find("time").text,
          midpoint(p1, p2), distance(p1, p2)/2.0, mark)

def extractMarks(srcGpx, dstGpx=None):
  src   = ET.parse(srcGpx) # , ET.XMLTreeBuilder()) # , GpxParser())
  sroot = src.getroot()

  
  root = ET.Element("gpx")
  root.attrib = sroot.attrib.copy()
  root.set("xmlns",            GPX_NS)
  root.set("{%s}dummy"%GPX_NS, "1.1") # dummy to force ns insertion
  root.set("{%s}dummy"%MY_NS,  "0.1") # dummy to force ns insertion
  root.text = "\n  "
  all    = sroot.findall(mkpath("trk/trkseg/trkpt"))
  
  trk = seg = None
  
  ctr  = []
  open = None
  
  for tpt in all:
    mark = tpt.find(mkpath("extensions/gpslog:mark")) # extensions/gpslog:mark"))
    if mark != None and mark.get("in") == "true":
      print mark.text
      trk  = ET.SubElement(root, "trk")
      tnm  = ET.SubElement(trk,  "name")
      tdsc = ET.SubElement(trk,  "desc")
      seg  = ET.SubElement(trk,  "trkseg")
      tnm.text  = mark.text
      tdsc.text = mark.text + " - " + tpt.find(mkpath("time")).text
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
  
  for i in range(len(ctr)):
    name, (lat, lon), r, mrk = ctr[i]
    wpt = ET.Element("wpt", lat="%f"%lat, lon="%f"%lon)
    nm  = ET.SubElement(wpt, "name")
    nm.text = name
    ext = ET.SubElement(wpt, "extensions")
    rad = ET.SubElement(ext, "{%s}hacc"%MY_NS)
    rad.text = "%f"%r; rad.tail = "\n      "
    ext.append(mrk)
    nm.tail = "\n    "; ext.tail = "\n  "; ext.text = "\n      "; wpt.text = "\n    "; wpt.tail = "\n  "
    root.insert(i, wpt)
    

  dst  = ET.ElementTree(root)
  if dstGpx:
    out = StringIO.StringIO()
    dst.write(out, "UTF-8")
    out = out.getvalue().replace(' gpslog:dummy="0.1"','').replace(' gpx:dummy="1.1"','')
    f = file(dstGpx, "w"); f.write(out); f.close()
  return dst

def makeLandmarks(gpx, dstLmx=None, addtlCat=["Speed"]):
  sroot = gpx.getroot()
  root  = ET.Element("{%s}lmx"%LMX_NS)
  root.set("{%s}schemaLocation"%XMLN_NS,  LMX_XSD)
  root.set("{%s}dummy"%LMX_NS, "0.1")
  root.text = "\n  "

  coll = ET.SubElement(root, "{%s}landmarkCollection"%LMX_NS)
  coll.text = "\n    "; coll.tail = "\n"

  selfcnt = 1
  
  rtime = sroot.find("metadata/time")
  if rtime != None: rtime = rtime.text + " - " 
  else:             rtime = ""

  lm = None
  for trk in sroot.findall("trk"):
    tpts = trk.findall("trkseg/trkpt")
    if len(tpts) == 0: continue
    
    la1, lo1, la2, lo2 = tpts[0].get("lat"), tpts[0].get("lon"), \
                         tpts[-1].get("lat"), tpts[-1].get("lon")
    la1, lo1, la2, lo2 = [ float(f) for f in [la1, lo1, la2, lo2]]
    lat, lon = midpoint((la1,lo1), (la2, lo2))
    rad      = distance((la1,lo1), (la2, lo2)) / 2.0
    
    name     = trk.find("name").text.strip().capitalize()
    desc     = trk.find("desc")
    if desc == None: desc = rtime + "%d" % selfcnt; selfcnt += 1
    desc     = name + " - " + desc.strip()

    lm = ET.SubElement(coll, "{%s}landmark"%LMX_NS)
    nm = ET.SubElement(lm,   "{%s}name"%LMX_NS);
    nm.text = desc
    co = ET.SubElement(lm,   "{%s}coordinates"%LMX_NS);
    la = ET.SubElement(co,   "{%s}latitude"%LMX_NS);
    lo = ET.SubElement(co,   "{%s}longitude"%LMX_NS);
    la.text, lo.text = "%f" % lat, "%f" % lon
    cr = ET.SubElement(lm,   "{%s}coverageRadius"%LMX_NS);
    cr.text = "%.1f" % rad
    for cat in [ name ] + addtlCat:
      ca = ET.SubElement(lm,   "{%s}category"%LMX_NS);
      cn = ET.SubElement(ca,   "{%s}name"%LMX_NS);
      cn.text = cat
      cn.tail = "\n      "; ca.text = "\n        "; ca.tail = "\n      ";
    
    nm.tail = "\n      "; cn.tail = "\n      ";
    co.tail = "\n      "; co.text = "\n        ";
    cr.tail = "\n      "; ca.tail = "\n    ";
    lm.text = "\n      "; lm.tail = "\n    "
    
  if lm != None: lm.tail = "\n  "
  
  out = StringIO.StringIO()
  lmk = ET.ElementTree(root)
  
  
  if dstLmx != None:
    out = StringIO.StringIO()
    lmk.write(out, "UTF-8")
    out = out.getvalue().replace(' lm:dummy="0.1"','')
    f = file(dstLmx, "w"); f.write(out); f.close()
  return lmk
  

def main():
  if sys.argv[1] and not sys.argv.lower().endswith(".kml"):
    gpx = extractMarks(sys.argv[1], sys.argv[2])
  else:
    if sys.argv.lower().endswith(".kml"):
      rc = os.system(BABEL+' -p "" -w -i kml -f "%s" -o gpx,gpxver=1.1 -F "%s"' %\
                     (sys.argv[1], sys.argv[2]))
      if rc != 0: sys.exit(rc)

    gpx = ET.parse(sys.argv[2])
    killNs(gpx.getroot())

  if len(sys.argv) > 3:
    makeLandmarks(gpx, sys.argv[3])

  

if __name__ == "__main__":
  main()