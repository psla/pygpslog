try:    import landmarks
except: landmarks = None
import gpslogutil

if landmarks != None:
  import os, e32, appuifw

  LANDMARK_DB = u"file://e:gpslog.ldb"
  LANDMARK_DB = None

  INF = 1e300**2 # These might not work in future python versions
  NAN = INF/INF

  ICONDIR  = r"C:\Data\Others" # (not e32.in_emulator() and str(os.path.split(appuifw.app.full_name())[0])) or "C:\Python"
  ICONFILE = unicode(os.path.join(ICONDIR,"gpsloglm_%s.mif" % appuifw.app.uid()))
  MKICON   = lambda ico: appuifw.Icon(ICONFILE, ico, ico)
  
  def findIcons(): # really: Install icons ;-)
    mydir = "." # str(os.path.split(appuifw.app.full_name())[0])
    srcicon = os.path.join(mydir, "gpsloglm.mif")
    if not os.path.exists(srcicon):
      srcicon = os.path.join(os.path.dirname(__file__), "gpsloglm.mif")
    # if e32.in_emulator(): mydir = r"C:\Python"
    import shutil
    shutil.copy2(srcicon, ICONFILE)

  findIcons()
  
  ICON_DEF = [ ("Default", 0x4000), ("GPS Log", 0x4000), ("Speed 30", 0x4002), ("Speed 50", 0x4004) ]
  ICONS    = dict([ (n, id) for n, id in ICON_DEF ])

  def OpenDb(uri=LANDMARK_DB, create=False):
    if uri != None:
      raise NotImplementedError, "It doesn't make sense anyway. Use Categories!"
    else:
      return landmarks.OpenDefaultDatabase()

  def CreateCat(name, icon=None):
    c   = landmarks.CreateLandmarkCategory()
    c.SetCategoryName(unicode(name))
    if icon != None and type(icon) != tuple:
      icon = (ICONFILE, ICONS[icon], ICONS[icon])
    if icon != None:
      c.SetIcon(*icon)
    db  = OpenDb()
    cm  = db.CreateCategoryManager()
    id  = cm.AddCategory(c)
    c.Close(); cm.Close(); db.Close()
      
  def CreateLm(wpt, name=None, desc=None, cat=[], edit=False):
    if not type(cat) in [list, tuple]:
      cat = [ cat ]
    lm = landmarks.CreateLandmark()
    if name == None:
      name = wpt[0]
    lm.SetLandmarkName(unicode(name))
    if desc != None:
      lm.SetLandmarkDescription(unicode(desc))

    for c in cat:
      lm.AddCategory(c)

    db = OpenDb()
  
    if cat:
      cm = db.CreateCategoryManager()
      c  = cm.ReadCategory(cat[0])
      icon = c.GetIcon()
      if icon != None:
        lm.SetIcon(*icon)
      c.Close()
      cm.Close()
    # wpt.alt = None
    alt, hacc, vacc = [ (v != None and v) or NAN for v in (wpt.alt, wpt.hacc, wpt.vacc)]
    lm.SetPosition(wpt.lat, wpt.lon, alt, hacc, vacc)
    id = db.AddLandmark(lm)
    lm.Close()
    if id and edit:
      id = db.ShowEditDialog(id, landmarks.ELmkAll, landmarks.ELmkEditor, False)

    db.Close()
  
  def NearestLm(lat, lon, max=16, maxdist=-1.0):
    sc   = landmarks.CreateNearestCriteria(lat, lon, 0.0, False, maxdist)
    db   = OpenDb()
    srch = db.CreateSearch()
    srch.SetMaxNumOfMatches(max)
    op   = srch.StartLandmarkSearch(sc, landmarks.ENoAttribute, 0, 0)
    res  = []
    op.Execute()
    op.Close()

    if srch.NumOfMatches() > 0: # ??? see landmarks doc
      it = srch.MatchIterator()
      id = it.Next()
      while id != landmarks.KPosLmNullItemId:
        lm  = db.ReadLandmark(id)
        pos = lm.GetPosition()
        res += [ (gpslogutil.Waypoint([ lm.GetLandmarkName(), pos[0], pos[1], pos[2],
                                        None, None, None, None, None, None, None,
                                        pos[3], pos[4] ] ), lm.GetIcon()) ]
        lm.Close()
        id = it.Next()
        if max > 0 and len(res) >= max:
          break
      it.Close()

    srch.Close()
    sc.Close()
    db.Close()
    return res

  class LandmarkSettings(gpslogutil.GpsLogSettings):

    catnames = property(lambda self: [ c[0] for c in self.categories ])
    catids   = property(lambda self: [ c[1] for c in self.categories ])

    def __init__(self, _desc_list=None, _fname=None):
    
      self.__loadCat()

      wptnames = [ unicode(c[0]) for c in self.categories ]
      desc = [
        (("uselm",   "Use Landmarks", True), "number",   [], 1),
        (("wptlm",   "Store Waypoints as Landmarks"), "combo",   [u"on", u"off"], u"on"),
        (("wptcat",  "Category for Waypoints"), "combo",  wptnames , u"(None)"),
        (("lmedit",  "Edit New Landmarks"), "combo",   [u"on", u"off"], u"on"),
        (("radius",  "Landmark Search Radius (km)"), "number",   [], 10),
        (("lmico",   "Show Landmark Icons"), "combo",   [u"on", u"off"], u"on"),
        (("smico",   "Small Icons"), "combo",   [u"on", u"off"], u"on"),
      ]
      self.ONOFFS   = [ "wptlm", "lmedit", "lmico", "smico" ]
    
      gpslogutil.GpsLogSettings.__init__(self, desc, "gpsloglm.settings")
      self.__apply()

    def __apply(self):
      for attr in self.ONOFFS:
       setattr(self, attr, getattr(self, attr)  == "on")

      if self.radius == 0: self.radius = -1
      self.radius = float(self.radius)
      
      if not self.wptcat in self.catnames:
        self.wptcat = self.categories[0][0]

      self.wptcat = self.cat(self.wptcat)[1]

    def __cnvt(self):
      for attr in self.ONOFFS:
        setattr(self, attr,  (getattr(self, attr)  and "on") or "off")

      self.radius = int(self.radius)
      if self.radius < 0: self.radius = 0

      try:
        self.wptcat = self.cat(self.wptcat)[0]
      except:
        self.wptcat = self.categories[0]
    
    def __loadCat(self):
      self.categories = [ ("(None)", landmarks.KPosLmNullGlobalCategory), # :-)) == 0
                          ("(Create New)", -1) ]
      db  = OpenDb()
      cm  = db.CreateCategoryManager()
      cit = cm.CategoryIterator(landmarks.ECategorySortOrderNameAscending) # :-)))
      id  = cit.Next()
      while id != landmarks.KPosLmNullItemId: # :-))))
        cat = cm.ReadCategory(id)
        self.categories += [ (cat.GetCategoryName(), id) ]
        cat.Close()
        id = cit.Next()
      cit.Close()
      cm.Close()
      db.Close()
    
    def cat(self, idx):
      if isinstance(idx, (str, unicode)): # name as index
        return [ c for c in self.categories if unicode(c[0]) == unicode(idx)][0]
      else: # id as index
        return [ c for c in self.categories if c[1] == idx][0]

    def lmeditor(self):
      try:
        rc = e32.start_exe(ur"Z:\sys\bin\landmarks.exe", u"", True)
        if rc != 0:
          appuifw.note(u"Landmark Editor failed (%d)" % rc, "error")
        else:
          appuifw.note(u"Please close and re-open Landmark settings", "conf")
      except:
        appuifw.note(u"Cannot Start Landmark Editor", "error")
        if e32.in_emulator(): raise

        
    def addDefCat(self):
      for nm, icon in ICON_DEF[1:]:
        if not nm in self.catnames:
          CreateCat(nm, nm)
      appuifw.note(u"Please close and re-open Landmark settings", "conf")
    
    def execute_dialog(self):
      self.__init__() # Categories may have been changed by other app!
      self.__cnvt()

      menu = [
        (u"Landmark Editor", self.lmeditor),
        (u"Add Default Categories", self.addDefCat),
      ]

      oldcat = self.wptcat

      try:
        gpslogutil.GpsLogSettings.execute_dialog(self, menu)
      except:
        self.reset()
        self.__init__()
        self.save()
        appuifw.note(u"Settings have been reset (new version?)", "error")
        gpslogutil.GpsLogSettings.execute_dialog(self, menu)
        

      self.__apply()
      
      if self.wptcat == -1:
        if not self.newCategory():
          self.wptcat = oldcat
        
      self.save()

    def newCategory(self):
      while True:
        ncat = appuifw.query(u"New Category", "text", u"GPS Log")
        if ncat == None or ncat not in self.catnames:
          break
        appuifw.note(u"Category exists", "error")
      
      if ncat == None:
        return False

      body = appuifw.app.body
      exit = appuifw.app.exit_key_handler
      menu = appuifw.app.menu

      lock = e32.Ao_lock()
      self.tmp_sel = None
      try:
        en = []
        for nm, id in ICON_DEF:
          en += [ (unicode(nm), MKICON(ICONS[nm])) ]
        lb  = None
        def selected():
          self.tmp_sel = lb.current()
          lock.signal()
        lb = appuifw.Listbox(en, selected)
        if ncat in ICONS:
          idx = [ i[0] for i  in ICON_DEF ].index(ncat)
          lb.set_list(en, idx)
        appuifw.app.exit_key_handler = lock.signal
        appuifw.app.menu = [ (u"Ok", selected), (u"Cancel", lock.signal) ]
        appuifw.app.body = lb
        lock.wait()
      finally:
        appuifw.app.body = body
        appuifw.app.menu = menu
        appuifw.app.exit_key_handler = exit

      icon = None
      if self.tmp_sel != None: icon = ICON_DEF[self.tmp_sel]

      CreateCat(ncat, icon)
      
      self.wptcat = id; self.categories += [ (ncat, id) ]
      self.save()
      self.__init__()

      return True

    def save(self):
      self.__cnvt()
      gpslogutil.GpsLogSettings.save(self)
      self.__apply()


else: # landmarks == None:
  class NoLandmarkSettings(object):
    def __init__(self):
      self.uselm = False
    def save(self):
      pass

  del LandmarkSettings
  LandmarkSettings = NoLandmarkSettings


def close():
  if landmarks:
    landmarks.ReleaseLandmarkResources()
