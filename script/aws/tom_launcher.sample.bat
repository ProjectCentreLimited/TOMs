%echo off

:while
if not exist c:\script\startup_done (
	timeout /T 1 /NOBREAK
	echo "Still waiting"
	goto :while
)

call "C:\Program Files\QGIS 3.22.10\bin\qgis-ltr.bat" C:\qgis_projects\CEC.qgs
