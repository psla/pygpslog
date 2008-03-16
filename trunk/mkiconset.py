import sys, os, glob

MAGICK = r"F:\UTIL\MMedia\ImageMagick-6.3.9-Q16"

ICONSIZE = "64x64"

MK_MASK = '-fill none -bordercolor white -fuzz 10%% '\
          '-border 1x1 -draw "matte 0,0, floodfill" -shave 1x1 '\
          '-channel matte -negate -separate -geometry %s' % ICONSIZE

os.environ["PATH"] = ";".join([MAGICK, os.environ["PATH"]])

def iconset(inpdir, outfile):
  imgs  = []
  masks = []


  icons = [ fn for fn in glob.glob(inpdir+"\\*") if os.path.isfile(fn) ]

  tile = "4x%d" % ((len(icons)+1) / 2)

  print tile
  # create masks
  for ico in icons:
    mask = os.path.splitext(os.path.basename(ico))[0]+"_mask.png"
    print "Creating", mask
    os.system('convert %s %s %s' % (ico, MK_MASK, mask))
    imgs   += [ mask, ico ]
    masks  += [ mask ]

  os.system('montage -density 12 -background black -geometry %s %s -quality 90 -tile %s %s' % (ICONSIZE, ' '.join(imgs), tile, outfile))

  for f in masks: os.remove(f)

if __name__ == "__main__":
  iconset(sys.argv[1], sys.argv[2])
