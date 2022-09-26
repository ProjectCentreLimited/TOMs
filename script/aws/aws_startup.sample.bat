@echo off
net use S: /delete
net use S: \\samba.private-projectcenter.com\appstream 2022u6 /user:ubuntu

set DEPLOY_ROOT_DIR=\\samba.private-projectcenter.com\appstream\live
set DEPLOY_CONFIG_FILE=%DEPLOY_ROOT_DIR%\aws_deploy.conf

"C:\Program Files\QGIS 3.22.10\bin\python-qgis-ltr.bat" %DEPLOY_ROOT_DIR%\qgis_plugin\script\aws\aws_deploy.py

timeout /T 10
net use S: /delete
