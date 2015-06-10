# ABOUT #
[pygpslog](http://code.google.com/p/pygpslog/) is a GPS logger for S60
smartphones that uses Nokia's internal location and landmarks API and
thus can co-exist with other navigation applications (e.g. Nokia Maps)
running at the same time.

It's features include
  * Record data in standard [GPX](http://www.topografix.com/GPX) or [OziExplorer](http://www.oziexplorer.com/) format.
  * Easy marking of waypoints (with or without confirmation).
  * Easy marking of six different track segment types (e.g. speed limits).
  * The usual: Data view, Satellite View, Compass View...
  * Simultaneous logging and navigation (e.g. with Nokia Maps).
  * Integration with Nokia's landmarks.

But best see the [Screenshots](README#SCREENSHOTS.md) below.

# WHAT'S NEW #
Please see the [History](History.md) page.

# LICENSE #
> see [LICENSES](LICENSES.md) and [COPYING](COPYING.md)

# REQUIREMENTS #
  * A device running S60 3rd edition.
  * An internal or external GPS device.
  * Python for S60, v1.4.2 or higher. Versions 1.9.x and higher are **not** supported at this time.
> You may get it from [SourceForge](http://sourceforge.net/project/showfiles.php?group_id=154155).
> If you're new to Python on S60 it's probably better to read the
> [PyS60 Wiki](http://wiki.opensource.nokia.com/projects/PyS60) first.
  * The [LocationRequestor](http://www.iyouit.eu/portal/Software.aspx) module (**see below!**).
  * The [Landmarks](http://www.iyouit.eu/portal/Software.aspx) module (**see below!**).

  * All installation files have to be [Symbian Signed](https://www.symbiansigned.com) by yourself in order to be really useful. Please see the [DOCUMENTATION](README#INSTALLATION.md)

The LocationRequestor module above is packaged with an UID that cannot be
used for Symbian's [Open Signed](https://www.symbiansigned.com/app/page/public/openSignedOnline.do)
process. Therefore I'm making a
[re-packaged version](http://code.google.com/p/pygpslog/downloads/list?can=2&q=label%3ARecommended+LocationRequestor)
available here.

Unfortunately, the Landmarks module, as of Mar. 7, 2008, contains a
few bugs that prevent it from working with pygpslog. Until I receive word
from the authors, you may download a
[patched version](http://code.google.com/p/pygpslog/downloads/list?can=2&q=label%3ARecommended+Landmarks)
from this site.

In fact, the LocationRequestor and Landmarks modules are not _absolutely_
required to run pygpslog, but the functionality will be severely limited.
Please see [below](README#OPERATION.md).

# CONTACT #
Please leave your comments on the [Contact](Contact.md) wiki page. I will be notified by
e-mail automagically ;-)

# DOCUMENTATION #
Is in the [README](README.md). Please read the [INSTALLATION](README#INSTALLATION.md) section!

# SCREENSHOTS #
![http://pygpslog.googlecode.com/svn/trunk/doc/img/PyGpsLog-Main.jpg](http://pygpslog.googlecode.com/svn/trunk/doc/img/PyGpsLog-Main.jpg)
and
![http://pygpslog.googlecode.com/svn/trunk/doc/img/PyGpsLog-Satellite.jpg](http://pygpslog.googlecode.com/svn/trunk/doc/img/PyGpsLog-Satellite.jpg)

Some more [here](Screenshots.md).

