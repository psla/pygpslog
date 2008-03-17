@echo off 
set DFLT=         /c16 icons\gpslog_dflt.svg
set ICONS=        /c16 icons\gpslog_sp30.svg
set ICONS=%ICONS% /c16 icons\gpslog_sp50.svg
set ICONS=%ICONS% /c16 icons\gpslog_sp60.svg
set ICONS=%ICONS% /c16 icons\gpslog_sp70.svg
set ICONS=%ICONS% /c16 icons\gpslog_sp80.svg
set ICONS=%ICONS% /c16 icons\gpslog_sp100.svg

rem Adjust when adding icons
set TILE=-tile 4x4

if '%UID%' == '' set UID=0xA0005B76

rem set DEST=mif\resource\apps\gpsloglm_%UID%.mif

set DEST=src\gpsloglm.mif

call symenv mifconv %DEST% /E %DFLT% %ICONS%

set PATH=F:\UTIL\MMedia\ImageMagick-6.3.9-Q16;%PATH%

set DFLT=%DFLT:icons\=icons\full\%
set DFLT=%DFLT:/c16=icons\full\gpslog_dflt_mask.svg%
set ICONS=%DFLT% %ICONS:icons\=icons\full\%
set ICONS=%ICONS:/c16=icons\full\gpslog_sp_mask.svg%
set SPLASHSVG=icons\full\PyGpsLog.svg


convert -density 12 -background black %SPLASHSVG%             -quality 80 src\gpslog.jpg
montage -density 12 -background black -geometry 64x64 %ICONS% -quality 75 %TILE% src\gpsloglm.jpg

mkiconset.py icons\iconsets\default src\gpslogico.jpg src\gpslogico
del src\gpslogico.mif
