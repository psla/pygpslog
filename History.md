# Version History #
### Legend ###
+ Added feature

- Bugfix

~ Changed functionality

## 0.3.1 - Mar. 30, 2009 ##
  * - Don't use undocumented positioning features for PyS60 versions >= 1.4.5 (fixes [Issue 8](https://code.google.com/p/pygpslog/issues/detail?id=8)).
  * ~ Add `'E:\resource`' to sys.path in case modules are installed on `'E:`'.

## 0.3.0 - Mar. 23, 2008 (Happy Easter!) ##
  * + Write marked waypoints to a separate GPX or OziExplorer file.
  * + Option to merge finished GPX tracks and waypoints.
  * + User configurable track segment markers.
  * + Optionally insert manually entered destinations as waypoints/landmarks.
  * + Added simple keyboard help.
  * + [extractmarks](extractmarks.md) can now create bi-directional landmarks.
  * - Fixed a bug in arrival time display.
  * - Switch off vibration while charging. May hang some devices (like the E65).
  * - Bugfixes in internal settings.
  * ~ Added a progress dialog to the `'Set Icons/Categories'` option.
  * ~ Don't set landmark icons for global categories.
  * ~ Relaxed parsing of destination coordinates.

## 0.2.3 - Mar. 21, 2008 ##
  * + Select categories to be displayed (see [settings](README#Landmarks.md)).
  * + Show running average speed on compass page, if a destination is selected.
  * - Landmark access optimized. Still eats a lot of CPU, so keep you charger ready.
  * ~ Switched to the GPLed [Tulliana 2](README#ACKNOWLEDGEMENTS.md) icon set

## 0.2.2 - Mar. 18, 2008 ##
  * + Added support for [directional track segments](extractmarks.md)
  * + Added support for [audible and vibrating alarms](README#Landmarks.md).
  * - Fixed a bug that caused wrong categories for track segments

## ~~0.2.1 - Mar. 17, 2008~~ ##
**Revoked due to a bad track segment marking bug**
  * + Support for UserIcons in landmarks
  * - Fixed slow application loading.
  * - Don't show average speed if logfile is closed
  * - Switch to normal screen on landmark edit (may crash Python).
  * ~ Lowered the icon quality to reduce installed size.

## 0.2.0 - Mar. 14, 2008 ##
  * + Simple Navigation (choose a destination)
  * + Display GPS data without starting a log file.
  * + Night mode
  * + Full screen mode with battery meter
  * + CPU usage meter
  * + Use `envy`-module to prevent accidental red-key-exit.
  * + Ask for restart on GPS failure
  * - Waypoint marking fixed
  * - Fix crash on lost GPS
  * ~ Optimized landmark drawing

## 0.1.7 - Mar. 07, 2008 ##
Initial public version.