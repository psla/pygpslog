## CONTENTS ##
  1. [ABOUT](#ABOUT.md)
  1. [WHAT'S NEW](#WHAT_S_NEW.md)
  1. [LICENSE](#LICENSE.md)
  1. [REQUIREMENTS](#REQUIREMENTS.md)
  1. [CONTACT](#CONTACT.md)
  1. [INSTALLATION](#INSTALLATION.md)
  1. [OPERATION](#OPERATION.md)
    1. [Location Requestor](#Location_Requestor.md)
    1. [Generic NMEA over Bluetooth](#Generic_NMEA_over_Bluetooth.md)
    1. [Nokia Positioning](#Nokia_Positioning.md)
  1. [USAGE](#USAGE.md)
    1. [Logging](#Logging.md)
    1. [Waypoints](#Waypoints.md)
    1. [Track Segments](#Track_Segments.md)
    1. [Display Modes](#Display_Modes.md)
    1. [Destination](#Destination.md)
  1. [SETTINGS](#SETTINGS.md)
    1. [General](#General.md)
    1. [Landmarks](#Landmarks.md)
  1. [TROUBLESHOOTING](#TROUBLESHOOTING.md)
    1. [Known Problems](#Known_Problems.md)
    1. [FAQ](#FAQ.md)
  1. [SCREENSHOTS](#SCREENSHOTS.md)
  1. [ACKNOWLEDGEMENTS](#ACKNOWLEDGEMENTS.md)

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

# INSTALLATION #
  1. Install Python for S60 from [SourceForge](http://sourceforge.net/project/showfiles.php?group_id=154155).
  1. If any old version of the LocationRequestor or Landmarks modules are installed, please uninstall them
  1. Get the [LocationRequestor](http://code.google.com/p/pygpslog/downloads/list?can=2&q=label%3ARecommended+LocationRequestor) module.
  1. Get the [Landmarks](http://code.google.com/p/pygpslog/downloads/list?can=2&q=label%3ARecommended+Landmarks) module.
  1. Get the [latest version](http://code.google.com/p/pygpslog/downloads/list?q=label:Featured) of pygpslog.
  1. If you're not yet, make yourself familiar with [Symbian Signed](https://www.symbiansigned.com). The easiest way by now seems to be [Open Signed Online](https://www.symbiansigned.com/app/page/public/openSignedOnline.do).
  1. Sign LocationRequestor, Landmarks and PyGpsLog. The capabilities required are `ReadUserData, WriteUserData, NetworkServices, LocalServices, UserEnvironment, ReadDeviceData, WriteDeviceData, Location` and `SwEvent`. See SymbianSigned.
  1. Install to your device
  1. Done!

Almost: I'd strongly recommend you to download, sign, and install those additional modules:
  * [e32jext](http://code.google.com/p/pygpslog/downloads/list?can=2&q=label%3ARecommended+e32jext) from this site.
  * [envy](http://prdownloads.sourceforge.net/pyed/envy_3rd_1_0_4_unsigned.sis?download). Read [this post](http://discussion.forum.nokia.com/forum/showthread.php?t=122897&highlight=envy) for a description.
  * [uikludges](http://uikludges.googlecode.com/svn/trunk/uikludges.SIS) from http://code.google.com/p/uikludges/.
  * [miso](http://pdis.hiit.fi/pdis/download/miso/miso-1.92-s60_3rd_dev.sis) from http://pdis.hiit.fi/pdis/download/miso/ or [misty](http://cyke64.googlepages.com/misty150_unsigned_dev_certfree.SIS) from http://cyke64.googlepages.com/.
> These modules give you additional features like a CPU graph, more meaningful dialog menus, vibrating alarm and prevent pygpslog from being accidentally closed by pressing the red key.

I know the signing process is tedious, but this application requires `Location`
capabilities (`SwEvent` might be needed later). To make things worse,
Symbian Signed seems to be in the process of changing their signing procedures.
As of now (Mar. 7, 2008) you're not able to get your own developer certificate
without a valid Publisher ID. But please check yourself at
[Symbian Signed](https://www.symbiansigned.com).

In the meantime I'll try to keep some SymbianSigned instructions [updated](SymbianSigned.md).
Please feel free to comment and contribute.

If you _absolutely_ want to avoid Symbian Signed _and_ you have and _external
Bluetooth_ GPS device, you may skip the installation of LocationRequestor and
Landmarks. In this case _you will not be able_ to share the GPS device
with other applications, and, you cannot use your phone's landmarks in any
way.

# OPERATION #
pygpslog can operate in three different modes. Each mode has it's advantages
and disadvantages. The default mode depends on what you installed during
the [installation process](#INSTALLATION.md).

### Location Requestor ###
(Preferred method, uses 3rd Party Python module)
#### Pro's: ####
  * GPS can be shared with other applications.
  * Very extensive data available.
  * Works with external or internal GPS devices.
  * Continues to work, even if Bluetooth connection is lost.
#### Con's: ####
  * Requires the [LocationRequestor](http://www.iyouit.eu/portal/Software.aspx) module.
  * Must be Symbian signed

### Generic NMEA over Bluetooth ###
#### Pro's: ####
  * Most extensive (and probably precise) data available.
  * Can be used without Symbian Signed.
  * No additional modules required.
#### Con's ####
  * Requires an external Bluetooth GPS.
  * GPS cannot be shared with Nokia Maps, Navigator, mgMaps or others.

### Nokia Positioning ###
(uses standard Python module)
#### Pro's: ####
  * GPS can be shared with other applications.
  * Works with external or internal GPS devices.
  * No additional modules required.
#### Con's: ####
  * Severely limited data (no satellite info, ...).
  * Must be Symbian signed.

# USAGE #

### Logging ###
The `'Yes'` (Green) key starts and stops the GPS logger. Every restart
creates a new log file in the [configured](#SETTINGS.md) data directory (default:
`C:\Data\GpsLog` or `E:\Data\GpsLog`).

The `'C'` (Backspace) key pauses the logging operation.

Logging can be started automatically on program startup (see [SETTINGS](#SETTINGS.md)).

PyGpsLog can store it's log files in two different formats:
##### GPX #####
[GPX](http://www.topografix.com/GPX) is a format used by a
[lot of devices and applications](http://www.topografix.com/gpx_resources.asp), including
[GoogleEarth](http://earth.google.com), and can be easily manipulated.
Additionally, PyGpsLog uses it's [own extensions](Screenshots#Extended_Format.md)
to store additional data for later analysis.

##### OziExplorer #####
[OziExplorer](http://www.oziexplorer.com/) is a powerful GPS mapping software. The format
used for their `.plt` track files is very compact and by
[far enough](Screenshots#OziExplorer.md) to store basic trackpoint data.

So, if you're low on memory use this format.

##### GPSBabel #####
One word for [GPSBabel](http://www.gpsbabel.org/): Depending on the information you need,
it doesn't really matter which format you use. You can alway use
[GPSBabel](http://www.gpsbabel.org/) to convert from one format into almost any other.

From [version 1.3.5 beta](http://www.gpsbabel.org/downloads.html) on, GPSBabel can
create Nokia LMX landmark files that can be sent via Bluetooth to your device. So I'm
using it to create my Landmarks in GoogleEarth, convert them to LMX and send them
to my E65.

### Waypoints ###
The `'#'` key inserts a waypoint into the log file.
For both, [GPX](#GPX.md) and [OziExplorer](#OziExplorer.md) formats, a separate log file
is created that holds the marked waypoints. The files are named
`'<Logfile>-wpt.gpx'` and `'<Logfile>.wpt'` respectively.

For [GPX](#GPX.md) files [there's an option](#General.md) to merge the track- and
waypoint-logfiles into a single file. This is done on request only, because
according to [GPX](#GPX.md)-syntax, waypoints have to appear before tracks, and
re-writing a large log file takes _considerable_ time on device
(see [this issue](http://code.google.com/p/pygpslog/issues/detail?id=4)).

If the Landmarks module is [installed](#INSTALLATION.md), and the option is
[activated](#Landmarks.md), a Nokia landmark with the current time stamp
is added.

### Track Segments ###
There are six different segment-marker categories. Their default names are:
`"Speed 30", "Speed 50", "Speed 60", "Speed 70", "Speed 80"` and `"Speed 100"`.

If you want to configure these markers yourself, please read about UserIcons.

The segments are activated by pressing one of the number keys from `'4'` to `'9'`.
To end a segment press the same key again or press the '`*'`-key.

If you press a different key from `'4'` to `'9'` while a segment is active,
the current segment will be closed and a new segment opened.

If the Landmarks module is [installed](#INSTALLATION.md), and the option is
[activated](#Landmarks.md), a Nokia landmark is added, that marks the
center between the start and the end of the segment, has a coverage
radius of half the distance and intersects the end points.

By default these landmarks are directional, i.e. notifications only take
place if you're going roughly in the same direction as the landmark.
If you want to change this, you have to save your tracks in GPX format,
[extract and edit](extractmarks.md) the segments and then write the landmarks
back to the device.

### Display Modes ###
To save battery, information display is usually only active if logging is switched on.

You can switch on GPS information in idle mode by pressing the `'Select'` key (or
`'Enter'` key, joystick button).

The left and right arrow key or the `'1'` and `'3'` keys switch back and forth
between the different modes.
  1. Overview - Log File Name and General GPS
  1. Compass and Speed
  1. Landmarks (if [installed](#INSTALLATION.md))
  1. Satellite View
  1. Power saving mode (log file writing only)

The `'2'` key switches the application in full screen mode. This especially
useful in night mode.

Night and day mode can be toggled with the `'0'` key. Night mode will
be automatically active the the application is started after 7pm or before
5am (should be 9am, but never mind ;-) )

The `'C'` (Backspace) key also freezes the GPS display.

### Destination ###
PyGpsLog provides a simple way of navigating, a little bit like Nokia's
own Navigator application.

The `Destination` menu allows you to select a destination, either from your
landmarks (if [installed](#INSTALLATION.md)) or as decimal coordinates.

Once a destination is selected it's distance and estimated arrival time is shown
on the Overview and Compass pages. In the landmarks list it will be shown on top.

On the Compass and Satellite pages there will be two dot helping you navigate.
A **blue** marker shows the absolute heading and a **red** marker will show heading
relative to your current heading (or view direction, when going forward).
Here's a [screnshot](Screenshots#Compass.md).

# SETTINGS #
## General ##
  * **Keep Backlight On**: Keeps the devices' backlight on while logging or GPS display is active. Default: **off**.
  * **Start automatically**: Start a new log file when the application is started. Default: **off**.
  * **Altitude Correction**: Calibrates your altitude. Please check, when using [LocationRequestor](#Location_Requestor.md) or [Nokia Positioning](#Nokia_Positioning.md). Default: **0**.
  * **Output Directory**: Log file directory. Default **`C:\Data\GpsLog`** (or **`E:\Data\GpsLog`**, if a memory card is installed).
  * **Log Format**: `GPX` or `OziExplorer`. Default: **GPX**.
  * **Min. Distance to Record**: The minimum distance in meters you have to travel, before a new trackpoint is inserted. Default: **25** m.
  * **Max. Distance per GPS interval**: Greater jumps will be regarded as incorrect data and discarded. Increase this value in an airplane. Default: **80** m.
  * **Extended Data Format**: Logs [additional data](Screenshots#Extended_Format.md) (like HDOP, VDOP, number of satellites and fix type in GPX format or formatted time in OziExplorer format). Default: **on**.
  * **Log Satellites**: Log [detailed satellite data](Screenshots#Satellite_Info.md) (in extended GPX format only). Turn this off, if you're low on memory. Default: **on**.
  * **Choose new Bluetooth device**: Set this to `on` to choose a new external Bluetooth device, next time you start logging. If you [signed](#INSTALLATION.md) the application or the [LocationRequestor module](#INSTALLATION.md) is installed, you can choose your [operating mode](#OPERATION.md) here. Default: Depends on your [installation](#INSTALLATION.md).
  * **Show CPU Usage**: Show the CPU meter for this application. Only available if the [e32jext](http://code.google.com/p/pygpslog/downloads/list?can=2&q=label%3ARecommended+e32jext) module is [installed](#INSTALLATION.md). Default: **on**.
  * **Show Battery Meter in Fullscreen**: Default: **on**.
  * **Reset to default settings**: Application will exit after resetting.

The `'Options'` menu of the general settings page holds these commands:
  * **Save**: Save all settings.
  * **Merge GPX Tracks+Wpts**: Merges _all_ existing logfiles and their corresponding waypoint files into a single log file.

## Landmarks ##
The landmark settings are only available if the Landmarks module is [installed](#INSTALLATION.md).

  * **Store Waypoints as Landmarks**: Default: **on**.
  * **Edit New Landmarks**: Let's you edit or delete landmarks after insertion. Default: **on**.
  * **Category for Waypoints**: New [waypoints](#Waypoints.md) will be assigned this category by default. Default: **(None)**.
  * **Store Markers as Landmarks**: Inserts a landmark for [track segment](#Track_Segments.md) markers. Default: **on**.
  * **Landmark Search Radius**: Landmarks further away will not be displayed on the landmarks page. Increasing this may _significantly_ slow down the application. Default: **10** km.
  * **Notify Near Category**: Shows a notification when you reach landmarks of a this category. Default: **(None)**.
  * **Distance for Notification**: Show the notification when closer. Default: **25** m
  * **Vibrate on Notification**: Only working if `miso` or `misty` modules are [installed](#INSTALLATION.md). Default: **on**.
  * **Update Interval**: Refresh the landmarks page only after this interval. Default: **3** sec.
  * **Use Small Icons**: Default: **off**.

These settings are for experimental features:
  * **Show Nokia Icons**: Shows a listbox with Nokia's own landmark icons instead of the internal ones. Default: **off**.

The `'Options'` menu of the landmarks settings page holds these commands:
  * **Save**: Save all settings.
  * **Remove Disp. Categories**: Hides categories from the landmarks page. **Careful**: This may eat a lot of battery.
  * **Add Display Categories**: Unless all categories are displayed, the caveat above applies!
  * **Landmark Editor**: Invokes Nokia's Landmark application. (**Caution**: experimental feature!).
  * **Set Icons/Categories**: This inserts the default Categories in Nokias landmarks database and sets the icons for Landmarks in these categories. **Repeat this step** if you imported landmarks from another device or PC.

Since version 0.2.1, there is also the possibility to add [user defined icon sets](UserIcons.md),
for new landmark categories or non-english versions of S60.

An audible alarm can be played on notification by copying a sound file
named `'alarm.aac'` to your [configured](#General.md) log directory.


# TROUBLESHOOTING #
## Known Problems ##
  * When using an external Bluetooth GPS, logfiles are closed, if the Bluetooth connection is lost.
  * Landmark display eats **a lot** of CPU time and battery. It's has been improved by using a cache.
  * Landmark category filtering is still incomplete.
  * _A lot_ of unhandled exceptions... Most of them will only be visible on program close.

## FAQ ##
  * Q: My Battery drains very rapidly!
  * A: First, [switch the backlight off](#General.md). If you only want to log your GPS track, switch to [Powersave mode](#Display_Modes.md). Or, if you don't need track segment warnings, [set 'Notify near Category'](#Landmarks.md) to `'(None)'`. If you absolutely want to display the landmarks page, [don't hide](#Landmarks.md) any categories.

  * Q: When I try to start PyGpsLog, nothing happens.
  * A: Try to install PyGpsLog to the same drive as your Python installation.

  * Q: There are no icons on the landmarks page.
  * A: Only icons for internally known categories will be shown. To do this go to Settings->Landmarks->Options->Set Icons/Categories.

# SCREENSHOTS #
![http://pygpslog.googlecode.com/svn/trunk/doc/img/PyGpsLog-Main.jpg](http://pygpslog.googlecode.com/svn/trunk/doc/img/PyGpsLog-Main.jpg)
![http://pygpslog.googlecode.com/svn/trunk/doc/img/PyGpsLog-Satellite.jpg](http://pygpslog.googlecode.com/svn/trunk/doc/img/PyGpsLog-Satellite.jpg)
![http://pygpslog.googlecode.com/svn/trunk/doc/img/PyGpsLog-Satellite-nm.jpg](http://pygpslog.googlecode.com/svn/trunk/doc/img/PyGpsLog-Satellite-nm.jpg)
![http://pygpslog.googlecode.com/svn/trunk/doc/img/PyGpsLog-Compass-nm.jpg](http://pygpslog.googlecode.com/svn/trunk/doc/img/PyGpsLog-Compass-nm.jpg)

Some more [here](Screenshots.md).

# ACKNOWLEDGEMENTS #
  * All authors of the [required and recommended modules](#INSTALLATION.md). Without them, this work would have been impossible!
  * [M. Umut Pulat](http://12m3.deviantart.com/) for his beautiful _Tulliana 2_ icon set!
  * [Milosz Wlazlo](http://miloszwl.deviantart.com/) for the original _Boomy_ icon set!