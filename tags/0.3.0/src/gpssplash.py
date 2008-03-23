import appuifw, os, e32, graphics

if os.path.exists(os.path.join(os.path.dirname(__file__), "gpslog.jpg")):
  IMGFILE = os.path.join(os.path.dirname(__file__), "gpslog.jpg")
else:
  IMGFILE = (e32.in_emulator() and r"C:\python\gpslog.jpg") or "gpslog.jpg"

__appbody = appuifw.app.body
__splash  = None
__img     = None
__msg     = None

def __draw(rect=None):
  if __splash and __img:
    __splash.clear(0)
    w, h   = __splash.size
    wi, hi = __img.size
    x, y = (w/2-wi/2, h/2-hi/2-15)    # sic!
    __splash.blit(__img, target=(x, y))
    if __msg:
      msr = __splash.measure_text(__msg, font="normal")[0]
      dx, dy = msr[2], msr[3]-msr[1]
      __splash.text((w/2-dx/2, h-dy-2), __msg, fill=0xffffff, font="normal")

def show(msg="Loading..."):
  # appuifw.app.body.set(u"Loading...")
  global __splash, __img, __msg
  __msg = unicode(msg)
  if not __splash:
    __splash = appuifw.Canvas(__draw)
    r = min(__splash.size[0],__splash.size[1])*2/3
    try:    img = graphics.Image.open(IMGFILE)
    except: img = graphics.Image.new((r,r)); img.clear(0)
    __img    = img.resize((r,r), keepaspect=True)
    appuifw.app.body = __splash
    del img
  __draw()
  e32.reset_inactivity()
  e32.ao_yield()
  # e32.ao_yield()
  

def hide():
  # appuifw.app.body.set(u"")
  global __splash, __img
  if __img:
    del __img
    __img = None
    
  if __splash:
    appuifw.app.body = __appbody
    del __splash
    __splash = None

  e32.reset_inactivity()
  e32.ao_yield()

def savedBody():
  return __appbody
