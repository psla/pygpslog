import landmarks

import time
from e32jext import cputime 
clock = time.clock

def lap(lbl="Time"):
  global clk
  stop = clock() - clk
  print lbl, "%.5f" % stop
  clk = clock()


class Criterion(object):
  def get(self):
    raise NotImplementedError, "This is an abstract base class"
    
class Nearest(Criterion):
  def __init__(self, pos, maxdist=-1.0, usecov=False):
    if len(pos) < 3: pos += (0.0,)
    self.pos = pos
    self.maxdist = maxdist
    self.usecov  = usecov
    
  def get(self):
    lat, lon, alt = self.pos
    return landmarks.CreateNearestCriteria(lat, lon, alt, self.usecov, self.maxdist)

class Category(Criterion):
  def __init__(self, cat):
    self.id, self.glbl, self.name = 0, 0, ""
    if   isinstance(cat, (str, unicode)):
      self.name = unicode(cat)
    elif cat >= 3000 and cat % 1000 == 0:
      self.glbl = cat
    else:
      self.id   = cat

  def get(self):
    return landmarks.CreateCategoryCriteria(self.id, self.glbl, self.name)

class ItemIds(Criterion):
  def __init__(self, ids):
    assert ids, "List cannot be empty"
    self.ids = ids
    
  def get(self):
    return landmarks.CreateIdListCriteria(self.ids)

class Landmarks(object):
  # (No docstrings to save S60 space ;-) )
  # usage: 
  #  search = Landmarks(criteria)
  #  ids    = search.findIds()
  #  lms    = search.find()
  #
  # criteria:
  #  Criterion                       # single
  #  [ Criteria, Criteria, ... ]     # 'or' combined list of 'and' combined
                                     # lists or single criterions

  NONE = landmarks.ECategorySortOrderNone
  ASC  = landmarks.ECategorySortOrderNameAscending
  DESC = landmarks.ECategorySortOrderNameDescending
  
  USE_COMPOSITE = False

  def __init__(self, criteria=None):
    self.crit  = criteria

    if self.crit != None  and type(self.crit) not in [list, tuple]:
      self.crit = [self.crit]
    
  def findTerm(self, term, db, max=-1, by=landmarks.ENoAttribute, order=ASC):
  
    if type(term) not in [list, tuple]: term = [ term ]
    
    if len(term) == 0: return []

    srch     = db.CreateSearch()
    prevOnly = False
    criteria = [ cr.get() for cr in term ]
    

    for i in range(len(criteria)):
      if max != -1 and i == len(criteria)-1: srch.SetMaxNumOfMatches(max)
      op = srch.StartLandmarkSearch(criteria[i], by, order, prevOnly)
      op.Execute(); op.Close()
      prevOnly = True
      numres = srch.NumOfMatches()
      if numres == 0:
        break

    if numres > 0:
      res = srch.MatchIterator().GetItemIds(0, numres)
    else:
      res = []
      
    srch.Close()
    while criteria: sc = criteria.pop(0); sc.Close()
    
    return res
      
  def findTermComposite(self, term, db, max=-1, by=landmarks.ENoAttribute, order=ASC):

    if type(term) in [list, tuple] and len(term) == 1: term = term[0]
    if type(term) not in [list, tuple]:
      cpst = None
      sc   = term.get()
    else:
      if len(term) == 0: return []
      cpst = [ cr.get() for cr in term ]
      sc   = landmarks.CreateCompositeCriteria(landmarks.ECompositionAND, cpst)

    srch = db.CreateSearch()

    if max != -1: srch.SetMaxNumOfMatches(max)

    op   = srch.StartLandmarkSearch(sc, by, order, False)
    op.Execute(); op.Close()
    numres = srch.NumOfMatches()
    if numres > 0:
      res = srch.MatchIterator().GetItemIds(0, numres)
    else:
      res = []

    sc.Close();  del sc
    if cpst:
      while cpst: sc = cpst.pop(0); sc.Close(); 
    if srch: srch.Close(); del srch

    return res

  def findIds(self, db=None, max=-1,  by=landmarks.ENoAttribute, order=ASC):

    if db == None: sdb = landmarks.OpenDefaultDatabase()
    else:          sdb = db

    res = []

    try:
      if self.crit != None:
        for term in self.crit:
          mx = (max != -1 and max - len(res)) or -1
          # Seems like compsite criteria aren't that smart after all...
          findfunc = (Landmarks.USE_COMPOSITE and self.findTermComposite) or self.findTerm
          res += [ id for id in findfunc(term, sdb, mx, by, order) if id not in res ]
          if max != -1 and len(res) >= max:
            break
      else:
        it = db.LandmarkIterator(by, order)
        res = it.GetItemIds(0, it.NumOfItems())
        it.Close()
    finally:
      if db == None:
        sdb.Close()
      
    return res

  def find(self, db=None, max=-1,  by=landmarks.ENoAttribute, order=ASC, partial=None):
    if db == None: sdb = landmarks.OpenDefaultDatabase()
    else:          sdb = db

    try:
      ids = self.findIds(db=db, max=max, by=by, order=order)
      res = [ self.__readlm(db, id, partial) for id in ids ]
      
    finally:
      if db == None:
        sdb.Close()
    
    return res

  def __readlm(self, db, id, partial=None):
    if partial != None:
      oattr, ofields = db.PartialReadParameters()
      db.SetPartialReadParameters(*partial)
      lm = db.ReadPartialLandmark(id)
      db.SetPartialReadParameters(oattr, ofields)
      return lm
    else:
      return db.ReadLandmark(id)

class Categories(object):
  NONE = landmarks.ECategorySortOrderNone
  ASC  = landmarks.ECategorySortOrderNameAscending
  DESC = landmarks.ECategorySortOrderNameDescending
  
