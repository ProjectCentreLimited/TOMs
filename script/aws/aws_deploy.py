import configparser
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

_here = Path(__file__).absolute().parent

FORMAT = "%(asctime)-15s %(levelname)s %(filename)s:%(lineno)04d: %(message)s"
logging.basicConfig(
    level=logging._nameToLevel.get(  # pylint: disable=protected-access
        os.environ.get("LOGGING_LEVEL", "DEBUG").upper()
    ),
    format=FORMAT,
    stream=sys.stdout,
)
logger = logging.getLogger("aws_deploy")

config = configparser.ConfigParser()


def config_prop(section, prop):
    try:
        return config[section][prop]
    except KeyError:
        sys.exit("Error reading property '{}' from section '{}'!".format(section, prop))


def copy_file(label: str, srcPath: str, destPath: str, fileMode=None):
    finalSrcPath = Path(os.path.expandvars(srcPath))
    if not finalSrcPath.exists():
        sys.exit("'{}' file '{}' does not exist.".format(label, finalSrcPath))
    if not finalSrcPath.is_file():
        sys.exit("'{}' path '{}' is not a file.".format(label, finalSrcPath))

    finalDestPath = Path(os.path.expandvars(destPath))
    if not finalDestPath.exists():
        finalDestPath.mkdir(parents=True)

    finalDestPath = finalDestPath / finalSrcPath.name

    # remove hidden and RO flags to be able to replace the file
    if finalDestPath.exists():
        subprocess.check_call(["attrib", "-r", "-h", finalDestPath])

    shutil.copyfile(finalSrcPath, finalDestPath)

    if fileMode:
        for m in fileMode:
            subprocess.check_call(["attrib", m, finalDestPath])

    logger.info(
        "'{}' file '{}' copied to '{}'".format(label, finalSrcPath, finalDestPath)
    )


def copy_directory(label: str, srcPath: str, destPath: str, purge=False, fileMode=None):
    finalSrcPath = Path(os.path.expandvars(srcPath))
    if not finalSrcPath.exists():
        sys.exit("'{}' directory '{}' does not exist.".format(label, finalSrcPath))
    if not finalSrcPath.is_dir():
        sys.exit("'{}' path '{}' is not a directory.".format(label, finalSrcPath))

    finalDestPath = Path(os.path.expandvars(destPath))
    if not finalDestPath.exists():
        finalDestPath.mkdir(parents=True)

    finalDestPath = finalDestPath / finalSrcPath.parts[-1]

    if finalDestPath.exists():
        # remove hidden and RO flags to be able to replace the files
        subprocess.check_call(["attrib", "-r", "-h", "/S", finalDestPath / "*"])
        if purge:
            shutil.rmtree(finalDestPath)

    shutil.copytree(finalSrcPath, finalDestPath)

    if fileMode:
        for m in fileMode:
            subprocess.check_call(["attrib", m, "/S", finalDestPath])

    logger.info(
        "'{}' directory '{}' copied to '{}'".format(label, finalSrcPath, finalDestPath)
    )


if __name__ == "__main__":
    # root path is the root directory of all plugin files, qgis projects, etc.
    rootPath = os.environ.get("DEPLOY_ROOT_DIR")
    if not rootPath:
        sys.exit("No root path defined! Use env var DEPLOY_ROOT_DIR!")
    if not os.path.exists(rootPath):
        sys.exit("Root directory '{}' does not exist.".format(rootPath))
    if not os.path.isdir(rootPath):
        sys.exit("Root directory '{}' is not a directory.".format(rootPath))

    os.environ["DEPLOY_ROOT_DIR"] = rootPath
    # expose var to whole windows env:
    stage = Path(rootPath).parts[-1]
    os.environ["DEPLOY_STAGE"] = stage
    subprocess.check_call(["setx", "DEPLOY_STAGE", stage])

    # read config file
    configFile = Path(
        os.environ.get("DEPLOY_CONFIG_FILE", str(_here / "aws_deploy.conf"))
    )
    if not configFile.exists():
        sys.exit("Config file '{}' does not exist!".format(configFile))
    try:
        config.read(configFile)
    except Exception as e:
        sys.exit("Error parsing config file '{}'! Error: {}".format(configFile, e))

    # ================ USER ELEVATION
    user = os.environ.get("AppStream_UserName")
    if not user:
        logger.warning("Unable to obtain appstream username, using guest mode.")
        mode = "guest"
    else:
        try:
            mode = config["users"][user]
            if mode not in [
                "admin",
                "guest",
                "write_confirm_operator",
                "write_no_confirm_operator",
                "read_only_operator",
            ]:
                logger.warning(
                    "Unknown elevation ('{}'), using guest mode.".format(mode)
                )
                mode = "guest"

        except KeyError:
            logger.info(
                "Unable to find elevated permission for user '{}', using guest mode.".format(
                    user
                )
            )
            mode = "guest"

    os.environ["DEPLOY_USER_ELEVATION"] = mode
    # expose var to whole windows env:
    subprocess.check_call(["setx", "DEPLOY_USER_ELEVATION", mode])

    # ================ QGIS
    # cleanup
    qgisPath = Path(os.path.expandvars("%USERPROFILE%/AppData/Roaming/QGIS"))
    if qgisPath.exists():
        subprocess.check_call(["attrib", "-r", "-h", "/S", qgisPath / "*"])
        shutil.rmtree(qgisPath)

    # create default QGIS ini (if not exist) with TOMs plugin and customization activated.
    copy_file(
        "Ini",
        config_prop("qgis", "ini_file_path"),
        "%USERPROFILE%/AppData/Roaming/QGIS/QGIS3/profiles/default/QGIS/",
    )

    copy_file(
        "Customizations",
        config_prop("qgis", "customization_file_path"),
        "%USERPROFILE%/AppData/Roaming/QGIS/QGIS3/profiles/default/QGIS/",
        ["+r", "+h"],
    )

    copy_directory(
        "Plugin",
        config_prop("qgis", "plugin_dir_path"),
        "%USERPROFILE%/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/",
        True,
    )

    # ================ PROJECT
    copy_file(
        "TOMs qgis project",
        config_prop("toms", "qgis_project_file_path"),
        "c:/qgis_projects/",
    )
    copy_file(
        "TOMs config", config_prop("toms", "config_file_path"), "c:/qgis_projects/"
    )

    # ================ PG_SERVICE
    copy_file(
        "PG service",
        config_prop("pg_service", "conf_file_path"),
        "%APPDATA%/postgresql/",
        ["+r", "+h"],
    )

    imagePath = Path("c:/qgis_photo_path")
    if not imagePath.exists():
        imagePath.mkdir(parents=True)
