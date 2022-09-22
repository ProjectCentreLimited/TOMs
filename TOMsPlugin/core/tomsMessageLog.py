# -----------------------------------------------------------
# Licensed under the terms of GNU GPL 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# ---------------------------------------------------------------------
# Tim Hancock 2017
# Oslandia 2022

import datetime
import logging
import os.path
from typing import Any

from qgis.core import (
    Qgis,
    QgsExpressionContextUtils,
    QgsMessageLog,
    QgsProject,
)

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    level=logging.DEBUG,
)
tomsLogger = logging.getLogger("TOMs")
tomsLogger.setLevel(logging.DEBUG)


class TOMsMessageLog:
    """
    Wraps QGis and Python logging systems
    """

    filename = ""
    currLoggingLevel = Qgis.Info
    DEBUG = logging.DEBUG
    tomsLogFileHandler = None

    @staticmethod
    def logMessage(msg: str, *args: Any, **kwargs: Any) -> None:
        """forward message to qgis and python logging"""
        # check to see if a logging level has been set
        # qLevel can also be equals to logging.DEBUG
        qLevel = kwargs.get("level") or Qgis.Info
        messageLevel = int(qLevel)

        # >>>> python logging part
        loggingLevel = logging.DEBUG
        if messageLevel == Qgis.Info:
            loggingLevel = logging.INFO
        elif messageLevel == Qgis.Warning:
            loggingLevel = logging.WARNING
        elif messageLevel == Qgis.Critical:
            loggingLevel = logging.ERROR

        filename, lineNumber, funcName, _ = tomsLogger.findCaller()
        logRec = logging.LogRecord(
            tomsLogger.name,
            loggingLevel,
            filename,
            lineNumber,
            msg,
            args,
            None,
            func=funcName,
        )
        tomsLogger.handle(logRec)

        # >>>>> QGIS logging part
        if (
            logging.DEBUG > messageLevel >= TOMsMessageLog.currLoggingLevel
        ):  # disable when messageLevel is DEBUG as QGIS does not handle it
            kwargs["level"] = messageLevel
            QgsMessageLog.logMessage(msg, *args, **kwargs, tag="TOMs Panel")

    @classmethod
    def setLogFile(cls) -> None:
        logFilePath = os.environ.get("QGIS_LOGFILE_PATH")
        if logFilePath is None:
            QgsMessageLog.logMessage(
                "Error in TOMsMessageLog. QGIS_LOGFILE_PATH not found ... ",
                tag="TOMs Panel",
            )
            return

        QgsMessageLog.logMessage(
            "LogFilePath: " + str(logFilePath), tag="TOMs Panel", level=Qgis.Info
        )

        logfile = "qgis_" + datetime.date.today().strftime("%Y%m%d") + ".log"
        TOMsMessageLog.filename = os.path.join(logFilePath, logfile)

        if TOMsMessageLog.tomsLogFileHandler:
            tomsLogger.removeHandler(TOMsMessageLog.tomsLogFileHandler)

        TOMsMessageLog.tomsLogFileHandler = logging.FileHandler(TOMsMessageLog.filename)
        tomsLogger.addHandler(TOMsMessageLog.tomsLogFileHandler)

        QgsMessageLog.logMessage(
            "Sorting out log file" + TOMsMessageLog.filename,
            tag="TOMs Panel",
            level=Qgis.Info,
        )
