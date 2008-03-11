# -*- coding: cp850 -*-
import gpssplash; reload(gpssplash);
gpssplash.show("Initializing.")
import os, time, traceback, math, thread
import appuifw, e32

IN_EMU = e32.in_emulator()
DEBUG  = IN_EMU or __name__ == 'editor' or os.path.exists(r"E:\python\gpslog.dbg")
#DEBUG = True
#DEBUG = False

import graphics
from   key_codes   import *
if     IN_EMU:     import gpslogutil; reload(gpslogutil)

gpssplash.show("Initializing..")
from   gpslogutil  import GpsLogSettings, OziLogfile, GpxLogfile,\
                          coord, distance, midpoint, sorted, isoformat,\
                          DEF_LOGDIR, FIXTYPES
gpssplash.show("Initializing...")
import gpsloglm  
if IN_EMU: reload(gpsloglm)
try:    from e32jext import cputime
except: cputime = None

gpssplash.show("Loading User Icons...")
import gpslogimg
if IN_EMU: reload(gpslogimg)

gpssplash.show("Loading GPS modules...")
try:    from gpslib.gpspos import PositioningProvider
except: PositioningProvider = None
try:    from gpslib.gpsloc import LocationRequestorProvider
except: LocationRequestorProvider = None
try:    from gpslib.gpsnmea import NMEABluetoothProvider
except: NMEABluetoothProvider = None
if IN_EMU or os.path.isdir(os.path.join(DEF_LOGDIR, "Sim")):
  gpssplash.show("Loading Simulator...")
  if IN_EMU: import gpslib.gpssim; reload(gpslib.gpssim)
  try:       from gpslib.gpssim import XMLSimulator
  except: XMLSimulator = None
else: XMLSimulator = None

DEF_MINDIST  = 25 # m
DEF_MAXDIST  = 80 # m/s = 288 km/h. Raise this when flying
DEF_LOGFMT   = "GPX"
MORNING      = "05"
EVENING      = "18"

DEL_THRESHOLD   = 20
DISP_NORM       = 0
DISP_COMPASS    = 1
DISP_LANDMARK   = 2
DISP_SATGRAPH   = 3
DISP_OFF        = 4
DISP_SAT        = 99 # unused, will disappear
DISPMODES       = [ "GpsLog", "Compass", "Landmarks", "Satellite View", "Powersave" ] #, (DISP_TMP, "Tmp")] # , (DISP_SAT, "Satellite Data")]
DISP_COLORS     = {
                    "day":   (0x000000, 0xffffff,
                              { "txtalpha": 0x707070, "satmark": 0x000000 }),
                    "night": (0xc12000, 0x000000,
                              { "txtalpha": 0x808080, "satmark": 0x400000 }),
                  }
TRAVELMODES     = [ ("City", 40, 50, 70), ("Overland", 100, 120, 140), ("Highway", 130, 160, 250) ]
INTERNAL_GPS    = u"Nokia Positioning"
LOCREQ_GPS      = u"Location Requestor"
XMLSIM_GPS      = u"XML Simulator"
MARKERS         = gpslogimg.ICONS.keys(); MARKERS.sort(); MARKERS = (MARKERS[2:]+[MARKERS[1]])[:6]

IMG_FONT        = (not IN_EMU and "normal") or "dense" #"title" # "dense"

PERF_CTRS       = 30


if not cputime: PERF_CTRS = 0

singleton = None

def isdaylight(): # :-)
  time.strftime("%H") >= MORNING and time.strftime("%H") <= EVENING

def globalCallback(gps): # the dreaded CONE 8!
  if singleton:
    return singleton.gpsCallback(gps)


if not hasattr(__builtins__, "sum"):
  def sum(seq):
    s = 0
    for e in seq: s += e
    return s

class GpsLog(object):

  ############################################################################
  def run(self, standalone=False):
    gpssplash.show("Starting up...")
    dummy  = appuifw.Text()
    
    self.gps     = None
    self.view    = None
    self.lbox    = None
    self.log     = None
    self.prev    = None
    self.prevrec = None
    self.paused  = False
    self.ignored = 0
    self.appbody = gpssplash.savedBody()
    self.focus   = True
    self.font    = dummy.font
    self.prevsat = 0
    self.stopping= False
    self.started = 0
    self.cbcg    = None
    self.lbsmall = False
    self.marker  = None
    self.markcnt = 0
    self.fmarker = None
    self.nearest = None
    self.gpssema = None
    self.busy    = 0
    self.perf    = None
    self.thperf  = 0.0
    
    self.nightmenu = None
    
    del dummy

    self.initializeSettings()

    self.applySettings()
    
    if isdaylight():
      self.colorMode("day")
    else:
      self.colorMode("night")

    if not self.cpugraph:
      global PERF_CTRS
      PERF_CTRS = 0
    
    self.settings.satupd = -5
    
    if self.settings.btdevice == "on":
      self.btaddr = None
      self.settings.btdevice = "off"
    
    gpssplash.hide()

    try:
      self.standalone = standalone
      self.lck  = e32.Ao_lock()

      self.view = appuifw.Canvas(self.drawGraph)
      appuifw.app.body = self.view
        
      #self.view = None

      if self.view != None:
        self.bindDefault(self.view)
        if not self.autostart:  self.view.bind(EKeyYes, self.start)
        else:                   self.view.bind(EKeyYes, self.stop)

      if self.lmsettings.uselm:
        lmmenu = [ (u"Landmark Settings", self.editLandmarkSettings) ]
        lmdisp = ( (u"Landmarks", lambda: self.cycleMode(set=DISP_LANDMARK) ), )
      else:
        lmmenu  = []
        lmmdisp = ()

      appuifw.app.menu =  [
        (u"Start",         self.start),
        (u"Pause",         self.togglePause),
        (u"Display Mode",  ( ( u"Overview",   lambda: self.cycleMode(set=DISP_NORM)),
                             ( u"Compass",    lambda: self.cycleMode(set=DISP_NORM))
                           ) + lmdisp + (
                             ( u"Satellites", lambda: self.cycleMode(set=DISP_SATGRAPH)),
                             ( u"Toggle Night Mode", self.colorMode),
                             ( u"Toggle Fullscreen", self.screenMode),
                           ) ),
      ] + lmmenu + [
        (u"Settings",      self.editSettings),
        (u"Exit",          self.close),
      ]
      
      appuifw.app.screen = str(self.settings.screen)

      appuifw.app.focus            = self.handleFocus
      appuifw.app.exit_key_handler = self.close
      
      self.display()

      if self.autostart:
        self.start()

      global singleton
      singleton = self

      self.lck.wait()

      self.stop()

      self.settings.save()
      self.lmsettings.save()

      self.cleanup()
    
      if self.standalone:
        appuifw.app.set_exit()
      else:
        print "Bye!"

    finally:
      self.closeLog()
      if self.gps:
        self.gps.close()
        del self.gps
      singleton = None
      gpsloglm.close()

  ############################################################################
  def bindDefault(self, control):
     self.boundkeys = []

     def bind(keys, func):
       if type(keys) == str: keys = [ ord(k) for k in keys ]
       if type(keys) in [ int, long ]: keys = [ keys ]
       for k in keys:
         if not (k, control) in self.boundkeys: self.boundkeys.append((k, control))
         control.bind(k, func)

     bind(EKeyRightArrow,      self.cycleMode)
     bind([EKey3, EKeySelect], self.cycleMode)
     bind(EKeyLeftArrow,       lambda: self.cycleMode(forward=False))
     bind([EKey1, ord(".")],   lambda: self.cycleMode(forward=False))
     bind(EKeyBackspace,       self.togglePause)
     bind(EKeyUpArrow,         self.cycleTravel)
     bind(EKeyDownArrow,       lambda: self.cycleTravel(forward=False))
     bind(EKey0,               self.markWaypoint)
     bind(EKeyStar,            self.markOut)
     bind(EKeyHash,            self.colorMode)
     bind(EKey2,               self.screenMode)
     appuifw.app._self = self
     for key in range(EKey4, EKey9+1):
       bind(key, eval("lambda: appuifw.app._self.markIn(%d)" % (key-EKey0-4)))
     

  ############################################################################
  def handleFocus(self, focus):
    self.focus = focus
    
  ############################################################################
  def cpuGraph(self, img):
    if self.log == None or cputime == None or not self.cpugraph:
      return
    try:    cpu, tm = cputime(), time.clock() # may raise errors on some devices!
    except: return
    if self.perf == None:
      self.perf = [ (0, 0, 0.0, 0.0) ] * (PERF_CTRS) # + [(cpu, tm, 100.0, 5.0)]
      return
    used, passed = cpu - self.perf[-1][0] + self.thperf, tm - self.perf[-1][1]
    self.thperf = 0.0
    if passed > 0: used = used / passed
    else:          used = 0.0
    useavg = PERF_CTRS/4
    avg = (used + sum([p[2] for p in self.perf[-useavg:-1]])) / useavg
    
    self.perf = (self.perf + [(cpu, tm, used, avg)])[-PERF_CTRS:]
    if img == None: return

    # count this function too
    # w, h, x, xs, my, col = img.size + (0, img.size[0]-53-PERF_CTRS, 20, 0x007f00)
    x, my, col = 0, 20, 0x009f00
    if self.busy > 0 or avg >= .25: col = 0xff0000
    
    pimg = graphics.Image.new((PERF_CTRS+2, my+2))
    mask = graphics.Image.new((PERF_CTRS+2, my+2), "L")
    pimg.rectangle((0,0,PERF_CTRS+2,my), self.fg, fill=self.bg)
    mask.clear(0xc0c0c0)

    for cpu, tm, used, pavg in self.perf:
      # make 90% look like full load
      y  = my-min(my*int(1000.0*used)/900+1,my)-2
      pimg.line((x+1,my-2,x+1,y), col)
      x += 1

    gpslogimg.alphaText(pimg, (1,2), u"%2.f%%" % (avg*100.0),
                        fill=self.fg, font=IMG_FONT, alpha=0xd0d0d0)

    w, h = img.size
    img.blit(pimg, target=(w-PERF_CTRS-53, h-my), mask=mask)
    
    del pimg, mask

  ############################################################################
  def drawMarkers(self, img):
    w, h = img.size
    
    x = w-64
    if self.marker and self.marker[0] in gpslogimg.ICONS:
      ico = gpslogimg.ICONS[self.marker[0]]
      ico.draw(img, pos=(x,h-84), alpha=0x7f7f7f)
      x -= ico.img.size[0] + 5
     
    if self.lmsettings.uselm and self.lmsettings.warncat and\
       not self.lmsettings.lmico and self.gps:
      
      try:
        nearest = gpsloglm.NearestLm(self.gps.lat, self.gps.lon,
                                     cat=self.lmsettings.warncat,
                                     max=1, maxdist=self.lmsettings.warnrad)
      except:
        if DEBUG: raise
        nearest = None

      if nearest:
        nearest, svgico = nearest[0]
        try:    cat = self.lmsettings.cat(nearest.attr["categories"][0])[0]
        except: cat = None
        if cat in gpslogimg.ICONS: ico = gpslogimg.ICONS[cat]
        else:                      ico = gpslogimg.ICONS["Default"]
        ico.draw(img, pos=(x,h-84), alpha=0xc0c0c0)
        caption = nearest.name
        if cat and caption.startswith(cat): caption = caption[len(cat):].strip(" -")
        gpslogimg.alphaText(img, (2, h-60), caption, 
                            fill=self.fg, alpha=self.txtalpha, font=IMG_FONT)
        e32.ao_yield()
        self.fmarker = cat
      else:
        self.fmarker = None
    else:
      self.fmarker = None

  ############################################################################  
  def drawGraph(self, rect=None):

    if not self.view:
      return

    global line

    font   = self.font
    bold   = font[:2] + ( font[2] | graphics.FONT_BOLD, )
    large  = (font[0], font[1] * 5 / 3, font[2] | graphics.FONT_BOLD)
    small  = (font[0], font[1] * 3 / 4, font[2])
    smit   = (font[0], font[1] * 3 / 4, font[2] | graphics.FONT_ITALIC)
    fg, bg = self.fg, self.bg
    
    gps    = self.gps

    dispmode = self.dispmode()
    
    #------------------------------------------------------------------------
    if self.busy > 0: # TODO: warn or beep or ...
      if DEBUG: print "Busy!", self.busy, "Mode:", dispmode
      self.busy = 0

    #------------------------------------------------------------------------
    if dispmode == DISP_OFF and self.gps != None and gps.dataAvailable():
      if (self.settings.satupd < 0) or (int(gps.time - self.prevsat) >= self.settings.satupd):
        self.settings.satupd = abs(self.settings.satupd)
        self.prevsat = gps.time
        fg, bg, m = DISP_COLORS["night"]
        self.view.clear(bg);
        if self.colmode != "night": 
          self.view.text((2, 20), u"Display is off", fill=fg, font=bold)
        self.cpuGraph(None)
      return

    # some helpers
    def prnt(x, y, text, font=font, fill=fg):
      text = unicode(text)
      # msr = self.view.measure_text(u"MM", font)[0]
      # dy = msr[3]-msr[1]
      dy = 0
      self.view.text((x, y-dy), text, fill=fill, font=font)
      
    if not hasattr(self.view, "drawNow"): # i.e. GLCanvas
      img = graphics.Image.new(self.view.size)
      img.clear(bg)
      blit = lambda i: self.view.blit(i)
    else:
      img = self.view
      blit = lambda i: 0
      self.view.clear(bg)

    w, h = img.size
    r = float(min(w, h) / 2.0 * 72.0 / 100.0)
    cx = w/2; cy = h/2 - 20

    def clearBottom():
      self.view.rectangle(((2,h-10),(w-54-PERF_CTRS,h)), bg, fill=bg)
      self.view.rectangle(((w-51,h-20),(w,h)), bg, fill=bg)

    if gps != None and gps.dataAvailable():
      loctime = gps.localtime
      gpsname = self.gps.name
    else:
      loctime = time.localtime()
      gpsname = self.settings.btdevice
    
    #------------------------------------------------------------------------
    self.drawMarkers(img)

    #------------------------------------------------------------------------
    self.cpuGraph(img)

    #------------------------------------------------------------------------
    if gps == None or not gps.dataAvailable():

      blit(img)
      if not self.gps: prnt(2, 20, u"Logging not active", large)
      else:            prnt(2, 20, u"Waiting for GPS...", large)
     
    #------------------------------------------------------------------------
    elif dispmode == DISP_NORM:
      blit(img)
      line = 0
      hl   = -self.view.measure_text(u"M", bold)[0][1] + 3
      dcol = w/3 + 10
      
      def show(label, text):
        global line
        prnt(2,    line, unicode(label+":"))
        prnt(dcol, line, unicode(text), bold)
        line += hl
   
      line += hl
      if self.log:
        prnt(2, line, os.path.basename(self.log.name()), bold); line += hl*3/2
      else:
        line += hl
      
      
      show("Latitude",  coord(gps.lat))
      show("Longitude", coord(gps.lon,"EW"))

      if gps.speed   != None: show("Speed",     "%-5.1f km/h" % gps.speed)
      if getattr(gps, "corralt", None): 
        show("Altitude",  "%-4.0f m" % gps.corralt)
      if gps.hdg     != None: show("Heading",   u"%-4.0f\u00b0" % gps.hdg)
    
      if gps.time:
        line += hl
        show("Time", time.strftime("%H:%M:%S", gps.localtime))
    
      if self.extended:
        line += hl
        if gps.hdop != None and gps.vdop != None:
          show("HDOP/VDOP", "%-.2f/%-.2f" % (gps.hdop, gps.vdop))
        if gps.hacc != None and gps.vacc != None:
          show("HACC/VACC", "%-.2f/%-.2f" % (gps.hacc, gps.vacc))
        
      if self.log:
        nt = (self.log.tracks() / 10 * 10)
        if nt < 100: nt = self.log.tracks()
        if self.started:
          dt = time.time() - self.started
          rt = "/%02d:%02d" % (int(dt/3600), (int(dt) % 3600) / 60)
        else:
          rt = ""
        show("Recorded", "%d/%.1fkm%s" % (nt, self.log.distance()/1000.0, rt))

    #------------------------------------------------------------------------
    elif dispmode == DISP_COMPASS:

      img.ellipse(((cx-r,cy-r),(cx+r,cy+r)), fg, width=2)
      
      if gps.hdg != None:
        a  = math.radians(gps.hdg)
        da = math.pi/16
        x  = int(math.sin(a) * r);     y  = int(math.cos(a) * r)
        x1 = -int(math.sin(a-da) * r); y1 = -int(math.cos(a-da) * r)
        x2 = -int(math.sin(a+da) * r); y2 = -int(math.cos(a+da) * r)
        xa = -x * 80 / 100;            ya = -y * 80 / 100
        # img.polygon(((cx+x, cy-y),(cx+x1,cy-y1),(cx+xa,cy-ya),(cx+x2,cy-y2)), 0x000000, fill=0)
        img.polygon(((cx+x, cy-y),(cx+x1,cy-y1),(cx+xa,cy-ya)), 0x007f00, fill=0x007f00)
        img.polygon(((cx+x, cy-y),(cx+xa,cy-ya),(cx+x2,cy-y2)), 0xbf0000, fill=0xbf0000)
        img.line(((cx+x, cy-y),(cx+xa,cy-ya)), bg)
        
      blit(img)
      
      
      if gps.hdg != None:
        prnt(2, 20, u"%.1f\u00b0" % gps.hdg, large)
      if getattr(gps, "corralt", None) != None:
        prnt(2, 30, u"%.1f m" % gps.corralt, small)
        
      mode, low, norm, high = self.travelmode()

      mark = None
      if self.marker: mark = self.marker[0]
      if not mark:    mark = self.fmarker
      
      if mark and mark.startswith("Speed "): mark = int(mark.split()[1])*107/100 
      else: mark = 4269

      if gps.speed != None:
        fill = fg
        if gps.speed > low:   fill = 0x7f4f00
        if gps.speed > norm:  fill = 0xbf0000
        if gps.speed > high:  fill = 0xff0000
        if gps.speed >= mark: fill = 0xff0000
        speed = u"%.1f km/h" % gps.speed
        prnt(2, h-15, speed, large, fill=fill)
      else:
        dx = 2

      dy = -self.view.measure_text(u"M", large)[0][1]
      prnt(2, h-20-dy, mode, small)

      prnt(w - 75, 10, coord(gps.lon),      small)
      prnt(w - 75, 20, coord(gps.lat,"EW"), small)
  
    #------------------------------------------------------------------------
    elif dispmode == DISP_SATGRAPH:

      if (self.settings.satupd < 0) or (int(gps.time - self.prevsat) >= self.settings.satupd):
        self.prevsat = gps.time

        self.settings.satupd = abs(self.settings.satupd)

        img.ellipse(((cx-r,cy-r),(cx+r,cy+r)), fg, width=2)
        img.line(((cx+r, cy),(cx-r,cy)), fg)
        img.line(((cx, cy-r),(cx,cy+r)), fg)
      
        msr = self.view.measure_text(u"88", small)[0]
        dx, dy = msr[2], msr[3]-msr[1]
      
        def satpos(sat): # the (relative) center of a satellite mark
          l = 1.0 - float(sat.elevation) / 90.0
          a = math.radians(sat.azimuth)
          x = int(l * math.sin(a) * r)
          y = int(l * math.cos(a) * r)
          return x, y
        
        sr = max(dx,dy) * 3 / 4 + 2 # mark radius

        if gps.sat: # draw the meter bars and mark circles
          i = 0
          for sat in gps.sat:
            if   sat.used:        fill = 0x008000
            elif sat.signal > 20: fill = 0xa06000
            else:                 fill = 0x800000
            img.rectangle(((2+i*(dx+3), h-dy-12-sat.signal/3),(2+(i+1)*(dx+3)-2, h-dy-12)), fg, fill=fill)
            x, y = satpos(sat)
            img.ellipse(((cx+x-sr,cy-y-sr),(cx+x+sr,cy-y+sr)), self.colmap["satmark"], fill=self.colmap["satmark"]) #xffffff)
            i += 1
        
        blit(img)
      
        if gps.fix:
          prnt(2, 15, u"Fix: ")
          prnt(2+2*dx, 15, u"%s" % FIXTYPES[gps.fix-1], bold)

        if gps.sat: # put labels inside the mark circles
          i = 0
          for sat in gps.sat:
            x, y = satpos(sat)
            prnt(cx+x-dx/2,cy-y+dy/2, "%02d" % sat.prn, small, fill=(sat.used and 0x00ff00) or 0xff0000)
            prnt(2+i*(dx+3),h-10, "%02d" % sat.prn, small, fill=(sat.used and 0x007f00) or 0xbf0000)
            prnt(2+i*(dx+3),h-8-2*dy-sat.signal/3, "%02d" % max(sat.signal,0), smit, fill=fg)
            i += 1
            
        else:
          prnt(2, h-10, u"No Satellite Data", fill=0xff0000, font=bold)
          
        msr = self.view.measure_text(u"M", font)[0]
        dx, dy = msr[2], msr[3]-msr[1]
        
        if gps.nsat != None:
          prnt(2, h-60, u"Used:")
          prnt(2+dx*4, h-60, u"%d" % gps.nsat, bold, fill=0x007f00)
          
        if gps.vsat != None:
          prnt(w-60, h-60, u"Vis.:")
          prnt(w-60+3*dx, h-60, u"%d" % gps.vsat, bold)
          
        sr = 3
        if gps.hdg != None:
          a  = math.radians(gps.hdg)
          da = math.pi/16
          x  = int(math.sin(a) * r);     y  = int(math.cos(a) * r)
          self.view.ellipse(((cx+x-sr,cy-y-sr),(cx+x+sr,cy-y+sr)), 0xbf0000, fill=0xbf0000)
          prnt(w-75,      15, u"Hdg.:")
          prnt(w-73+3*dx, 15, u"%.1f\u00b0" % gps.hdg, bold)

        if gps.speed != None:
          prnt(w-65, 30, u"Spd.: %-2.1fkm/h" % gps.speed, small)

      else: # just clear the name and time area
        clearBottom()
        self.view.blit(img, source=(w-PERF_CTRS-55, h-22, w-55, h),
                            target=(w-PERF_CTRS-55, h-22))

    #----------------------------------------------------------------------
    elif dispmode == DISP_LANDMARK and self.lmsettings.uselm:
      hl   = -self.view.measure_text(u"M", bold)[0][1] + 3
      line = hl
      ucol = w/4 - 2
      dcol = w/3 + 16
      icol = dcol - 16
      fnt, bld = font, bold
      if w < 210: font, bld = small, font
      
      def show(lm):
        global line
        wpt, svgicon = lm
        d = wpt.distance(self.gps.position)
        if d < 1000: d = "%7.f" % d; unit = "m"
        else:        d = "%7.1f" % (d / 1000); unit = "km"

        dd = self.view.measure_text(unicode(d), fnt)[0][2]
        prnt(ucol-dd-3, line, d, fnt)
        prnt(ucol,      line, unit, fnt)
        
        name = wpt.name
        try:
          cat = self.lmsettings.cat(wpt.attr["categories"][0])[0]
          if name.startswith(cat): name = name[len(cat):].strip(" -")
        except: pass
        prnt(dcol,      line, name, bld)
        line += hl
        
      def icon(lm, img):
        global line
        wpt, svgicon = lm

        try:    cat = self.lmsettings.cat(wpt.attr["categories"][0])[0]
        except: cat = None
        if cat in gpslogimg.ICONS: ico = gpslogimg.ICONS[cat]
        else:                      ico = None
        if cat == "GPS Log" and ico == None: ico = gpslogimg.ICONS["Default"]
        if ico: ico.draw(img, (icol, line-hl), (hl,hl))
        line += hl

      
      def searchThread():
        try:
          if self.nearest: return # probably still in use
          nearest = gpsloglm.NearestLm(self.gps.lat, self.gps.lon,
                                       max=h/hl, maxdist=self.lmsettings.radius*1000.0)
          self.nearest = nearest
        except:
          if DEBUG: raise
          self.nearest = []
        if cputime: self.thperf += cputime()
        
      if self.gps.lat != None and self.gps.lon != None: # may have become invalid
        if self.nearest == None:
          # thread.start_new_thread(e32.ao_callgate(searchThread), () )
          thread.start_new_thread(searchThread, () )
          # searchThread()
          e32.ao_yield()

        if self.nearest != None:
          saveline = line

          for lm in self.nearest:
            icon(lm, img)
            if line + hl > h:
              break
        
          line = saveline
          blit(img)

          for lm in self.nearest:
            show(lm)
            if line + hl > h:
              break
        else: # just clear the screen and redraw the name and time area
          clearBottom()
          self.view.blit(img, source=(w-PERF_CTRS-55, h-22, w-55, h),
                              target=(w-PERF_CTRS-55, h-22))

      else:
        blit(img)
              
      self.nearest = None

      
    prnt(2, h, gpsname, smit)
    prnt(w - 52, h-10, unicode(time.strftime("%H:%M:%S", loctime)), small)
    prnt(w - 52, h,    unicode(time.strftime("%d.%m.%Y", loctime)), small)

    if img != self.view:
      del img

  ############################################################################
  def showLandmarks(self):
    if not self.lmsettings.uselm:
      return # temporarily disabled
      
    if self.gps == None or not self.gps.dataAvailable():
      if self.view != None:
        appuifw.app.body = self.view
      return self.drawGraph()

    if not self.gps.lat or not self.gps.lon:
       return

    try:
      nearest = gpsloglm.NearestLm(self.gps.lat, self.gps.lon,
                                   max=32, maxdist=self.lmsettings.radius*1000.0)
    except:
      if DEBUG: raise
      nearest = []

    # defico = appuifw.Icon(u"Z:\\resource\\apps\\lmkui.mif", 16386, 16384)
    defico = gpsloglm.MKICON(gpsloglm.ICONS["Default"])

    entries = []

    for wpt, ico in nearest:
      d = wpt.distance(self.gps.position)
      if d < 1000: d =u"%7.fm"%d
      else:        d =u"%7.1fkm" % (d / 1000); unit = "km"
      if not self.lmsettings.smico:
        entries += [ (unicode(wpt.name), d, (ico != None and appuifw.Icon(*ico)) or defico) ]
      else:
        entries += [ (unicode(d.strip()+" "+wpt.name), (ico != None and appuifw.Icon(*ico)) or defico) ]
 
    if len(entries) == 0:
      if not self.lmsettings.smico:
        entries = [ (u"(No Landmarks)", u"", defico) ]
      else:
        entries = [ (u"(No Landmarks)", defico) ]


    if self.lbox != None and self.lbsmall != self.lmsettings.smico:
      # You cannot change the structure of an active listbox :-(
      appuifw.app.body = self.appbody
      del self.lbox
      self.lbox = None

    if self.lbox == None:
      self.lbox    = appuifw.Listbox(entries, lambda: 0)
      self.lbsmall = self.lmsettings.smico
      self.bindDefault(self.lbox)
      if not self.log:    self.lbox.bind(EKeyYes, self.start)
      else:               self.lbox.bind(EKeyYes, self.stop)
    else:
      self.lbox.set_list(entries, self.lbox.current())
    if appuifw.app.body != self.lbox:
      appuifw.app.body = self.lbox
      
  ############################################################################
  def display(self, immediately=False):
  
    if immediately  and self.dispmode() in [DISP_SATGRAPH, DISP_OFF]:
      self.settings.satupd = -abs(self.settings.satupd)

    appuifw.app.title = unicode(self.modetitle())

    if self.paused:
      appuifw.app.title += u" - Paused"

    try:
      if hasattr(self.view, "drawNow"):
        self.view.drawNow()
      elif self.dispmode() != DISP_LANDMARK or not self.lmsettings.lmico:
        if appuifw.app.body != self.view:
          appuifw.app.body = self.view
        self.drawGraph()
      else:
        self.showLandmarks()

    except Exception, exc:
      if not DEBUG: appuifw.note(u"Error displaying Data: %s" % str(exc), "error")
      if DEBUG: raise
      self.stop(display=False)

  ############################################################################
  def dispmode(self):
    return self.settings.dispmode
    
  ############################################################################
  def modetitle(self):
    return DISPMODES[self.settings.dispmode]

  ############################################################################
  def travelmode(self): 
    return TRAVELMODES[self.settings.trvlmode]

  ############################################################################
  def togglePause(self):
    if not self.gps:
      return
    mark = u""
    self.paused = not self.paused
    if self.paused: mark = u" \u221a";

    appuifw.app.menu[1] = (u"Pause" + mark, self.togglePause)
    self.display()

  ############################################################################  
  def markName(self):
    if self.marker:
      return "%s - %d" % (self.marker[0], self.markcnt)
    return ""

  ############################################################################  
  def markIn(self, no, display=True):
    if not self.gps or not self.log:
      return

    if self.marker:
      active = self.marker[0]
      self.markOut(display=False)
      if active == MARKERS[no]: # toggle
        return

    
    self.marker   = (MARKERS[no], self.gps.position)
    self.markcnt += 1

    wpt = self.log.waypoint(self.gps, name=self.markName(),
                            attr={"gpslog:mark": ({"in":"true"},self.marker[0])})
    
    if display:
      self.display(immediately=True)
    
  ############################################################################  
  def markOut(self, display=True):
    if not self.marker:
      return

    try:
      inName        = self.markName()
      self.markcnt += 1
    
      if self.gps:
        attr = {"gpslog:mark": ({"in":"false", "match":inName},self.marker[0])}
        pos = self.gps.position
        wpt = self.log.waypoint(self.gps, name=self.markName(), attr=attr)
    
        if self.lmsettings.uselm and self.lmsettings.marklm:
          tm = (self.gps.time != None and self.gps.time) or time.time()
          mark = self.marker[0]
          wpt.lat, wpt.lon = midpoint(self.marker[1], pos)
          categories = [] 
          for c in [mark, mark.split()[0]]:
            if not c in categories and c in self.lmsettings.catnames:
              categories += [c]
          categories = [ self.lmsettings.cat(c)[1] for c in categories ]
          gpsloglm.CreateLm(wpt, name=mark +  " - " + isoformat(tm), desc=mark,
                            cat=categories,
                            radius=distance(pos, self.marker[1])/2,
                            edit=self.lmsettings.lmedit)
        
      self.marker = None
      if display:
        self.display(immediately=True)

    except:
      self.marker = None
      self.stop()
      raise

  ############################################################################
  def markWaypoint(self):
    if not self.gps or not self.log:
      return

    wpt = self.log.waypoint(self.gps)
    
    if self.lmsettings.uselm and self.lmsettings.wptlm:
      desc = "%s, %s" % (os.path.basename(self.log.name()), wpt[0])
      tm = (self.gps.time != None and self.gps.time) or time.time()
      gpsloglm.CreateLm(wpt, name=isoformat(tm), desc=desc,
                        cat=self.lmsettings.wptcat, edit=self.lmsettings.lmedit)
    self.display()

  ############################################################################
  def cycleTravel(self, forward=True, set=None):
    if self.dispmode() != DISP_COMPASS:
      return
    if set != None:
      if set not in range(len(TRAVELMODES)): return
    elif forward:   set = (self.settings.trvlmode+1) % len(TRAVELMODES)
    else:           set = (self.settings.trvlmode-1) % len(TRAVELMODES)

    self.settings.trvlmode = set

  ############################################################################
  def cycleMode(self, forward=True, set=None):
    if not self.gps:
      return
    if set != None:
      if set not in range(len(DISPMODES)): return
    elif forward:   set = (self.settings.dispmode+1) % len(DISPMODES)
    else:           set = (self.settings.dispmode-1) % len(DISPMODES)

    if self.settings.dispmode == DISP_LANDMARK and not self.lmsettings.uselm:
      self.cycleMode(forward)
      
    self.settings.dispmode = set

    self.display(immediately=True)

  ############################################################################
  def colorMode(self, mode=None):
    if mode == None:
      if self.colmode == "day": self.colmode = "night"
      else:                     self.colmode = "day"
    else:
      self.colmode = mode
    self.fg, self.bg, self.colmap = DISP_COLORS[self.colmode]
    # frequently used
    self.txtalpha = self.colmap["txtalpha"]
    
    if mode == None:
      self.display(immediately=True)

  ############################################################################
  def screenMode(self, set=None):
    if set:                              mode = set
    elif appuifw.app.screen == "normal": mode = "full"
    else:                                mode = "normal"
    appuifw.app.screen = self.settings.screen = mode
    self.display(immediately=True)

  ############################################################################
  def gpsCallback(self, gps):

    if self.gpssema > 0:
      self.busy += 1
      return

    self.gpssema = 1

    try:
      if self.backlight and self.focus and self.dispmode() != DISP_OFF:
        e32.reset_inactivity()
      
      if self.paused:
        return

      try:
        if not gps.ok and not self.stopping:
          err = gps.lastError
          if err == None: err = "GPS terminated unexpectedly"
          raise SystemError, err

        gps.corralt = gps.alt
    
        if not gps.lat and not gps.lon and not gps.alt:
          self.display()
          return

        if gps.corralt != None:
          gps.corralt += self.altcorr

        self.display()
      
        if not self.log:
          return

        if not gps.dataAvailable() or not gps.lat:
          return

        if self.prevrec != None and\
           self.settings.mindist and\
           distance(gps.position, self.prevrec) < self.settings.mindist:
          self.prev = (gps.position, gps.alt) # sic!
          return
        if self.prevrec != None:
          ppos, ppalt = self.prev
          alt = gps.alt
          if alt   == None: alt = 0
          if ppalt == None: ppalt = 0
        if self.prevrec != None and\
           self.settings.maxdist != 0 and\
           ( (distance(gps.position, ppos) > self.settings.maxdist) or\
             (abs(alt-ppalt) > self.settings.maxdist / 3) ):
          self.prev    = (gps.position, gps.alt)
          self.ignored += 1
          return
        
        if self.log != None:
          self.log.format(gps, self.ignored)
      
        self.ignored = 0
        self.prevrec = gps.position
        self.prev    = (gps.position, gps.alt)

      except Exception, exc:
        if not DEBUG: appuifw.note(u"Error processing GPS: %s" % str(exc), "error")
        if DEBUG: raise
        self.stop(display=False)

    finally:
      self.gpssema = 0

  ############################################################################
  def openLog(self):
    if not os.path.exists(self.settings.logdir):
      os.makedirs(self.settings.logdir)
    name = ""
    if self.gps != None: name = self.gps.name
    if self.settings.logfmt != "OziExplorer":
      self.log = GpxLogfile(logdir=self.settings.logdir,
                            extended=self.extended, satellites=self.satellites,
                            comment=name)
    else:
      self.log = OziLogfile(logdir=self.settings.logdir,
                            extended=self.extended, comment=name)

  ############################################################################
  def closeLog(self):
    if self.log != None:
      self.markOut(display=False)
      fname = self.log.name(); n = self.log.tracks()
      self.log.close(); del self.log; self.log = None
      if n > 0 and n < DEL_THRESHOLD:
        rc = appuifw.query(u"Less than %d points recorded. Keep file?" % DEL_THRESHOLD, "query")
        if not rc:
          os.remove(fname)
                      
    self.logn = None

  ############################################################################
  def start(self):
    try:
      if self.settings.btdevice == INTERNAL_GPS:
        if PositioningProvider != None:
          self.gps = PositioningProvider()
        else:
          appuifw.note(u"Positioning failed to install! Please se the README.", "error")
          return
      elif self.settings.btdevice == LOCREQ_GPS:
        if LocationRequestorProvider != None:
          self.gps = LocationRequestorProvider()
        else:
          appuifw.note(u"LocationRequestor module not installed! Please see the README.", "error")
          return
      elif self.settings.btdevice == XMLSIM_GPS:
        if XMLSimulator != None:
          self.gps = XMLSimulator(sources=[os.path.join(self.settings.logdir,"sim","*.gpx"),os.path.join(self.settings.logdir,"sim","*.kml")])
        else:
          appuifw.note(u"XMLSimulator module not installed! Please see the README.", "error")
          return
      else:
        if NMEABluetoothProvider != None:
          self.gps = NMEABluetoothProvider(self.btaddr)
          self.btaddr = self.gps.addr
          self.settings.btaddr = unicode(repr(self.btaddr))
        else:
          appuifw.note(u"Bluetooth failed to install! Please se the README.", "error")
          return

    except SymbianError, exc:
      if exc[0]==-46: # KErrPermissionDenied
        if not DEBUG: appuifw.note(u"Permission denied. Did you sign GpsLog? See README.", "error")
      else:
        if not DEBUG: appuifw.note(u"Module failed to start. (%s)" % str(exc), "error")
      if DEBUG: raise
      return
      
    except Exception, exc:
      if not DEBUG: appuifw.note(u"Error opening GPS: %s" % str(exc), "error")
      else:         raise
      return

    if self.paused: self.togglePause()

    try:
      self.openLog()

      # self.cbcg = self.gps.registerCallback(self.gpsCallback)
      self.cbcg = self.gps.registerCallback(globalCallback) # the dreaded PANIC CONE 8
      
      self.started = time.time()

    except Exception, exc:
      if not DEBUG: appuifw.note(u"Error starting log: %s" % str(exc), "error")
      self.gps.close(); del self.gps; self.gps = None
      if DEBUG: raise
      return

  
    appuifw.app.menu[0] = (u"Stop", self.stop)
    if self.view != None: self.view.bind(EKeyYes, self.stop)
    if self.lbox != None: self.lbox.bind(EKeyYes, self.stop)
    self.display()
    
  ############################################################################
  def stop(self, display=True):
    if self.stopping: return
    appuifw.app.menu[0] = (u"(Stopping...)", self.stop)
    self.stopping = True
    self.markOut(display=False)
    if self.gps != None:
      self.gps.close(); del self.gps; self.gps = None
    self.closeLog()
    self.stopping = False
    self.markcnt  = 0
    appuifw.app.menu[0] = (u"Start", self.start)
    if self.view != None: self.view.bind(EKeyYes, self.start)
    if self.lbox != None: self.lbox.bind(EKeyYes, self.start)
    if display:
      self.display()


  ############################################################################
  def initializeSettings(self, msg="New Version. Please check your settings"):
    
    SETTINGS_VER = 7
    self.ON_OFF_SETT = ["backlight","autostart","extended","satellites","cpugraph"]
    cpuhide          = (cputime == None)
    
    DEFDESC = [
      (("backlight", "Keep Backlight On"), "combo",   [u"on", u"off"], u"off"),
      (("autostart", "Start automatically"), "combo",   [u"on", u"off"], u"off"),
      (("altcorr",   "Altitude Correction"), "text",   [], u"0"),
      (("logdir",    "Output Directory"), "text",     [], DEF_LOGDIR),
      (("logfmt",    "Log Format"), "combo",   [u"GPX", u"OziExplorer"], unicode(DEF_LOGFMT)),
      (("mindist",   "Min. Distance to record"), "number",   [], DEF_MINDIST),
      (("maxdist",   "Max. Distance per GPS interval"), "number",   [], DEF_MAXDIST),
      (("extended",  "Extended Data Format"), "combo",   [u"on", u"off"], u"on"),
      (("satellites","Log Satellites (GPX extended only)"), "combo",   [u"on", u"off"], u"on"),
      (("btdevice",  "Choose New Bluetooth Device"), "combo",   [u"on", u"off"], u"on"),
      (("cpugraph",  "Show CPU Usage", cpuhide), "combo",   [u"on", u"off"], u"on"),
      (("resetdflt", "Reset to default settings and exit"), "combo",   [u"Yes", u"No!"], u"No!"),
      (("btaddr",    "Bluetooth Address", True), "text",     [], "None"),
      (("dispmode",  "Display Mode", True), "number",   [], DISP_NORM),
      (("trvlmode",  "Travel Mode", True), "number",   [], 0),
      (("screen",    "Screen Mode", True), "text",   [], u"normal"),
      (("haspos",    "Positioning avail.", True), "number",   [], 0),
      (("hasloc",    "LocationRequestor avail.", True), "number",   [], 0),
      (("hassim",    "Simulator avail.", True), "number",   [], 0),
      (("ver",       "Setings Version", True), "number",   [], -1),
    ]

    self.settings = GpsLogSettings(DEFDESC, "gpslog.settings")
    
    wereNew = self.settings.areNew() or self.settings.ver != SETTINGS_VER

    if wereNew:
      import gpslib
      self.settings.haspos = gpslib.hasPositioning
      self.settings.hasloc = gpslib.hasLocationRequestor
      self.settings.hassim = (XMLSimulator != None)
      self.settings.ver    = SETTINGS_VER
      self.settings.save()
    
    desc = DEFDESC[:]

    gpsset = [ d for d in desc if d[0][0] == "btdevice" ][0]
    ix = desc.index(gpsset)
    gpsset = list(gpsset)
      
    if self.settings.haspos:
      gpsset[-2] += [ INTERNAL_GPS ]
      gpsset[-1] =    INTERNAL_GPS

    if self.settings.hasloc:
      gpsset[-2] += [ LOCREQ_GPS ]
      gpsset[-1] =    LOCREQ_GPS
      
    if self.settings.hassim:
      gpsset[-2] += [ XMLSIM_GPS ]
      
    desc[ix] = tuple(gpsset)

    del self.settings

    self.settings = GpsLogSettings(desc, "gpslog.settings")

    if wereNew:
      appuifw.note(unicode(msg), "conf")
      self.editSettings()

    if self.settings.dispmode > len(DISPMODES):   self.settings.dispmode = 0
    if self.settings.trvlmode > len(TRAVELMODES): self.settings.travelmode = 0

    self.lmsettings = gpsloglm.LandmarkSettings()

  ############################################################################
  def applySettings(self):
    
    for sett in self.ON_OFF_SETT:
      setattr(self, sett, getattr(self.settings, sett) == "on")

    if 0:
      self.extended  = (self.settings.extended == "on")
      self.autostart = (self.settings.autostart == "on")
      self.satellites= (self.settings.satellites== "on")
      self.backlight = (self.settings.backlight == "on")

    self.btaddr    = eval(self.settings.btaddr)
    try:    self.altcorr = int(self.settings.altcorr)
    except: self.altcorr = 0; self.settings.altcorr = u"0"
  
  ############################################################################
  def editSettings(self):
  
    orientation = appuifw.app.orientation
    appuifw.app.orientation = "portrait"

    btdevice = self.settings.btdevice
    logfmt   = self.settings.logfmt
    
    SETTINGS_HELP="""Set 'Choose New Bluetooth'
device to true, if your GPS
is out of reach.
"""

    def help():
      appuifw.popup_menu([unicode(l) for l in SETTINGS_HELP.splitlines()],
                         u"Settings Help")

    menu = [ (u"Help", help) ]
    try:
      self.settings.execute_dialog(menu=menu)
    except:
      self.settings.reset()
      self.initializeSettings(msg="Settings have been reset. (New version?)")
    
    if self.settings.settings_changed:
    
      if self.settings.resetdflt == "Yes":
        self.settings.reset()
        self.close(force=True)
        return
    
      self.applySettings()

      if self.settings.btdevice != btdevice:
        if self.settings.btdevice == "on":
          self.btaddr = None
          self.settings.btaddr = unicode(repr(self.btaddr)) # -> u'None' ;-)
          self.settings.btdevice = "off"
        if self.gps != None:
          appuifw.note(u"Please restart logging", "conf")
      if self.settings.logfmt != logfmt and self.log != None:
        appuifw.note(u"Please restart logging", "conf")
    else:
      appuifw.app.orientation = orientation

  ############################################################################
  def editLandmarkSettings(self):
    if self.lmsettings.uselm:
      self.lmsettings.execute_dialog()

  ############################################################################
  def close(self, force=False):
    if self.log != None and not force:
      if not appuifw.query(u"Logging still active. Really exit?", "query"):
        return

    self.lck.signal()

  ############################################################################
  def cleanup(self):
    for k, ctl in self.boundkeys:
      ctl.bind(k, None)
    del self.boundkeys
    appuifw.app.screen = 'normal'
    appuifw.app.focus  = None
    appuifw.app.body   = self.appbody
    self.closeLog()
    if self.gps != None:
      self.gps.close(); del self.gps; self.gps = None
    if self.view != None:
      del self.view; self.view = None
    if self.lbox != None:
      del self.lbox; self.lbox = None
    if self.cbcg != None:
      del self.cbcg; self.cbcg = None

if __name__ in ['__main__', 'editor']:
  GpsLog().run()