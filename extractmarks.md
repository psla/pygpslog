# extractmarks.py #

In the source distribution, you'll find the
[extractmarks.py](http://code.google.com/p/pygpslog/source/browse/trunk/tools/extractmarks.py)
utility ([download link](http://pygpslog.googlecode.com/svn/trunk/tools/extractmarks.py)).

This tool can help you to manage your recorded track segments from your [GPX](README#GPX.md)
log files.

```
usage: extractmarks <input>... [options]

options:
  -h, --help            show this help message and exit
  -o OUTFILE, --outfile=OUTFILE, --gpx=OUTFILE
  -l LANDMARKS, --landmarks=LANDMARKS, --lmx=LANDMARKS
  -m MAXRAD, --maxrad=MAXRAD
                        maximum coverage radius
  -b, --makebidi        Make two directional landmarks from non-directional
                        marks
```

So what I'm doing, is to run `extractmarks.py` on all newly recorded [GPX](README#GPX.md)
files like this:
```
extractmarks.py inp/new/GpsLog-*.gpx -o segments/Segments-YYMMDD.gpx
```

After that, I edit the file with
[any decent](http://notepad-plus.sourceforge.net) text or XML editor,
giving the segments proper names, or deleting the `'directional'` attribute
from the first trackpoint where appropriate.

When I'm satisfied (e.g. by viewing the [GPX](README#GPX.md) file in
[Google Earth](http://earth.google.com)), I'll run `extractmarks.py` again:
```
extractmarks.py segments/Segments-*.gpx -o segments/Collection.gpx -m 500 --lmx=segments/Collection.lmx
```

This collects all my edited files and put's them into a single collection
(which I usually convert to KML, using [GPSBabel](README#GPSBabel.md)).
This also creates a `Collection.lmx` file which I'll send back to my device,
replacing the (coarse) recorded landmarks. The `-m 500` option tells
`extractmarks.py` to split all large segments into smaller ones with a maximum
radius of 500 m.

After that, I'll run PyGpsLog, call the [Set Icon/Categories](README#Landmarks.md) menu
and got all my track segments and their icons in my landmark collection.

For this tool to work, you need to have Python with
[cElementTree](http://effbot.org/zone/celementtree.htm) (standard from 2.5 on)
or [ElementTree](http://effbot.org/zone/element-index.htm) (though not tested),
installed.