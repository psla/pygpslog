# Screenshots #

### Overview ###
![http://pygpslog.googlecode.com/svn/trunk/doc/img/PyGpsLog-Main.jpg](http://pygpslog.googlecode.com/svn/trunk/doc/img/PyGpsLog-Main.jpg)
![http://pygpslog.googlecode.com/svn/trunk/doc/img/PyGpsLog-Main-nm.jpg](http://pygpslog.googlecode.com/svn/trunk/doc/img/PyGpsLog-Main-nm.jpg)

### Satellite Status ###
![http://pygpslog.googlecode.com/svn/trunk/doc/img/PyGpsLog-Satellite.jpg](http://pygpslog.googlecode.com/svn/trunk/doc/img/PyGpsLog-Satellite.jpg)
![http://pygpslog.googlecode.com/svn/trunk/doc/img/PyGpsLog-Satellite-nm.jpg](http://pygpslog.googlecode.com/svn/trunk/doc/img/PyGpsLog-Satellite-nm.jpg)

### Compass ###
![http://pygpslog.googlecode.com/svn/trunk/doc/img/PyGpsLog-Compass.jpg](http://pygpslog.googlecode.com/svn/trunk/doc/img/PyGpsLog-Compass.jpg)
![http://pygpslog.googlecode.com/svn/trunk/doc/img/PyGpsLog-Compass-nm.jpg](http://pygpslog.googlecode.com/svn/trunk/doc/img/PyGpsLog-Compass-nm.jpg)

### Landmarks ###
Only available with landmarks module installed

![http://pygpslog.googlecode.com/svn/trunk/doc/img/PyGpsLog-Landmarks.jpg](http://pygpslog.googlecode.com/svn/trunk/doc/img/PyGpsLog-Landmarks.jpg)
![http://pygpslog.googlecode.com/svn/trunk/doc/img/PyGpsLog-Landmarks-big.jpg](http://pygpslog.googlecode.com/svn/trunk/doc/img/PyGpsLog-Landmarks-big.jpg)
![http://pygpslog.googlecode.com/svn/trunk/doc/img/PyGpsLog-Landmarks-nm.jpg](http://pygpslog.googlecode.com/svn/trunk/doc/img/PyGpsLog-Landmarks-nm.jpg)

### Sample Logfiles ###

##### Basic Info #####
```
<?xml version='1.0'?>

<gpx creator="GpsLog for S60" version="1.1" xmlns="http://www.topografix.com/GPX/1/1" xmlns:gpslog="http://pygpslog.googlecode.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://pygpslog.googlecode.com http://pygpslog.googlecode.com/files/gpslog_0_2.xsd http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd">
  <metadata>
    <time>2008-03-16T10:53:30Z</time>
  </metadata>
  <trk>
    <trkseg>
      <trkpt lat="61.474350000" lon="23.838883333">
        <ele>192.599991</ele>
        <time>2005-08-12T12:57:39Z</time>
      </trkpt>
      <trkpt lat="61.474566667" lon="23.838683333">
        <ele>192.599991</ele>
        <time>2005-08-12T12:57:40Z</time>
      </trkpt>
...
      <trkpt lat="61.476650000" lon="23.836050000">
        <ele>188.899994</ele>
        <time>2005-08-12T12:57:53Z</time>
      </trkpt>
    </trkseg>
  </trk>
</gpx>
<!-- Summary: -->
<!-- Trackpoints: 12 -->
<!-- Distance:    0.3km -->
```

##### Extended Format #####
With a segment marker

```
<?xml version='1.0'?>

<gpx creator="GpsLog for S60 (S60 Location using #Simulation)" version="1.1" xmlns="http://www.topografix.com/GPX/1/1" xmlns:gpslog="http://pygpslog.googlecode.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://pygpslog.googlecode.com http://pygpslog.googlecode.com/files/gpslog_0_2.xsd http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd">
  <metadata>
    <time>2008-03-05T20:48:25Z</time>
  </metadata>
  <trk>
    <trkseg>
      <trkpt lat="61.476033333" lon="23.836850000">
        <ele>188.899994</ele>
        <time>2005-08-12T12:57:50Z</time>
        <name>Speed 80 - 1</name>
        <sat>5</sat>
        <hdop>4.3</hdop>
        <vdop>6.5</vdop>
        <extensions>
          <gpslog:speed>73.71</gpslog:speed>
          <gpslog:hdg>329.1000</gpslog:hdg>
          <gpslog:hacc>26.0</gpslog:hacc>
          <gpslog:vacc>39.0</gpslog:vacc>
          <gpslog:mark in="true">Speed 80</gpslog:mark>
        </extensions>
      </trkpt>
...
      <trkpt lat="61.477416667" lon="23.834950000">
        <ele>183.500000</ele>
        <time>2005-08-12T12:57:59Z</time>
        <sat>5</sat>
        <hdop>4.8</hdop>
        <vdop>7.3</vdop>
        <extensions>
          <gpslog:speed>71.12</gpslog:speed>
          <gpslog:hdg>328.5000</gpslog:hdg>
          <gpslog:hacc>29.0</gpslog:hacc>
          <gpslog:vacc>43.5</gpslog:vacc>
        </extensions>
      </trkpt>
      <trkpt lat="61.477600000" lon="23.834666667">
        <ele>180.899994</ele>
        <time>2005-08-12T12:58:00Z</time>
        <name>Speed 80 - 2</name>
        <sat>5</sat>
        <hdop>4.7</hdop>
        <vdop>7.0</vdop>
        <extensions>
          <gpslog:speed>70.56</gpslog:speed>
          <gpslog:hdg>328.2000</gpslog:hdg>
          <gpslog:hacc>28.0</gpslog:hacc>
          <gpslog:vacc>42.0</gpslog:vacc>
          <gpslog:mark in="false" match="Speed 80 - 1">Speed 80</gpslog:mark>
        </extensions>
      </trkpt>
    </trkseg>
  </trk>
</gpx>
<!-- Summary: -->
<!-- Trackpoints: 31 -->
<!-- Distance:    0.8km -->
```

##### Satellite Info #####

```
<gpx creator="GpsLog for S60 (S60 Location using Bluetooth GPS)" version="1.1" xmlns="http://www.topografix.com/GPX/1/1" xmlns:gpslog="http://pygpslog.googlecode.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://pygpslog.googlecode.com http://pygpslog.googlecode.com/files/gpslog_0_2.xsd http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd">
  <metadata>
    <time>2008-03-05T20:57:08Z</time>
  </metadata>
  <trk>
    <trkseg>
      <trkpt lat="48.939628333" lon="12.320273333">
        <ele>444.399994</ele>
        <time>2008-03-05T21:04:47Z</time>
        <sat>6</sat>
        <hdop>2.0</hdop>
        <vdop>2.3</vdop>
        <extensions>
          <gpslog:speed>70.63</gpslog:speed>
          <gpslog:hdg>267.4800</gpslog:hdg>
          <gpslog:hacc>12.0</gpslog:hacc>
          <gpslog:vacc>13.6</gpslog:vacc>
          <gpslog:sat az="306.0" ele="75.0" prn="26" signal="50" used="true" />
          <gpslog:sat az="86.0" ele="63.0" prn="28" signal="39" used="true" />
          <gpslog:sat az="299.0" ele="60.0" prn="15" signal="51" used="true" />
          <gpslog:sat az="68.0" ele="33.0" prn="8" signal="48" used="true" />
          <gpslog:sat az="199.0" ele="29.0" prn="10" signal="36" used="true" />
          <gpslog:sat az="320.0" ele="15.0" prn="18" signal="35" used="false" />
          <gpslog:sat az="131.0" ele="12.0" prn="17" signal="33" used="false" />
          <gpslog:sat az="263.0" ele="11.0" prn="9" signal="43" used="true" />
          <gpslog:sat az="77.0" ele="9.0" prn="27" signal="32" used="false" />
          <gpslog:sat az="19.0" ele="2.0" prn="19" signal="-1" used="false" />
          <gpslog:sat az="294.0" ele="1.0" prn="21" signal="23" used="false" />
          <gpslog:sat az="215.0" ele="28.0" prn="33" signal="35" used="false" />
        </extensions>
      </trkpt>
    </trkseg>
  </trk>
</gpx>
<!-- Summary: -->
<!-- Trackpoints: 383 -->
<!-- Distance:    12.6km -->
```

##### OziExplorer #####
```
OziExplorer Track Point File Version 2.1
WGS 84
Altitude is in Feet
Reserved 3
0,2,255,S60 GpsLog,0,0,2,8421376
8
61.474567,23.838683,1,631,38576.5400463,12-Aug-05,12:57:40
61.474767,23.838433,0,620,38576.5400694,12-Aug-05,12:57:42
61.474967,23.838150,0,620,38576.5400810,12-Aug-05,12:57:43
61.475183,23.837917,0,620,38576.5400926,12-Aug-05,12:57:44
61.475400,23.837667,0,620,38576.5401157,12-Aug-05,12:57:46
61.475617,23.837417,0,619,38576.5401273,12-Aug-05,12:57:47
61.475817,23.837117,0,619,38576.5401389,12-Aug-05,12:57:48
61.476033,23.836850,0,619,38576.5401620,12-Aug-05,12:57:50
```