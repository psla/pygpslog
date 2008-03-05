import sys, os, e32
from graphics import Image

try: raise Exception
except     Exception:  thisdir = os.path.dirname(sys.exc_info()[2].tb_frame.f_code.co_filename)

ICONSIZE      = (64,64)
ICONS_PER_ROW = 2
ALLICONS      = Image.open(os.path.join(thisdir, "gpsloglm.jpg"))
DEFALPHA      = [ 0x7f7f7f, 0x1f1f1f ]
ICONS         = [ "Default",  "Speed 30", "Speed 50", "Speed 60", "Speed 70",
                  "Speed 80", "Speed 100" ]
ICONS         = [ (ICONS[idx], idx) for idx in range(len(ICONS)) ]

assert len(ICONS) <= ALLICONS.size[1] / ICONSIZE[1] * ICONS_PER_ROW, \
       "Not enough icons in image file"


class GpsIcon(object):

  def __init__(self, idx):
    self.img  = Image.new(ICONSIZE)
    self.mask = Image.new(ICONSIZE,"L")
    sx, sy = ICONSIZE[0], ICONSIZE[1]
    x1, y1 = idx*2*sx % (2*ICONS_PER_ROW*sx) + sx, idx / 2 * sy
    x2, y2 = x1+sx, y1+sy
    self.img. blit(ALLICONS, source=((x1,   y1),(x2,   y2)))
    self.mask.blit(ALLICONS, source=((x1-64,y1),(x2-64,y2)))
    self.alphas = {}
    self.resized = {}
    # Pre-Cache standard sizes and alpha
    for a in DEFALPHA:
      for sz in [ ICONSIZE, (ICONSIZE[0]/2,ICONSIZE[1]/2), (ICONSIZE[0]/4,ICONSIZE[1]/4) ]:
        self.draw(None, (0,0), sz, a)
        
  def alphaMask(self, a=None, size=ICONSIZE):
    if a == None:               return self.alphas[(DEFALPHA[0],size)]
    if (a,size) in self.alphas: return self.alphas[(a,size)]
    aimg = Image.new(size, 'L')
    aimg.clear(a)
    self.alphas[(a, size)] = Image.new(size, 'L')
    self.alphas[(a, size)].clear(0);
    self.alphas[(a, size)].blit(self.mask.resize(size), mask=aimg)
    return self.alphas[(a, size)]

    
  def draw(self, drawable, pos, size=ICONSIZE, alpha=None):
    if size != ICONSIZE:
      if size in self.resized:
        img, mask = self.resized[size]
      else:
        img, mask = self.resized[size] = self.img.resize(size), self.mask.resize(size)
    else:
      img, mask = self.img, self.mask
     
    if alpha != None: mask = self.alphaMask(alpha, size)

    if drawable:
      drawable.blit(img, target=pos, mask=mask)

ICONS = dict([ (name, GpsIcon(idx)) for name, idx in ICONS ])

del ALLICONS
