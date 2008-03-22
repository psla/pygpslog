# -*- coding: cp850 -*-
import gpssplash; reload(gpssplash);
gpssplash.show("Initializing.")
import os, time, traceback, math, thread
import appuifw, e32, sysinfo, audio

import graphics
from   key_codes   import *

IN_EMU = e32.in_emulator()
if IN_EMU : import gpslogutil; reload(gpslogutil); del gpslogutil

gpssplash.show("Initializing..")
from   gpslogutil  import *

# DEBUG = False
gpssplash.show("Initializing...")
import gpsloglm  
if IN_EMU: reload(gpsloglm)
try:    from e32jext import cputime, battery_status, EPoweredByBattery
except: cputime, battery_status = None, None
try: import misty as miso
except:
  try: import miso
  except: miso = None

gpssplash.show("Loading Default Icons.")
import gpslogimg
if IN_EMU: reload(gpslogimg)
gpssplash.show("Loading Default Icons..")
import gpslogico
if IN_EMU: reload(gpslogico)
gpssplash.show("Loading Default Icons...")
gpslogimg.addIconModule(gpslogico)    
del gpslogico


gpssplash.show("Loading GPS modules...")
try:    from gpslib.gpspos import PositioningProvider
except: PositioningProvider = None
try:    from gpslib.gpsloc import LocationRequestorProvider
except: LocationRequestorProvider = None
try:    from gpslib.gpsnmea import NMEABluetoothProvider
except: NMEABluetoothProvider = None
if IN_EMU or os.path.isdir(os.path.join(DEF_LOGDIR, "Sim")):
  gpssplash.show("Loading Simulator...")
  if IN_EMU: import gpslib.gpssim; import gpslib.xmldata; reload(gpslib.gpssim); reload(gpslib.xmldata)
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
ALARM_SOUND     = "alarm.aac"
AVG_BUFLEN      = 120

IMG_FONT        = (not IN_EMU and "normal") or "dense" #"title" # "dense"

PERF_CTRS       = 30

WATCHDOG_TIMEOUT= 60
WATCHDOG_TICK   = 10

if not cputime: PERF_CTRS = 0
if IN_EMU:      WATCHDOG_TIMEOUT, WATCHDOG_TICK, ALARM_SOUND = 10, 5, "alarm.wav"

##############################################################################
def isdaylight(): # :-)
  return time.strftime("%H") >= MORNING and time.strftime("%H") <= EVENING

def ischarging():
  if IN_EMU:             return False
  if not battery_status: return False
  return battery_status() != EPoweredByBattery

  
if not hasattr(__builtins__, "sum"):
  def sum(seq):
    s = 0
    for e in seq: s += e
    return s

def avg(seq):
  return float(sum(seq))/len(seq)

############################################################################
alarmsnd = None

def alarmEnd(pstate, cstate, err):
  if cstate == audio.EOpen:
    alarmsnd.stop()

def alarm(snd=ALARM_SOUND, vibrate=True, snddir="."):

  if os.path.exists(os.path.join(snddir, snd)):
    global alarmsnd
    if alarmsnd == None:
      alarmsnd = audio.Sound.open(unicode(os.path.join(snddir, snd)))
      alarmsnd.set_volume(alarmsnd.max_volume())

    if alarmsnd.state() == audio.EOpen:
      alarmsnd.play(callback=alarmEnd)

  # on my E65, vibrating while charging seems to be a BAD idea!
  # so if we cannot check the charging status, forget the vibration
  if not vibrate or not miso or not battery_status: return

  def vibraThread():
    miso.vibrate(750, 100)
    
  if not ischarging() and not IN_EMU:
    thread.start_new_thread(vibraThread, () )

##############################################################################

singleton = None

def globalCallback(gps): # the dreaded CONE 8!
  if singleton:
    return singleton.gpsCallback(gps)

def globalWatchdog(): # the dreaded CONE 8!
  if singleton:
    return singleton.watchdog()

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
    self.prevlm  = 0
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
    self.lastgps = time.time()
    self.wdtimer = None
    self.dest    = None
    self.gpson   = False
    self.markers = gpslogimg.MARKERS
    self.markcat = gpslogimg.MARKERCAT
    self.prevmark= None
    self.warned  = False
    self.lmdb    = None
    self.drawing = False
    self.avgbuf  = [40] * AVG_BUFLEN

    del dummy

    self.initializeSettings()

    self.applySettings()
    
    if isdaylight():
      self.colorMode("day")
    else:
      self.colorMode("night")

    if not self.cpugraph:
      global PERF_CTRS
    #  PERF_CTRS = 0
    
    self.settings.satupd = 2
    
    self.setRedraw(now=True)

    if self.settings.btdevice == "on":
      self.btaddr = None
      self.settings.btdevice = "off"
    
    gpssplash.show("Loading User icons...")

    try:
      gpslogimg.addIcons(os.path.join(self.settings.logdir, "icons"))
      self.markers = gpslogimg.MARKERS
      self.markcat = gpslogimg.MARKERCAT
    except Exception, exc:
      appuifw.note(u"Error loading icons: %s" % str(exc), "error")
    
    if self.lmsettings.uselm:
      gpsloglm.addUserIcons(gpslogimg.ICONS)

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
        lmmenu = ( (u"Landmarks", self.editLandmarkSettings), )
        lmdisp = ( (u"Landmarks", lambda: self.cycleMode(set=DISP_LANDMARK) ), )
        lmdest = ( (u"From Landmarks", lambda: self.selectDestination(landmark=True) ), )
      else:
        lmmenu  = lmdisp = lmdest  = ()
        
      if lmmenu:
        setmenu  = (u"Settings",    ( ( u"General", self.editSettings),) + lmmenu )
      else:
        setmenu  = (u"Settings", self.editSettings)

      destmenu = ( (u"Enter Manually", self.selectDestination),
                   (u"Clear",          lambda: self.selectDestination(clear=True) ) )

      destmenu = (u"Destination", lmdest + destmenu)

      appuifw.app.menu =  [
        (u"Start",         self.start),
        (u"Pause",         self.togglePause),
        ] + [ destmenu ] + [
        (u"Display Mode",  ( ( u"Overview",   lambda: self.cycleMode(set=DISP_NORM)),
                             ( u"Compass",    lambda: self.cycleMode(set=DISP_NORM))
                           ) + lmdisp + (
                             ( u"Satellites", lambda: self.cycleMode(set=DISP_SATGRAPH)),
                             ( u"Toggle Night Mode", self.colorMode),
                             ( u"Toggle Fullscreen", self.screenMode),
                             ( u"Toggle Idle GPS",   self.toggleGps),
                           ) ),
        ] + [ setmenu ] + [
        (u"Help",          self.showHelp),
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

      self.wdtimer = e32.Ao_timer()
      self.wdtimer.after(WATCHDOG_TICK, globalWatchdog)

      self.lck.wait()

      self.stop(closeGps=True)

      self.settings.save()
      self.lmsettings.save()

      self.cleanup()
    
      if self.standalone:
        appuifw.app.set_exit()
      else:
        print "Bye!"

    finally:
      self.closeLog()
      self.stopGps()
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
     bind(EKey3,               self.cycleMode)
     bind(EKeySelect,          self.toggleGps)
     bind(EKeyLeftArrow,       lambda: self.cycleMode(forward=False))
     bind([EKey1, ord(".")],   lambda: self.cycleMode(forward=False))
     bind(EKeyBackspace,       self.togglePause)
     bind(EKeyUpArrow,         self.cycleTravel)
     bind(EKeyDownArrow,       lambda: self.cycleTravel(forward=False))
     bind(EKeyHash,            self.markWaypoint)
     bind(EKeyStar,            self.markOut)
     bind(EKey0,               self.colorMode)
     bind(EKey2,               self.screenMode)
     if DEBUG:
       bind(EKeyEdit,          self.toggleConsole)
     appuifw.app._self = self
     for key in range(EKey4, EKey9+1):
       bind(key, eval("lambda: appuifw.app._self.markIn(%d)" % (key-EKey0-4)))
     

  ############################################################################
  def toggleConsole(self):
    if appuifw.app.body != self.appbody:
      appuifw.app.body = self.appbody
    else:
      appuifw.app.body = self.view

  ############################################################################
  def handleFocus(self, focus):
    self.focus = focus
    
  ############################################################################
  def watchdog(self):
    diff = time.time() - self.lastgps
    if self.gps and self.gps.ok and diff >= WATCHDOG_TIMEOUT:
      rc = appuifw.query(u"No signal from GPS for %d s. Stop GPS and logging?" % int(diff) , "query")
      if rc:
        self.stop(closeGps=True)
      self.lastgps = time.time()
    if not self.gps or not self.gps.ok:
      self.lastgps = time.time()
    if diff >= WATCHDOG_TICK: self.display(immediately=True)
    self.wdtimer.after(WATCHDOG_TICK, globalWatchdog)

  ############################################################################
  def cpuGraph(self, img):
    if cputime == None or not self.cpugraph:
      return
    try:    cpu, tm = cputime(), time.clock() # may raise errors on some devices!
    except: return
    if self.perf == None:
      self.perf = [ (0, 0, 0.0) ] * (PERF_CTRS) # + [(cpu, tm, 100.0, 5.0)]
      return

    used, passed = cpu - self.perf[-1][0] + self.thperf, tm - self.perf[-1][1]
    self.thperf = 0.0
    if passed > 0: used = used / passed
    else:          used = 0.0
    useavg = PERF_CTRS/4
    
    # count this function
    self.perf = (self.perf + [(cpu, tm, used)])[-PERF_CTRS:]

    if img != None:
      x, my, col = 0, 20, 0x009f00
      if used >= .25:                 col = 0xa06000
      if self.busy > 0 or used >= .4: col = 0xff0000
    
      pimg = graphics.Image.new((PERF_CTRS+2, my+2))
      mask = graphics.Image.new((PERF_CTRS+2, my+2), "L")
      pimg.rectangle((0,0,PERF_CTRS+2,my), self.fg, fill=self.bg)
      mask.clear(0xc0c0c0)

      for cpu, tm, gused in self.perf:
        # make 90% look like full load
        y  = my-min(my*int(1000.0*gused)/900+1,my)-2
        pimg.line((x+1,my-2,x+1,y), col)
        x += 1

      gpslogimg.alphaText(pimg, (1,2), u"%2.f%%" % (used*100.0),
                          fill=self.fg, font=IMG_FONT, alpha=self.txtalpha, back=self.bg)
      # pimg.text((1,my-3), u"%2.f%%" % (avg*100.0), fill=self.fg, font=IMG_FONT)

      w, h = img.size
      img.blit(pimg, target=(w-PERF_CTRS-53, h-my), mask=mask)
    
      del pimg, mask

  ############################################################################
  def batteryMeter(self, img):
    if appuifw.app.screen != "full" or not self.battmeter:
      return
    w, h = img.size
    wb, hb, fg, bg = 9, 24, self.fg, self.bg
    x, y = w-5-wb, 32+hb
    batt = min(sysinfo.battery(), 100) * (hb-4) / 100 + 1
    chrg = ischarging()
    if   IN_EMU: batt = (60-time.time() % 60  ) * (hb-4)  / 60
    if   chrg:   batt = (   time.time() %  7+1) * (hb-4)  /  7 + 1
    col = 0x007f00
    if not chrg:
      if batt < (hb-4) / 2: col = 0xa06000
      if batt < (hb-4) / 4: col = 0xff0000
    img.rectangle(((x,y-hb+2),(x+wb,y)), outline=fg, fill=bg)
    img.rectangle(((x+wb/4,y-hb),(x+wb*3/4+1,y-hb+2)), outline=fg, fill=fg)
    img.rectangle(((x+1,y-batt),(x+wb-1,y-1)), outline=col, fill=col)
    for i in range(6): bar=y+2-hb+(i+1)*(hb-2)/7; img.line(((x+1,bar),(x+wb-1,bar)), fg)

  ############################################################################
  def drawMarkers(self, img, offs=0):
    w, h = img.size
    
    x    = w-64
    yico = h-84+offs
    ytxt = h-60

    if not self.gps or not self.gps.dataAvailable():
      self.fmarker = None
      return

    if self.marker and self.marker[0] in gpslogimg.ICONS:
      ico = gpslogimg.ICONS[self.marker[0]]
      ico.draw(img, pos=(x,yico), alpha=0x7f7f7f)
      x -= ico.img.size[0] + 5
     
    if self.lmsettings.uselm and self.lmsettings.warncat and\
       not self.lmsettings.lmico:
      
      try:
        nearest = gpsloglm.NearestLm(self.gps.lat, self.gps.lon,
                                     cat=self.lmsettings.warncat,
                                     max=2, maxdist=self.lmsettings.warnrad,
                                     db=self.lmdb)
        if nearest and len(nearest) > 0 and self.gps.hdg:
          i = 0
          while i < len(nearest):
            wpt = nearest[i][0]
            if wpt.hdg != None and abs(self.gps.hdg - wpt.hdg) > 45.0:
              del nearest[i]
            else:
              i += 1

      except:
        if DEBUG: raise
        nearest = None

      if nearest:
        nearest, svgico = nearest[0]
        try:    cat = self.lmsettings.cat(nearest.attr["categories"][0])[0]
        except: cat = None
        if cat in gpslogimg.ICONS: ico = gpslogimg.ICONS[cat]
        else:                      ico = gpslogimg.ICONS["Default"]
        ico.draw(img, pos=(x,yico), alpha=0xc0c0c0)
        caption = nearest.name
        if cat and caption.startswith(cat): caption = caption[len(cat):].strip(" -")
        gpslogimg.alphaText(img, (2, ytxt), caption, 
                            fill=self.fg, alpha=self.txtalpha, font=IMG_FONT, back=self.bg)
        e32.reset_inactivity()
        e32.ao_yield()
        self.fmarker = cat
        if self.prevmark != self.fmarker:
          self.alarm()
      else:
        self.fmarker = None
    else:
      self.fmarker = None

    self.prevmark = self.fmarker

    if not self.log:
      gpslogimg.alphaText(img, (2, 30), "No Logfile Open",
                          fill=0xff0000, alpha=self.txtalpha, font=IMG_FONT, back=self.bg)
      
  def setRedraw(self, now=True):
    s = (now and -1) or 1
    self.settings.satupd = s*abs(self.settings.satupd)
    if self.lmsettings.uselm:
      self.lmsettings.upd  = s*abs(self.lmsettings.upd)
    
  ############################################################################  
  def drawGraph(self, rect=None):

    if not self.view:
      return

    global line

    if rect != None:
      self.setRedraw()

    font   = self.font
    bold   = font[:2] + ( font[2] | graphics.FONT_BOLD, )
    large  = (font[0], font[1] * 5 / 3, font[2] | graphics.FONT_BOLD)
    small  = (font[0], font[1] * 3 / 4, font[2])
    smit   = (font[0], font[1] * 3 / 4, font[2] | graphics.FONT_ITALIC)
    fg, bg = self.fg, self.bg
    
    gps      = self.gps
    if gps and gps.dataAvailable():
      position = gps.position
      lat, lon = position
      hdg      = gps.hdg
    else:
      positon = lat = lon = hdg = None

    dispmode   = self.dispmode()
    fullscreen = (appuifw.app.screen == "full")
    perfc = (self.cpugraph and PERF_CTRS) or 0
    

    #------------------------------------------------------------------------
    if self.busy > 0: # TODO: warn or beep or ...
      if DEBUG: print "Busy!", self.busy, "Mode:", dispmode
      self.busy = 0

    #------------------------------------------------------------------------
    if dispmode == DISP_OFF and gps != None and gps.dataAvailable():
      if (self.settings.satupd < 0) or (int(gps.time - self.prevsat) >= self.settings.satupd):
        self.setRedraw(False)
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
      self.view.text((x, y), text, fill=fill, font=font)
      
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
    hl = -self.view.measure_text(u"M", bold)[0][1] + 3

    def clearBottom():
      hc = (fullscreen and 30) or 20
      self.view.rectangle(((2,h-10),(w-54-perfc,h)), bg, fill=bg)
      self.view.rectangle(((w-51,h-hc),(w,h)), bg, fill=bg)

    def dot(drawable, a, col=0xbf0000, sr=3):
      a  = math.radians(a)
      x  = int(math.sin(a) * r)
      y  = int(math.cos(a) * r)
      drawable.ellipse(((cx+x-sr,cy-y-sr),(cx+x+sr,cy-y+sr)), col, fill=col)
    
    if gps != None and gps.dataAvailable():
      loctime = gps.localtime
      gpsname = gps.name
    else:
      loctime = time.localtime()
      gpsname = self.settings.btdevice
    
    #------------------------------------------------------------------------
    self.drawMarkers(img, offs=(fullscreen and -10) or -1)

    #------------------------------------------------------------------------
    self.cpuGraph(img)

    #------------------------------------------------------------------------
    self.batteryMeter(img)

    #------------------------------------------------------------------------
    if gps == None or not gps.dataAvailable():

      blit(img)
      if not gps: prnt(2, 20, u"Logging not active", large)
      else:       prnt(2, 20, u"Waiting for GPS...", large)
     
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
        prnt(2, line, "No logfile!", bold); line += hl*3/2
      
      show("Latitude",  coord(lat))
      show("Longitude", coord(lon,"EW"))

      if self.log: avgspd = (self.log.distance() / (time.time() - self.log.starttime()) * 3.6)
      else:        avgspd = 0.000001

      if gps.speed   != None:            show("Speed",     u"%-5.1f km/h" % gps.speed)
      if h > 240 and self.log != None:   show("Avg. Speed",u"%-5.1f km/h" % avgspd)
      if getattr(gps, "corralt", None):  show("Altitude",  u"%-4.0f m" % gps.corralt)
      else:                              line += hl
      if hdg != None:                    show("Heading",   u"%-4.0f\u00b0" % hdg)
      else:                              line += hl
      
      if self.dest and position and position != (None,None):
        if h > 240: line += hl
        ddist = self.dest.distance(position)
        if ddist >= 1000.0: show("Destination",u"%-5.1f km" % ( ddist / 1000.0))
        else:               show("Destination",u"%-5.0f m" % ddist)
        if h > 240:
          mavg = avg(self.avgbuf)+0.000001
          show("Arrival", time.strftime("%H:%M:%S", time.localtime(gps.time + ddist / mavg * 3.6)))
        
      line += hl
      if gps.time:                       show("Time", time.strftime("%H:%M:%S", gps.localtime))
    
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
      
      if hdg != None:
        a  = math.radians(hdg)
        da = math.pi/16
        x  = int(math.sin(a) * r);     y  = int(math.cos(a) * r)
        x1 = -int(math.sin(a-da) * r); y1 = -int(math.cos(a-da) * r)
        x2 = -int(math.sin(a+da) * r); y2 = -int(math.cos(a+da) * r)
        xa = -x * 80 / 100;            ya = -y * 80 / 100
        # img.polygon(((cx+x, cy-y),(cx+x1,cy-y1),(cx+xa,cy-ya),(cx+x2,cy-y2)), 0x000000, fill=0)
        img.polygon(((cx+x, cy-y),(cx+x1,cy-y1),(cx+xa,cy-ya)), 0x007f00, fill=0x007f00)
        img.polygon(((cx+x, cy-y),(cx+xa,cy-ya),(cx+x2,cy-y2)), 0xbf0000, fill=0xbf0000)
        img.line(((cx+x, cy-y),(cx+xa,cy-ya)), bg)
        
      if self.dest != None and lat and lon:
        brg = bearing(position, (self.dest.lat, self.dest.lon))
        dot(img, brg, col=0x0000ff)
        if hdg:
          dot(img, brg-hdg, col=0xff0000)

      blit(img)
      
      
      if gps.hdg != None:
        prnt(2, 20, u"%.1f\u00b0" % gps.hdg, large)
      if getattr(gps, "corralt", None) != None:
        prnt(2, 30, u"%.1f m" % gps.corralt, small)
        
      mode, low, norm, high = self.travelmode()

      mark, warn = None, None
      if self.marker: mark = self.marker[0]
      if not mark:    mark = self.fmarker
      
      if mark and mark.startswith("Speed "):
        mark = int(mark.split()[1])*107/100 
        warn = mark*117/100 # ~ 125%
      else: mark = 4269

      if gps.speed != None:
        speed = gps.speed
        fill  = fg
        
        if warn != None and speed >= warn:
          if not self.warned:  self.alarm(); self.warned = True
        else: self.warned = False

        if speed > low:   fill = 0x7f4f00
        if speed > norm:  fill = 0xbf0000
        if speed > high:  fill = 0xff0000
        if speed >= mark: fill = 0xff0000
        speed = u"%.1f km/h" % speed
        prnt(2, h-15, speed, large, fill=fill)
        
      else:
        dx = 2

      if self.dest != None and lat and lon:
        ddist = self.dest.distance(position)
        mavg = avg(self.avgbuf)+0.000001
        if ddist >= 1000.0: fdist = u"%5.1f km" % ( ddist / 1000.0)
        else:               fdist = u"%5.0f m" % ddist
        maspd = u"%.1f km/h" % mavg
        mt  = self.view.measure_text(fdist, bold)[0]
        mts = self.view.measure_text(maspd, smit)[0]
        yd, ya, ys = cy - r - 2*mt[1], cy + r + mt[1], cy + r + mt[1]-4+mts[1]
        prnt(cx-mt[2]/2,  yd, fdist, bold)
        prnt(cx-mt[2]/2,  ya, time.strftime("%H:%M:%S", time.localtime(gps.time + ddist / mavg * 3.6)), bold)
        prnt(cx-mts[2]/2, ys, maspd, smit)

      dy = -self.view.measure_text(u"M", large)[0][1]
      prnt(2, h-20-dy, mode, small)

      prnt(w - 75, 10, coord(lat),      small)
      prnt(w - 75, 20, coord(lon,"EW"), small)
  
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
        
        if self.dest != None and lat and lon:
          brg = bearing(position, (self.dest.lat, self.dest.lon))
          dot(img, brg, col=0x0000ff)
          if hdg:
            dot(img, brg-hdg, col=0xff0000)

        blit(img)
      
        if gps.fix:
          fix = gps.fix
        else:
          if   position == None or position == (None,None): fix = 1
          elif getattr(gps, "corralt", None) == None:       fix = 2
          else:                                             fix = 3
         
        if fix != None:
          prnt(2, 15, u"Fix: ")
          prnt(2+2*dx, 15, u"%s" % FIXTYPES[fix-1], bold)

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
          
        if gps.hdg != None:
          dot(self.view, gps.hdg, col=0x008000)
          prnt(w-75,      15, u"Hdg.:")
          prnt(w-73+3*dx, 15, u"%.1f\u00b0" % gps.hdg, bold)

        if gps.speed != None:
          prnt(w-65, 30, u"Spd.: %-2.1fkm/h" % gps.speed, small)

      else: # just clear the name and time area
        clearBottom()
        self.view.blit(img, source=(w-perfc-55, h-22, w-55, h),
                            target=(w-perfc-55, h-22))

    #----------------------------------------------------------------------
    elif dispmode == DISP_LANDMARK and self.lmsettings.uselm:
      hl   = -self.view.measure_text(u"M", bold)[0][1] + 3
      smico = self.lmsettings.smico
      
      
      if smico:
        line = hl
        ucol = w/4 - 2
        dcol = w/3 + 16
        icol = dcol - 16
      else:
        hl = hl * 5 / 2
        line = hl + 2
        ucol = hl * 2
        dcol = ucol
        icol = 2
      
      fnt, bld = font, bold
      if w < 210: font, bld = small, font
      
      def show(lm):
        global line
        wpt, svgicon = lm
        d = wpt.distance(position)
        if d < 1000: d = "%7.f" % d; unit = "m"
        else:        d = "%7.1f" % (d / 1000); unit = "km"

        if not smico: line -= hl / 2
        
        dd = self.view.measure_text(unicode(d), fnt)[0][2]
        prnt(ucol-dd-3, line, d, fnt)
        prnt(ucol,      line, unit, fnt)
        
        if not smico: line += hl / 2
        
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
          max = h/hl
          if self.dest: max -= 1
          nearest = gpsloglm.NearestLm(lat, lon,
                                       max=max, maxdist=self.lmsettings.radius*1000.0,
                                       cat=self.lmsettings.dispcat,
                                       db=None) # not!: self.lmdb, different thread)
          if self.dest:
            nearest = [ (self.dest, None) ] + nearest
          self.nearest = nearest
        except:
          self.nearest = [(Waypoint(["Error in landmarks!", 0.0, 0.0]+10*[None]+[{"categories": ["GPS Log"]}]), None)]
          if DEBUG: raise
        if cputime: self.thperf += cputime()
        
      if lat != None and lon != None and self.lmsettings.dispcat != []: # may have become invalid
        if self.nearest == None:
          if (self.lmsettings.upd < 0) or (int(gps.time - self.prevlm) >= self.lmsettings.upd):
            self.prevlm  = gps.time
            self.lmsettings.upd = abs(self.lmsettings.upd)
            # thread.start_new_thread(e32.ao_callgate(searchThread), () )
            thread.start_new_thread(searchThread, () )
            # searchThread()
            e32.ao_yield()

        if self.nearest != None:
          saveline = line

          for lm in self.nearest:
            icon(lm, img)
            if line >= h - 30:
              break
        
          line = saveline
          blit(img)

          for lm in self.nearest:
            show(lm)
            if line >= h - 30:
              break
        else: # just clear the screen and redraw the name and time area
          clearBottom()
          self.view.blit(img, source=(w-perfc-55, h-22, w-55, h),
                              target=(w-perfc-55, h-22))

      else:
        blit(img)
        
        if self.lmsettings.dispcat == []:
          prnt(2, hl, u"No Categories selected", bold)
              
      self.nearest = None

      
    prnt(2, h, gpsname, smit)
    if fullscreen: prnt(w - 52, h-20, self.modetitle(), smit)
    prnt(w - 52, h-10, unicode(time.strftime("%H:%M:%S", loctime)), small)
    prnt(w - 52, h,    unicode(time.strftime("%d.%m.%Y", loctime)), small)

    if img != self.view:
      del img

    self.setRedraw(False)

  ############################################################################
  def showLandmarks(self): # show LMs as listbox, for the regular version see drawGraph

    self.cpuGraph(None)

    if not self.lmsettings.uselm or self.lmsettings.lmico in [False, "off"]:
      return # temporarily disabled
      
    gps = self.gps
    
    if gps == None or not gps.dataAvailable():
      if self.view != None:
        appuifw.app.body = self.view
      return self.drawGraph()

    if not gps.lat or not gps.lon:
       return

    if (self.lmsettings.upd > 0) and (int(gps.time - self.prevlm) < self.lmsettings.upd):
      return
      
    self.prevlm  = gps.time
    self.lmsettings.upd = abs(self.lmsettings.upd)

    try:
      nearest = gpsloglm.NearestLm(gps.lat, gps.lon,
                                   max=32, maxdist=self.lmsettings.radius*1000.0)
    except:
      if DEBUG: raise
      nearest = []

    # defico = appuifw.Icon(u"Z:\\resource\\apps\\lmkui.mif", 16386, 16384)
    defico = gpsloglm.MKICON(gpsloglm.ICONS["Default"])

    entries = []

    for wpt, ico in nearest:
      d = wpt.distance(gps.position)
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
  
    if self.drawing: return

    self.drawing = True
    
    self.setRedraw(immediately)

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
      self.stop(display=False, closeGps=True)

    self.drawing = False

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
    if self.paused:
      mark = u" \u221a";
      appuifw.app.screen = "normal"
    else:
      appuifw.app.screen = str(self.settings.screen)

    appuifw.app.menu[1] = (u"Pause" + mark, self.togglePause)
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
    # if not self.gps:
    #   return
    if set != None:
      if set not in range(len(DISPMODES)): return
    elif forward:   set = (self.settings.dispmode+1) % len(DISPMODES)
    else:           set = (self.settings.dispmode-1) % len(DISPMODES)

    self.settings.dispmode = set

    if self.settings.dispmode == DISP_LANDMARK and not self.lmsettings.uselm:
      self.cycleMode(forward)
      
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
    e32.ao_yield()
    self.display(immediately=True)

  ############################################################################  
  def markName(self):
    if self.marker:
      return "%s - %d" % (self.marker[0], self.markcnt)
    return ""

  ############################################################################  
  def markIn(self, no, display=True):
    if not self.gps or not self.log:
      appuifw.note(u"Pleas start a new logfile to enable marking!", "error")
      return

    if self.marker:
      active = self.marker[0]
      self.markOut(display=False)
      if active == self.markers[no]: # toggle
        return

    if not self.markers[no]:
      return

    self.marker   = (self.markers[no], self.gps.position)
    self.markcnt += 1

    wpt = self.log.waypoint(self.gps, name=self.markName(),
                            attr={"gpslog:mark": ({"in":"true", "directional":"true"},
                            self.marker[0])})
    
    if display:
      self.display(immediately=True)
    
  ############################################################################  
  def markOut(self, display=True, directional=True):
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
          if directional:
            wpt.hdg = int(bearing(self.marker[1], pos))
          categories = [] 
          for c in [mark, self.markcat]:
            if c and not c in categories and c in self.lmsettings.catnames:
              categories += [c]
          categories = [ self.lmsettings.cat(c)[1] for c in categories ]
          gpsloglm.CreateLm(wpt, name=mark +  " - " + isoformat(tm), desc=mark,
                            cat=categories,
                            radius=distance(pos, self.marker[1])/2,
                            edit=self.lmsettings.lmedit, fakehdg=True)
        
      self.marker = None
      if display:
        self.display(immediately=True)

    except:
      self.marker = None
      self.stop(closeGps=True)
      raise

  ############################################################################
  def markWaypoint(self):
    gps = self.gps
    if not gps:
      return
    if not self.gps.dataAvailable() or self.gps.position == (None,None):
      appuifw.note(u"No GPS data at the moment.", "error")
      return

    if self.log:
      wpt = self.log.waypoint(gps)
      desc = os.path.basename(self.log.name())
    else:
      wpt  = Waypoint(("Landmark", gps.lat,  gps.lon,  alt,  gps.time,
                                   gps.speed,gps.hdg,  gps.fix,
                                   gps.hdop, gps.vdop, gps.pdop,
                                   gps.hacc, gps.vacc, attr))
      desc = "GPS Log"
      
    if self.lmsettings.uselm and self.lmsettings.wptlm:
      desc = "%s, %s" % (desc, wpt[0])
      tm = (gps.time != None and gps.time) or time.time()
      gpsloglm.CreateLm(wpt, name=isoformat(tm), desc=desc,
                        cat=self.lmsettings.wptcat, edit=self.lmsettings.lmedit)
    self.display()

  ############################################################################
  def selectDestination(self, landmark=False, clear=False):
    if clear:
      del self.dest; self.dest = None; self.settings.dest="None"; return
    if landmark and not self.lmsettings.uselm:
      appuifw.note(u"Landmarks not installed", "error")
    if not landmark:
      rc = appuifw.multi_query(u"Latitude", u"Longitude")
      if not rc: return
      try:
        lat, lon = float(rc[0]), float(rc[1])
        assert ( -90.0 <= lat) and (lat <=  90.0) and\
               (-180.0 <= lon) and (lon <= 180.0), "Invalid!"
        wpt = Waypoint(['Destination', lat, lon])
      except:
        appuifw.note(u"Invalid Input", "error")
        raise
        return
    else:
      screen = appuifw.app.screen
      try:
        appuifw.app.screen = "normal"
        rc, id, db = gpsloglm.landmarks.ShowSelectLandmarkDialog(0)
        if rc == 0: return
        wpt, _icon = gpsloglm.ReadLmWpt(db, id)
        db.Close()
      finally:
        appuifw.app.screen = screen

    self.dest = wpt
    self.settings.dest = repr(wpt)

  ############################################################################
  def toggleGps(self):
    if self.log:
      return

    if self.gps:
      self.stopping = True
      self.stopGps(); self.gpson = False
    else:
      self.startGps()
    self.display()
    self.stopping = False

  ############################################################################
  def gpsCallback(self, gps):

    if self.gpssema > 0:
      self.busy += 1
      return

    self.lastgps = time.time()

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
      
        if not gps.dataAvailable() or not gps.position or gps.position == (None,None):
          return

        if self.dest != None and gps.speed != None:
          self.avgbuf.pop(0)
          self.avgbuf.append(int(gps.speed))

        if not self.log:
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
        logopen = (self.log != None)
        self.stop(display=False, closeGps=True)

        # The user might have missed the error message.
        if logopen:
          rc = appuifw.query(u"GPS acquisition terminated. Try to restart?", "query")
          if rc:
            self.start()
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
  def startGps(self):
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

      self.cbcg = self.gps.registerCallback(globalCallback) # the dreaded PANIC CONE 8

      if self.lmsettings.uselm:
        self.lmdb = gpsloglm.OpenDb()

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
    
  ############################################################################
  def stopGps(self):
    if self.gps:
      self.gps.close(); del self.gps; self.gps = None

    if self.lmdb != None:
      self.lmdb.Close(); del self.lmdb; self.lmdb = None
    
  ############################################################################
  def start(self):

    self.gpson = (self.gps != None)

    if self.paused: self.togglePause()

    try:
      self.openLog()

      self.started = time.time()

    except Exception, exc:
      if not DEBUG: appuifw.note(u"Error starting log: %s" % str(exc), "error")
      self.stopGps()
      if DEBUG: raise
      return

  
    if not self.gps:
      self.startGps()

    appuifw.app.menu[0] = (u"Stop", self.stop)
    if self.view != None: self.view.bind(EKeyYes, self.stop)
    if self.lbox != None: self.lbox.bind(EKeyYes, self.stop)
    self.prevsat = 0; self.lastgps = time.time()
    self.display()
    
  ############################################################################
  def stop(self, display=True, closeGps=False):
    if self.stopping: return
    appuifw.app.menu[0] = (u"(Stopping...)", self.stop)
    self.stopping = True
    try:
      self.markOut(display=False)
      if self.gps != None and (not self.gpson or closeGps):
        self.stopGps()
      self.closeLog()
    except Exception, exc:
      appuifw.note(u"Logfile closing failed: %s" % str(exc), "error")
      del self.log; self.log = None
      if DEBUG: self.stopping = False; raise

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
    self.ON_OFF_SETT = ["backlight","autostart","extended","satellites",
                        "cpugraph", "battmeter"]
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
      (("battmeter", "Show Battery Meter in Fullscreen"), "combo",   [u"on", u"off"], u"on"),
      (("resetdflt", "Reset to default settings and exit"), "combo",   [u"Yes", u"No!"], u"No!"),
      (("btaddr",    "Bluetooth Address", True), "text",     [], "None"),
      (("dispmode",  "Display Mode", True), "number",   [], DISP_NORM),
      (("trvlmode",  "Travel Mode", True), "number",   [], 0),
      (("screen",    "Screen Mode", True), "text",   [], u"normal"),
      (("dest",      "Destination", True), "text",   [], u"None"),
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

    if self.settings.dispmode > len(DISPMODES):   self.settings.dispmode   = 0
    if self.settings.trvlmode > len(TRAVELMODES): self.settings.travelmode = 0

    self.lmsettings = gpsloglm.LandmarkSettings()

    # landmarks may have gone
    if self.settings.dispmode == DISP_LANDMARK and not self.lmsettings.uselm:
      self.settings.dispmode = 0

  ############################################################################
  def applySettings(self):
    
    for sett in self.ON_OFF_SETT:
      setattr(self, sett, getattr(self.settings, sett) == "on")

    self.btaddr    = eval(self.settings.btaddr)
    try:    self.altcorr = int(self.settings.altcorr)
    except: self.altcorr = 0; self.settings.altcorr = u"0"
  
    self.dest = eval(self.settings.dest, {"NaN": gpsloglm.NAN})
    if self.dest != None:
      self.dest = Waypoint(self.dest)

  ############################################################################
  def showHelp(self):
    viewMenu = ( # Was meant to be used as a submenu
      (u"Start Log [Yes] (Green)", lambda: 0),
      (u"Start GPS [Enter]", lambda: 0),
      (u"Pause [C]", lambda: 0),
      (u"Next Page [\u2192], [3]", lambda: 0),
      (u"Prev. Page [\u2190], [1]", lambda: 0),
      (u"Create Waypoint [#]", lambda: 0),
      (u"Start Segment [4]-[9]", lambda: 0),
      (u"End Segment [*]", lambda: 0),
      (u"Toggle Night Mode [0]", lambda: 0),
      (u"Toggle Fullscreen [2]", lambda: 0),
    )
    appuifw.popup_menu([m[0] for m in viewMenu], u"Keyboard Help")
    
  ############################################################################
  def editSettings(self):
  
    orientation = appuifw.app.orientation
    appuifw.app.orientation = "portrait"

    btdevice = self.settings.btdevice
    logfmt   = self.settings.logfmt
    
    SETTINGS_HELP="""Set 'Choose New Bluetooth'
device to 'on', if your
GPS is out of reach.

'Merge GPX Tracks+Wpts'
merges all Waypoint files
in your log directory
to their track files.
"""

    def help():
      appuifw.popup_menu([unicode(l) for l in SETTINGS_HELP.splitlines()],
                         u"Settings Help")

    locks = []

    def merge():
      if self.log != None:
        appuifw.note(u"Please close your logfile first!", "error")
        return
      locks.append(e32.Ao_lock())
      mergeAllGpx(self.settings.logdir)
      locks[0].signal()

    menu = [ (u"Merge GPX Tracks+Wpts", merge), (u"Help", help) ]

    try:
      self.settings.execute_dialog(menu=menu)
      if locks: locks[0].wait() # TODO: doesn't really help
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
  def alarm(self, snd=ALARM_SOUND):
    vib = self.lmsettings.uselm and self.lmsettings.warnvib
    alarm(snd=snd, snddir=self.settings.logdir, vibrate=vib)

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
      try:    ctl.bind(k, None)
      except: pass
    del self.boundkeys
    appuifw.app.screen = 'normal'
    appuifw.app.focus  = None
    appuifw.app.body   = self.appbody
    self.closeLog()
    if self.wdtimer:
      self.wdtimer.cancel(); del self.wdtimer; self.wdtimer = None
    if self.gps != None:
      self.stopGps()
    if self.dest != None:
      del self.dest; self.dest = None
    if self.view != None:
      del self.view; self.view = None
    if self.lbox != None:
      del self.lbox; self.lbox = None
    if self.cbcg != None:
      del self.cbcg; self.cbcg = None
    if self.lmdb != None:
      self.lmdb.Close(); del self.lmdb; self.lmdb = None
    global alarmsnd
    if alarmsnd != None:
      alarmsnd.stop(); alarmsnd.close(); del alarmsnd; alarmsnd = None

if __name__ in ['__main__', 'editor']:
  GpsLog().run()
