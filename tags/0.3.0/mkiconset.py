import sys, os, glob

MAGICK   = r"F:\UTIL\MMedia\ImageMagick-6.3.9-Q16"
MIFCONV  = r"E:\Develop\Nokia\Symbian\9.1\S60_3rd_MR_2\Epoc32\tools\mifconv.exe"

ICONSIZE = "64x64"
MBMSIZE  = "48x48"

MK_MASK = '-fill none -bordercolor white -fuzz 10%% '\
          '-border 1x1 -draw "matte 0,0, floodfill" -shave 1x1 '\
          '-channel matte -negate -separate -geometry %s'

MK_MBM     = "-geometry %s -depth 16"
MK_MBMMASK = MK_MASK.replace("-negate", "")+" -depth 2"

os.environ["PATH"] = ";".join([MAGICK, os.environ["PATH"]])

def iconset(inpdir, outfile, mbm=None):
  imgs  = []
  masks = []


  icons = [ fn for fn in glob.glob(inpdir+"\\*") if os.path.isfile(fn) ]

  tile = "4x%d" % ((len(icons)+1) / 2)

  # create masks
  for ico in icons:
    mask = os.path.splitext(os.path.basename(ico))[0]+"_mask.png"
    print "Creating", mask
    if ico.lower()[-4:] in [".ico", ".gif"]:
      ico += '[0]'
    os.system('convert %s %s %s' % (ico, MK_MASK % ICONSIZE, mask))
    imgs   += [ mask, ico ]
    masks  += [ mask ]

  os.system('montage -density 12 -background black -geometry %s %s -quality 75 -tile %s %s' % (ICONSIZE, ' '.join(imgs), tile, outfile))

  for f in masks: os.remove(f)


  if mbm != None:
    if not os.path.exists("tmp"): os.mkdir("tmp")
  
    parname = os.path.join(".", "mkiconset.tmp")
    par = file(parname, "w")

    masks = []

    for ico in icons:
      icon = os.path.join("tmp", os.path.splitext(os.path.basename(ico))[0]+".bmp")
      mask = os.path.join("tmp", os.path.splitext(os.path.basename(ico))[0]+"_mask.bmp")
      print "Creating", icon
      os.system('convert %s %s BMP3:%s' % (ico, MK_MBMMASK % MBMSIZE, mask))
      os.system('convert %s %s BMP3:%s' % (ico, MK_MBM % MBMSIZE, icon))
      masks  += [ mask, icon ]
      print >> par, "/c12,1 %s" % icon

    par.close()
  
    os.system(MIFCONV+" "+mbm+" /f"+parname)

    for f in masks: os.remove(f)
    os.remove(parname)
  
if __name__ == "__main__":
  mbm = (len(sys.argv) > 3 and sys.argv[3]) or None
  iconset(sys.argv[1], sys.argv[2], mbm)
