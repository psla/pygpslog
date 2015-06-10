# Why #
Python for S60 doesn't have the option (yet) to use S60 icon files (in
.mif or .mbm format, for you experts out there) for drawing the graphics
contained in them.

So, finding the pure text landmarks list a little bit dull, i created some
JPEG files to be displayed on the list. Unfortunately, those icons don't
really match Nokia's but so what...

The next problem is that the pre-installed icons and category names probably
don't match the names on your non-English device. So you might create your own
to match them. If somebody would send me a S60 phone in their language,
I'd even be prepared to do it for them ;-)

# How #
### The Track Segment Markers ###
You need a definition file to describe the categories for the markers. Suppose
you will have a definition file called `'myicons.def'` (the name _must_ end
with `'.def'`), that looks like this:
```
MARKERS    = [ "Offroad",  "Rough",     "Bumpy",
               "Smooth",   "Racetrack", "Runway" ]
MARKERCAT  = "Road Quality"
```

You simply create a directory `'icons'` in your log file directory (see
[SETTINGS](README#SETTINGS.md)), using your favorite S60 file manager or
Bluetooth tool, and copy the file there. Voilà!

If you don't care about icons, see [Finish the Job](#Finish_the_Job.md)!

**Note:**
  * The names are _case sensitive_.
  * The MARKERS list must have _exactly_ six elements!
  * MARKERCAT will additionally be assigned to [landmarks](README#Landmarks.md) if [installed](README#INSTALLATION.md).
  * Both MARKERS and MARKERCAT are optional, if you only want to create new icon sets.
  * If you _do not_ create your own icon set, the default icon will be used for all categories.

### The Landmarks List in PyGpsLog ###
This is still fairly simple. All you need is a JPEG or PNG file with your icons and
their transparency masks. Icons and their masks must be 64 x 64 pixels in size,
each row of the image contains two pairs of mask and icon. Masks may either be
black and white or gray scale, with white marking the opaque parts. It should
look like this:

![http://pygpslog.googlecode.com/svn/trunk/src/gpslogico.jpg](http://pygpslog.googlecode.com/svn/trunk/src/gpslogico.jpg)

There is even a little script,
[mkiconset.py](http://code.google.com/p/pygpslog/source/browse/trunk/mkiconset.py) in
the source distribution that can do this for you, but you'll probably have to
be little bit Python-literate as you'll have to change it to match your
installation. It requires to have a fairly recent version of
[ImageMagick](http://www.imagemagick.org/) installed.


You then need a definition file to describe the categories for the icons. Suppose you
name the above JPEG `'myicons.jpg'` you will have a definition file `'myicons.def'`
(the name _must_ end with `'.def'`), that looks like this:

```
ICONFILE   = "myicons.jpg"
ICONDEF    = [ "Accomodation",  "Businesses",    "Telecommunicat.",
               "Education",     "Entertainment", "Food & drink",
               "Geographical locat.", "Outdoor activities", "People",
               "Public services", "Places of worship", "Shopping",
               "Sightseeing", "Sports", "Transport", "User" ]
```

Install the two files like [above](#The_Track_Segment_Markers.md).

If you do not want to add icons to Nokia's internal landmarks database,
[Finish the Job](#Finish_the_Job.md)!

### Nokia's Landmarks Database ###
If you want to add your own categories with your own icons, things get a little bit
more complicated. Again that little script,
[mkiconset.py](http://code.google.com/p/pygpslog/source/browse/trunk/mkiconset.py), may
help you. But you have to have one of
[Nokia's S60 Platform SDKs](http://www.forum.nokia.com/info/sw.nokia.com/id/4a7149a5-95a5-4726-913a-3c6f21eb65a5/S60-SDK-0616-3.0-mr.html)
installed to convert your images to MBM or MIF format.

So suppose you've created your own MBM file, and it contains the icons and masks
starting with index `1` for the first icon, index `2` for the first mask, and so on,
then you just change your `'myicons.def'` from above to:

```
ICONFILE   = "myicons.jpg"
ICONMIF    = "myicons.mbm"
ICONDEF    = [ "Accomodation",  "Businesses",    "Telecommunicat.",
               "Education",     "Entertainment", "Food & drink",
               "Geographical locat.", "Outdoor activities", "People",
               "Public services", "Places of worship", "Shopping",
               "Sightseeing", "Sports", "Transport", "User" ]
```
And copy the `'myicons.mbm'` to your icon directory, too.

If your MBM file has shifted indices `'myicons.def'` might look like this:

```
ICONFILE   = "myicons.jpg"
ICONMIF    = "myicons.mbm"
ICONDEF    = [ "Accomodation",  "Businesses",    ("Telecommunicat.", 42, 43),
               "Education",     "Entertainment", "Food & drink",
               "Geographical locat.", "Outdoor activities", "People",
               "Public services", "Places of worship", "Shopping",
               "Sightseeing", "Sports", "Transport", ("User", 69, 70) ]
```

If you created a MIF file from SVG drawings, it might look like this:

```
ICONFILE   = "myicons.jpg"
ICONMIF    = "myicons.mif"
ICONDEF    = [ ("Airports", 0x4000),  ("Train Stations", 0x4002), ("Bus Terminals", 0x4004) ]
```

#### Finish the Job ####
Every time you change the segment markers or create a new icon set,
go to [Landmark Settings](README#Landmarks.md) and invoke
the `Options->Set Icons/Categories` menu. All non-standard categories and
their icons will be added to your Landmarks database.