try:    import landmarks
except: landmarks = None
import  gpslogutil

INF = 1e300**2 # These might not work in future python versions
NAN = INF/INF

if landmarks != None:
  import os, e32, appuifw
  import lmsearch

  LANDMARK_DB = u"file://e:gpslog.ldb"
  LANDMARK_DB = None

  ICONDIR  = r"C:\Data\Others" # (not e32.in_emulator() and str(os.path.split(appuifw.app.full_name())[0])) or "C:\Python"
  ICONFILE = unicode(os.path.join(ICONDIR,"gpsloglm_%s.mif" % appuifw.app.uid()))
  #MKICON   = lambda ico: appuifw.Icon(ICONFILE, ico, ico)
  MKICON   = lambda ico: appuifw.Icon(*ico)
  
  def findIcons(): # really: Install icons ;-)
    mydir = "." # str(os.path.split(appuifw.app.full_name())[0])
    srcicon = os.path.join(mydir, "gpsloglm.mif")
    if not os.path.exists(srcicon):
      srcicon = os.path.join(os.path.dirname(__file__), "gpsloglm.mif")
    # if e32.in_emulator(): mydir = r"C:\Python"
    if not os.path.exists(ICONFILE) or os.stat(srcicon).st_mtime > os.stat(ICONFILE).st_mtime:
      import shutil
      shutil.copy2(srcicon, ICONFILE)

  findIcons()
  
  ICON_DEF = [ 
    ("Default",  0x4000), ("GPS Log",  0x4000), ("Speed",     0x400A),
    ("Speed 30", 0x4002), ("Speed 50", 0x4004), ("Speed 60",  0x4006),
    ("Speed 70", 0x4008), ("Speed 80", 0x400A), ("Speed 100", 0x400C),
  ]
  ICONS    = dict([ (n, (ICONFILE, id, id)) for n, id in ICON_DEF ])

  WPT_LM_ATTR = 0x003F & ~(landmarks.EDescription)
                # landmarks.EAllAttributes &~... makes API panic (and app terminate)!
  
  waypointCache = {}

  def addUserIcons(icons):
    global ICON_DEF, ICONS
    for name in icons:
      ico = icons[name].mifIcon()
      if name not in ICONS:
        ICON_DEF += [ (name, None) ]
      if ico != None:
        ICONS[name] = ico
      elif name not in ICONS:
        ICONS[name] = (ICONFILE, ICON_DEF[0][1], ICON_DEF[0][1])

  def OpenDb(uri=LANDMARK_DB, create=False):
    if uri != None:
      raise NotImplementedError, "It doesn't make sense anyway. Use Categories!"
    else:
      return landmarks.OpenDefaultDatabase()

  def ClearCache():
    while waypointCache:
      del waypointCache[waypointCache.keys()[0]]
  
  def ReadLm(db, id):
    # no caching here: we crash on closing the cached lm's
    return db.ReadLandmark(id)
    
  def ReadPartialLm(db, id, attr=WPT_LM_ATTR, fields=[]):
    oattr, ofields = db.PartialReadParameters()
    db.SetPartialReadParameters(attr, fields)
    lm = db.ReadPartialLandmark(id)
    db.SetPartialReadParameters(oattr, ofields)
    return lm
    
  def ReadLmWpt(db, id):
    if id in waypointCache:
      return waypointCache[id]

    # lm = ReadPartialLm(db, id)
    lm = ReadLm(db, id)
    pos = lm.GetPosition()
    rad = lm.GetCoverageRadius()
    attr = { "categories": lm.GetCategories() }
    if rad != None: attr["radius"] = rad
    hdg = None
    if lm.IsPositionFieldAvailable(landmarks.EPositionFieldHeading):
      hdg = float(lm.GetPositionField(landmarks.EPositionFieldHeading))
    # HACK ALERT:  lmx format doesn't allow for import or export of heading
    elif lm.IsPositionFieldAvailable(landmarks.EPositionFieldBuildingTelephone):
      hdg = lm.GetPositionField(landmarks.EPositionFieldBuildingTelephone)
      if hdg.startswith("hdg:"): hdg = float(hdg[4:])
    wpt = (gpslogutil.Waypoint([ lm.GetLandmarkName(), pos[0], pos[1], pos[2],
                                 None, None, hdg, None, None, None, None,
                                 pos[3], pos[4], attr ] ), lm.GetIcon())
    lm.Close()
    waypointCache[id] = wpt
    return wpt

      
  def CreateCat(name, icon=None):
    c   = landmarks.CreateLandmarkCategory()
    c.SetCategoryName(unicode(name))
    if icon != None and type(icon) != tuple:
      icon = ICONS[icon]
    if icon != None:
      c.SetIcon(*icon)
    db  = OpenDb()
    cm  = db.CreateCategoryManager()
    id  = cm.AddCategory(c)
    c.Close(); cm.Close(); db.Close()
      
  def SearchLm(crit, max=-1, asWpt=False, db=None):
      
    if db != None: sdb = db
    else:          sdb = OpenDb()
    
    try:
      ids = lmsearch.Landmarks(crit).findIds(sdb)
      if not asWpt:
        res = ids
      else:
        res = [ ReadLmWpt(sdb, id) for id in ids ]
    finally:
      if db == None:
        sdb.Close()

    return res

  def SetCatIcons(name): # This version gives us a KErrLocked
    db   = OpenDb()
    cm   = db.CreateCategoryManager()
    cid  = cm.GetCategory(unicode(name))
    if cid != landmarks.KPosLmNullItemId:
      cat = cm.ReadCategory(cid)
      if cat.GlobalCategory() != landmarks.KPosLmNullItemId:
        return # ignore Global categories
      icon = cat.GetIcon()
      cat.Close()
      if icon != None:
        ids  = SearchLm(lmsearch.Category(cid), db=db)
        done = [] # dupes possible, then db is locked (though lm is closed :-( )
        for id in ids:
          if id in done: continue
          RETRY = 10
          for i in range(RETRY):
            try:
              lm = ReadLm(db, id)
              lm.SetIcon(*icon); db.UpdateLandmark(lm); lm.Close()
              done += [id]
              break
            except SymbianError, exc:
              if exc[0] != -22 or i >= RETRY-1: raise # KErrLocked
              e32.ao_sleep(0.2)
    cm.Close()
    db.Close()

  def CreateLm(wpt, name=None, desc=None, cat=[], radius=None, edit=False, fields=[], fakehdg=False):
    if not type(cat) in [list, tuple]:
      cat = [ cat ]
    lm = landmarks.CreateLandmark()
    if name == None:
      name = wpt[0]
    lm.SetLandmarkName(unicode(name))
    if desc != None:
      lm.SetLandmarkDescription(unicode(desc))
    if radius != None:
      lm.SetCoverageRadius(radius)
    for c in cat:
      if c != landmarks.KPosLmNullGlobalCategory: # :-))) You have to love it!
        lm.AddCategory(c)

    if wpt.hdg != None:
      fields += [ (landmarks.EPositionFieldHeading, str(wpt.hdg)) ]
      # HACK ALERT:  lmx format doesn't allow for import or export of heading
      if fakehdg:
        fields += [ (landmarks.EPositionFieldBuildingTelephone, "hdg:"+str(wpt.hdg)) ]

    for f in fields:
     lm.SetPositionField(f[0], unicode(f[1]))

    db = OpenDb()
  
    if cat:
      cm = db.CreateCategoryManager()
      if cat[0] != landmarks.KPosLmNullGlobalCategory: # :-)))))))
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
      screen = appuifw.app.screen
      try:
        appuifw.app.screen = "normal"
        id = db.ShowEditDialog(id, landmarks.ELmkAll, landmarks.ELmkEditor, False)
      finally:
        appuifw.app.screen = screen
      
    db.Close()
  
  def NearestLmClassic(lat, lon, max=16, maxdist=-1.0, cat=-1, db=None):
    if lat == None or lon == None:
      return []

    if cat != -1 and cat != None:
      if type(cat) not in [list, tuple]: cat = [cat]
    else: cat = []

    nrst = lmsearch.Nearest((lat, lon), maxdist, True) 

    if len(cat) != 0:
      sc = [ (nrst, lmsearch.Category(c)) for c in cat ]
    else:
      sc = [ nrst ]

    res  = SearchLm(sc, max=max, asWpt=True, db=db)

    while sc: del sc[0]

    return res

  def NearestLm(lat, lon, max=16, maxdist=-1.0, cat=-1, db=None):
    if lat == None or lon == None:
      return []

    if cat != -1 and cat != None:
      if type(cat) not in [list, tuple]: cat = [cat]
    else: cat = []

    nrst = lmsearch.Nearest((lat, lon), maxdist, True) 

    if len(cat) == 0:
      res = SearchLm(nrst, max=max, asWpt=True, db=db)

    else:
      # We want the result ordered by distance
      if db != None: sdb = db
      else:          sdb = OpenDb()


      near = lmsearch.Landmarks(nrst).findIds(db=sdb)

      if near:
        usecompost = lmsearch.Landmarks.USE_COMPOSITE
        lmsearch.Landmarks.USE_COMPOSITE = True
        sc  = [ (lmsearch.ItemIds(near), lmsearch.Category(c)) for c in cat ]
        ids = lmsearch.Landmarks(sc).findIds(db=sdb)
        ids = [ id for id in near if id in ids ]
        if max > 0: ids = ids[:max]
        res = [ ReadLmWpt(sdb, id) for id in ids ]
        del near, ids
        while sc: del sc[0]
        lmsearch.Landmarks.USE_COMPOSITE = usecompost
      else:
        res = []

      if db == None:
        sdb.Close()


    del nrst

    return res
  

  class LandmarkSettings(gpslogutil.GpsLogBaseSettings):

    catnames = property(lambda self: [ c[0] for c in self.categories ])
    catids   = property(lambda self: [ c[1] for c in self.categories ])

    ##########################################################################
    def __init__(self, _desc_list=None, _fname=None):
    
      self.__loadCat()

      wptnames = [ unicode(c[0]) for c in self.categories ]
      desc = [
        (("uselm",   "Use Landmarks", True), "number",   [], 1),
        (("wptlm",   "Store Waypoints as Landmarks"), "combo",   [u"on", u"off"], u"on"),
        (("lmedit",  "Edit New Landmarks"), "combo",   [u"on", u"off"], u"on"),
        (("wptcat",  "Category for Waypoints"), "combo",  wptnames , u"(None)"),
        (("marklm",  "Store Markers as Landmarks"), "combo",   [u"on", u"off"], u"on"),
        (("radius",  "Landmark Search Radius (km)"), "number",   [], 10),
        (("warncat", "Notify near Category"), "combo",  wptnames , u"(None)"),
        (("warnrad", "Distance for Notfication (m)"), "number",  [] , 10),
        (("warnvib", "Vibrate on Notification"), "combo",   [u"on", u"off"], u"on"),
        (("upd",     "Update interval (s)"), "number",   [], 3),
        (("smico",   "Small Icons"), "combo",   [u"on", u"off"], u"off"),
        (("lmico",   "Show Nokia Icons"), "combo",   [u"on", u"off"], u"off"),
       #(("dispcat", "Display Categories", True), "text",   [], u"[]"),
        (("dispcat", "Display Categories", True), "text",   [], u"None"),
      ]
      self.ONOFFS   = [ "wptlm", "marklm", "lmedit", "lmico", "smico", "warnvib" ]
    
      gpslogutil.GpsLogBaseSettings.__init__(self, desc, "gpsloglm.settings")
      self.__apply()
      
    ##########################################################################
    def __apply(self):
      for attr in self.ONOFFS:
       setattr(self, attr, getattr(self, attr)  == "on")

      if self.radius == 0: self.radius = -1
      self.radius = float(self.radius)
      
      if not self.wptcat in self.catnames:
        self.wptcat = self.categories[0][0]
      self.wptcat = self.cat(self.wptcat)[1]

      if not self.warncat in self.catnames:
        self.warncat = self.categories[0][0]
      self.warncat = self.cat(self.warncat)[1]

      self.dispcat = eval(self.dispcat)
      # kill removed categories
      if self.dispcat != None:
        self.dispcat = [ c[1] for c in self.categories if c[1] in self.dispcat]

    ##########################################################################
    def __cnvt(self):
      for attr in self.ONOFFS:
        setattr(self, attr,  (getattr(self, attr)  and "on") or "off")

      self.radius = int(self.radius)
      if self.radius < 0: self.radius = 0

      try:
        self.wptcat = self.cat(self.wptcat)[0]
      except:
        self.wptcat = self.categories[0]
    
      try:
        self.warncat = self.cat(self.warncat)[0]
      except:
        self.warncat = self.categories[0]
      
      self.dispcat = unicode(repr(self.dispcat))

      self.upd = abs(self.upd)

    ##########################################################################
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
    
    ##########################################################################
    def cat(self, idx):
      if isinstance(idx, (str, unicode)): # name as index
        return [ c for c in self.categories if unicode(c[0]) == unicode(idx)][0]
      else: # id as index
        return [ c for c in self.categories if c[1] == idx][0]

    ##########################################################################
    def lmeditor(self):
      screen = appuifw.app.screen
      try:
        appuifw.app.screen = "normal"
        rc, id, db = landmarks.ShowSelectLandmarkDialog(landmarks.KPosLmNullItemId)
        if rc == 0: return
        db.ShowEditDialog(id, landmarks.ELmkAll, landmarks.ELmkEditor, True)
        db.Close()
      finally:
        appuifw.app.screen = screen
      
    ##########################################################################
    def showcat(self):
      # we're in execute_dialog i.e. we're in unicode world now!
      # and, 'None' means all, '[]' means None ;-)
      dispcat = eval(self.dispcat)
      allcat    = self.categories[2:]
      if dispcat != None:
        choicecat = [ c for c in allcat if not c[1] in dispcat ]
        choicecat.sort()
        if len(choicecat) == 0: # something happened...
          dispcat = None;  self.dispcat = "None"

      if dispcat == None:
        appuifw.note(u"All categories already displayed", "error")
        return
      
      choices = [ unicode(c[0]) for c in choicecat ]
      sel = appuifw.multi_selection_list(choices, style="checkbox", search_field=True)
      if not sel: return # Cancel
      
      dispcat += [ choicecat[c][1] for c in sel ]
      if len(dispcat) == len(allcat): dispcat = None
      self.dispcat = str(repr(dispcat))

    ##########################################################################
    def hidecat(self):
      # we're in execute_dialog i.e. we're in unicode world now!
      dispcat = eval(self.dispcat)
      if dispcat == []:
        appuifw.note(u"No categories displayed", "error")
        return
      if dispcat == None:
        dispcat = [ c[1] for c in self.categories[2:]]

      choicecat = [ c for c in self.categories if c[1] in dispcat]
      choicecat.sort()

      choices = [ unicode(c[0]) for c in choicecat ]
      sel = appuifw.multi_selection_list(choices, style="checkbox", search_field=True)
      if not sel: return # Cancel

      hidden = [ choicecat[c][1] for c in sel ]
      rest = [ c for c in dispcat if not c in hidden ]
      rest.sort()
      self.dispcat = str(repr(rest))

    ##########################################################################
    def addDefCat(self):
      prog = gpslogutil.ProgressDialog()
      prog.show()
      tot = len(ICON_DEF)-1; i = 1
      try:
        for nm, icon in ICON_DEF[1:]:
          prog.text = nm; prog.progress = i * 100 / tot; i += 1
          if not nm in self.catnames:
            CreateCat(nm, nm)
          if nm != "Speed": # sorry for the special case
            SetCatIcons(nm)
      except Exception, exc:
        prog.hide()
        appuifw.note(u"An error occurred: %s" % str(exc), "error")
        
      del prog

      self.__loadCat()
      appuifw.note(u"Please close and re-open Landmark settings", "conf")
    
    ##########################################################################
    def execute_dialog(self):
      self.uselm = False
      try:
        self.__init__() # Categories may have been changed by other app!
        self.__cnvt()

        menu = [
          (u"Landmark Editor", self.lmeditor),
          (u"Add Display Categories", self.showcat),
          (u"Remove Disp. Categories", self.hidecat),
          (u"Set Icons/Categories", self.addDefCat),
        ]
        #if e32.in_emulator() or __file__.lower() == r"e:\python\gpslog\gpsloglm.py":
        #  menu += [
        #  ]

        oldcat  = self.wptcat
        oldwarn = self.warncat

        try:
          gpslogutil.GpsLogBaseSettings.execute_dialog(self, menu)
        except:
          if e32.in_emulator(): raise
          self.reset()
          self.__init__()
          self.save()
          appuifw.note(u"Settings have been reset (new version?)", "error")
          gpslogutil.GpsLogBaseSettings.execute_dialog(self, menu)
        
        if self.lmico == "on":
          rc = appuifw.query(u"Icons are an experimental feature! Enable?", "query")
          if not rc: self.lmico = "off"
            
        self.__apply()
      
        if self.wptcat == -1:
          if not self.newCategory():
            self.wptcat = oldcat
        elif self.warncat == -1:
          if not self.newCategory(wptcat=False):
            self.warncat = oldwarn
        
        self.save()
      finally:
        self.uselm = True

    ##########################################################################
    def newCategory(self, wptcat=True):
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
      
      if wptcat: self.wptcat  = id
      else:      self.warncat = id
      self.categories += [ (ncat, id) ]
      self.save()
      self.__init__()

      return True

    ##########################################################################
    def save(self):
      self.__cnvt()
      gpslogutil.GpsLogBaseSettings.save(self)
      self.__apply()


else: # landmarks == None:
  class NoLandmarkSettings(object):
    def __init__(self):
      self.uselm = False
    def save(self):
      pass

  LandmarkSettings = NoLandmarkSettings


def close():
  if landmarks:
    ClearCache()
    landmarks.ReleaseLandmarkResources()
