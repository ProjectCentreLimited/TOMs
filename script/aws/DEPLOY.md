# Deploy

## Installation

1. On a EC2 server, add a share folder (to a directory `/home/ubuntu/appstream`) and a user to the samba server:

   ```ini
   [appstream]
   comment = Appstream data
   path = /home/ubuntu/appstream
   guest ok = yes
   browseable = yes
   read only = yes
   ```

   and add user with `smbpasswd -a ubuntu`

1. inside `/home/ubuntu/appstream` create these directories :

   ```raw
   \- DEPLOY_LEVEL1/
   |  \- USER_ELEVATION1/
   |  |  |- .pg_service.conf
   |  |  |- CEC.qgs
   |  |  |- QGISCUSTOMIZATION3.ini
   |  |  |- TOMs.conf
   |  \- USER_ELEVATION2/
   |  |  |- .pg_service.conf
   |  |  |- CEC.qgs
   |  |  |- QGISCUSTOMIZATION3.ini
   |  |  |- TOMs.conf
   |  \- qgis_plugin/
   |  |  |- ...
   |  |- aws_deploy.conf
   \- DEPLOY_LEVEL2/
   |  \- USER_ELEVATION1/
   |  |  |- .pg_service.conf
   |  |  |- CEC.qgs
   |  |  |- QGISCUSTOMIZATION3.ini
   |  |  |- TOMs.conf
   |  \- USER_ELEVATION2/
   |  |  |- .pg_service.conf
   |  |  |- CEC.qgs
   |  |  |- QGISCUSTOMIZATION3.ini
   |  |  |- TOMs.conf
   |  \- qgis_plugin/
   |  |  |- ...
   |  |- aws_deploy.conf
   ```

   * `DEPLOY_LEVEL` are the different deploiment kinds: `prod`, `test`, `staging`...
   * `USER_ELEVATION` are the different possible user elevations: `admin`, `write_confirm_operator`, `guest`...

   * The `.pg_service.conf` will contain valid information to connect to the databases used in the `CEC.qgs` QGis project file  (see [sample](pg_service.sample.conf)).
   * The `QGISCUSTOMIZATION3.ini` contains QGis customizations (see [sample](QGISCUSTOMIZATION3.sample.ini)).
   * The `TOMs.conf` contains the TOMs plugin configuration and must reference the plugin forms with this path (see [sample](TOMs.sample.conf)):

     ```ini
     [TOMsLayers]
     form_path = %%USERPROFILE%%/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/TOMsPlugin/ui
     ```

   * The `qgis_plugin` directory is a clone of the [TOMsPlugin](https://github.com/ProjectCentreLimited/TOMs.git) directory
   * The `aws_deploy.conf` describes the deployment configuration read by the `aws_deploy.py` script (on Windows) (see [sample](aws_deploy.windows-sample.conf))

1. On the `c:\script` directory of AWS image builder, add a file `aws_startup.bat` like this [sample](aws_startup.sample.bat). In this sample:

   * `\\samba.private-projectcenter.com\appstream` references the share previouly created
   * `ubuntu` references the samba user previously created
   * `DEPLOY_ROOT_DIR` references a deploy level directory inside `/home/ubuntu/appstream` (f.e. `live`)

1. On the `c:\script` directory of AWS image builder, add a file `aws_cleanup.bat` like this [sample](aws_cleanup.sample.bat).

1. On the `c:\script` directory of AWS image builder, add a file `tom_launcher.bat` like this [sample](tom_launcher.sample.bat).
   This script will be use in the `ImageAssistant` as the application to be launched.

1. Follow instructions [To link Amazon FSx file shares with AppStream 2.0](https://aws.amazon.com/fr/blogs/desktop-and-application-streaming/using-amazon-fsx-with-amazon-appstream-2-0/)
   to use the script `c:\script\aws_startup.bat` for `Logon` and `c:\script\aws_cleanup.bat` for `Logoff`.


## User elevation

Differents permission are defined:

| Name                        | Full control | Read | Write | Print | Report bay data | Confirm (accept or reject) orders | Db role         |
| ----                        | ----         | ---- | ----- | ----- | --------------- | --------------------------------- | --              |
| `admin`                     | Y            | Y    | Y     | Y     | Y               | Y                                 | `toms_admin`    |
| `write_confirm_operator`    | N            | Y    | Y     | Y     | Y               | Y                                 | `toms_operator` |
| `write_no_confirm_operator` | N            | Y    | Y     | Y     | Y               | N                                 | `toms_operator` |
| `read_only_operator`        | N            | Y    | N     | Y     | N               | N                                 | `toms_public`   |
| `guest`                     | N            | Y    | N     | N     | N               | N                                 | `toms_public`   |

## Updates

To update a deployment just update the files in a `DEPLOY_LEVEL` for a given `USER_ELEVATION` (from the EC2 server) and restart the AppStream session.
