# -----------------------------------------------------------
# Licensed under the terms of GNU GPL 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# -----------------------------------------------------------
# Tim Hancock/Matthias Kuhn 2017
# Oslandia 2022

import configparser
import os

from qgis.core import Qgis, QgsExpressionContextUtils, QgsProject
from qgis.PyQt.QtCore import NULL, QObject, pyqtSignal
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.utils import iface

from .core.tomsMessageLog import TOMsMessageLog


class TOMsParams(QObject):

    tomsParamsNotFound = pyqtSignal()
    """ signal will be emitted if there is a problem with opening TOMs - typically a layer missing """
    tomsParamsSet = pyqtSignal()
    """ signal will be emitted if there is a problem with opening TOMs - typically a layer missing """

    def __init__(self):
        QObject.__init__(self)

        TOMsMessageLog.logMessage("In TOMSParams.init ...", level=TOMsMessageLog.DEBUG)
        self.tomsParamsList = [
            "BayWidth",
            "BayLength",
            "BayOffsetFromKerb",
            "LineOffsetFromKerb",
            "CrossoverShapeWidth",
            "PhotoPath",
            "MinimumTextDisplayScale",
            "TOMsDebugLevel",
            "AllowZoneEditing",
        ]

        self.tomsParamsDict = {}

    def getParams(self):

        TOMsMessageLog.logMessage("In TOMsParams.getParams ...", level=TOMsMessageLog.DEBUG)
        found = True

        # Check for project being open
        currProject = QgsProject.instance()

        if len(currProject.fileName()) == 0:
            QMessageBox.information(None, "ERROR", ("Project not yet open"))
            found = False

        else:

            # TOMsMessageLog.logMessage("In TOMSLayers.getParams ... starting to get", level=logging.DEBUG)

            for param in self.tomsParamsList:
                TOMsMessageLog.logMessage(
                    "In TOMsParams.getParams ... getting " + str(param),
                    level=TOMsMessageLog.DEBUG,
                )

                currParam = None
                try:
                    currParam = QgsExpressionContextUtils.projectScope(QgsProject.instance()).variable(param)
                except Exception:
                    QMessageBox.information(
                        None,
                        "ERROR",
                        ("Property " + param + " is not present"),
                    )

                if len(str(currParam)) > 0:
                    self.tomsParamsDict[param] = currParam
                    TOMsMessageLog.logMessage(
                        "In TOMsParams.getParams ... set " + str(param) + " as " + str(currParam),
                        level=TOMsMessageLog.DEBUG,
                    )
                else:
                    QMessageBox.information(
                        None,
                        "ERROR",
                        ("Property " + param + " is not present"),
                    )
                    found = False
                    break

        if not found:
            self.tomsParamsNotFound.emit()
        else:
            self.tomsParamsSet.emit()

            # TOMsMessageLog.logMessage("In TOMSLayers.getParams ... finished ", level=logging.DEBUG)

        return found

    def setParam(self, param):
        return self.tomsParamsDict.get(param)


class TOMsConfigFile(QObject):

    tomsConfigFileNotFound = pyqtSignal()
    """ signal will be emitted if TOMs config file is not found """

    def __init__(self):
        super().__init__()

        TOMsMessageLog.logMessage("In TOMsConfigFile.init ...", level=TOMsMessageLog.DEBUG)

        self.config = configparser.ConfigParser()

    def initialiseTOMsConfigFile(self):

        # function to open file "toms.conf". Assume path is same as project file - unless environ variable is set

        # check for environ variable
        configPath = None
        try:
            configPath = os.environ.get("TOMs_CONFIG_PATH")
        except Exception:
            TOMsMessageLog.logMessage("In getTOMsConfigFile. TOMs_CONFIG_PATH not found ...", level=Qgis.Info)

        if configPath is None:
            configPath = QgsExpressionContextUtils.projectScope(QgsProject.instance()).variable("project_home")

        if configPath == NULL:
            QMessageBox.information(
                None,
                "Information",
                "Project probably not opened",
                QMessageBox.Ok,
            )
            self.tomsConfigFileNotFound.emit()
            return

        TOMsMessageLog.logMessage(
            "In getTOMsConfigFile. config_path: {}".format(configPath),
            level=TOMsMessageLog.DEBUG,
        )

        configFile = os.path.abspath(os.path.join(configPath, "TOMs.conf"))
        TOMsMessageLog.logMessage(
            "In getTOMsConfigFile. TOMs_CONFIG_PATH: {}".format(configFile),
            level=TOMsMessageLog.DEBUG,
        )

        if not os.path.isfile(configFile):
            QMessageBox.information(
                None,
                "Information",
                "TOMs configuration file not found. Stopping ...",
                QMessageBox.Ok,
            )
            self.tomsConfigFileNotFound.emit()

        # now read file
        self.readTOMsConfigFile(configFile)

    def readTOMsConfigFile(self, configFile):

        try:
            self.config.read(configFile)
        except Exception as e:
            TOMsMessageLog.logMessage(
                "In TOMsConfigFile.init. Error reading config file ... {}".format(e),
                level=Qgis.Warning,
            )
            self.tomsConfigFileNotFound.emit()

    def getTOMsConfigElement(self, section, value):
        item = None
        try:
            item = self.config[section][value]
        except KeyError:
            TOMsMessageLog.logMessage(
                "In getTOMsConfigElement. not able to find: {}:{}".format(section, value),
                level=Qgis.Info,
            )

        return item


class TOMsLayers(QObject):
    tomsLayersNotFound = pyqtSignal()
    """ signal will be emitted if there is a problem with opening TOMs - typically a layer missing """
    tomsLayersSet = pyqtSignal()
    """ signal will be emitted if everything is OK with opening TOMs """

    def __init__(self):
        QObject.__init__(self)

        TOMsMessageLog.logMessage("In TOMSLayers.init ...", level=Qgis.Info)

        self.tomsLayerDict = {}
        self.formPath = ""
        self.tomsLayerList = None
        self.configFileObject = None

    def getTOMsLayerListFromConfigFile(self, configFileObject: "TOMsConfigFile"):
        self.configFileObject = configFileObject
        layers = configFileObject.getTOMsConfigElement("TOMsLayers", "layers")
        if layers:
            self.tomsLayerList = layers.split("\n")
            return True

        self.tomsLayersNotFound.emit()
        return False

    def getTOMsFormPathFromConfigFile(self, configFileObject):
        formPath = configFileObject.getTOMsConfigElement("TOMsLayers", "form_path")
        return os.path.expandvars(formPath)  # expand env var like USERPROFILE

    def setLayers(self, configFileObject):

        TOMsMessageLog.logMessage("In TOMSLayers.getLayers ...", level=Qgis.Info)
        found = True

        # Check for project being open
        project = QgsProject.instance()

        if len(project.fileName()) == 0:
            QMessageBox.information(iface.mainWindow(), "ERROR", "Project not yet open")
            found = False

        else:

            if not self.getTOMsLayerListFromConfigFile(configFileObject):
                QMessageBox.information(
                    iface.mainWindow(),
                    "ERROR",
                    "Problem with TOMs config file ...",
                )
                self.tomsLayersNotFound.emit()
                found = False

            self.formPath = self.getTOMsFormPathFromConfigFile(configFileObject)
            TOMsMessageLog.logMessage(
                "In TOMsLayers:setLayers. formPath is {} ...".format(self.formPath),
                level=Qgis.Info,
            )

            # check that path exists
            if not os.path.isdir(self.formPath):
                QMessageBox.information(
                    iface.mainWindow(),
                    "ERROR",
                    "Form path in config file was not found ...",
                )
                self.tomsLayersNotFound.emit()
                found = False

        if found:
            for layer in self.tomsLayerList:
                if QgsProject.instance().mapLayersByName(layer):
                    self.tomsLayerDict[layer] = QgsProject.instance().mapLayersByName(layer)[0]
                    # set paths for forms
                    layerEditFormConfig = self.tomsLayerDict[layer].editFormConfig()

                    if len(layerEditFormConfig.initFilePath()) > 0:
                        TOMsMessageLog.logMessage(
                            "In TOMsLayers:setLayers. cleaning useless initFilePath for layer {}...".format(layer),
                            level=Qgis.Info,
                        )
                        layerEditFormConfig.setInitFilePath("")
                        self.tomsLayerDict[layer].setEditFormConfig(layerEditFormConfig)

                    uiPath = layerEditFormConfig.uiForm()
                    if len(uiPath) > 0:
                        TOMsMessageLog.logMessage(
                            "In TOMsLayers:setLayers. current ui_path for layer {} is {} ...".format(layer, uiPath),
                            level=Qgis.Info,
                        )
                        # try to get basename - doesn't seem to work on Linux
                        # base_ui_path = os.path.basename(ui_path)
                        pathAbsolute = os.path.abspath(os.path.join(self.formPath, os.path.basename(uiPath)))
                        if not os.path.isfile(pathAbsolute):
                            TOMsMessageLog.logMessage(
                                "In TOMsLayers:setLayers. form path not found for layer {} ...".format(layer),
                                level=Qgis.Warning,
                            )
                        else:
                            TOMsMessageLog.logMessage(
                                "In TOMsLayers:setLayers. setting new path for form {} ...".format(pathAbsolute),
                                level=Qgis.Info,
                            )
                            layerEditFormConfig.setUiForm(pathAbsolute)
                            self.tomsLayerDict[layer].setEditFormConfig(layerEditFormConfig)

                            # TODO: may need to reinstate original values here - so save them somewhere useful
                    else:
                        TOMsMessageLog.logMessage(
                            "In TOMsLayers:setLayers. no ui_path for layer {}".format(layer),
                            level=Qgis.Info,
                        )

                else:
                    QMessageBox.information(
                        iface.mainWindow(),
                        "ERROR",
                        "Table " + layer + " is not present",
                    )
                    found = False
                    break

        # TODO: need to deal with any errors arising ...

        if not found:
            self.tomsLayersNotFound.emit()

    def removePathFromLayerForms(self):

        TOMsMessageLog.logMessage("In TOMSLayers.removePathFromLayerForms ...", level=Qgis.Info)

        # Check for project being open
        project = QgsProject.instance()

        if len(project.fileName()) == 0:
            QMessageBox.information(iface.mainWindow(), "ERROR", ("Project not yet open"))

        else:

            for layer in self.tomsLayerList:
                if QgsProject.instance().mapLayersByName(layer):
                    self.tomsLayerDict[layer] = QgsProject.instance().mapLayersByName(layer)[0]
                    # set paths for forms
                    layerEditFormConfig = self.tomsLayerDict[layer].editFormConfig()
                    uiPath = layerEditFormConfig.uiForm()
                    TOMsMessageLog.logMessage(
                        "In TOMsLayers:removePathFromLayerForms. ui_path for layer {} is {} ...".format(layer, uiPath),
                        level=Qgis.Info,
                    )
                    if len(self.formPath) > 0 and len(uiPath) > 0:
                        # try to get basename - doesn't seem to work on Linux
                        # base_ui_path = os.path.basename(ui_path)
                        formName = os.path.basename(uiPath)
                        layerEditFormConfig.setUiForm(formName)
                        self.tomsLayerDict[layer].setEditFormConfig(layerEditFormConfig)

                else:
                    QMessageBox.information(
                        iface.mainWindow(),
                        "ERROR",
                        ("Table " + layer + " is not present"),
                    )
                    break

    def getLayer(self, layer):
        return self.tomsLayerDict.get(layer)


class TOMsLabelLayerNames(QObject):
    def __init__(self, currRestrictionLayer):
        QObject.__init__(self)

        TOMsMessageLog.logMessage(
            "In TOMsLabelLayerName:initialising .... {}".format(currRestrictionLayer),
            level=Qgis.Warning,
        )

        self.labelLayerName = self.setCurrLabelLayerNames(currRestrictionLayer)
        self.labelLeaderLayersNames = self.setCurrLabelLeaderLayerNames(currRestrictionLayer)

    def setCurrLabelLayerNames(self, currRestrictionLayer):
        # given a layer return the associated layer with label geometry
        # get the corresponding label layer

        if currRestrictionLayer.name() == "Bays":
            labelLayerName = ["Bays.label_pos"]
        if currRestrictionLayer.name() == "Lines":
            labelLayerName = ["Lines.label_pos", "Lines.label_loading_pos"]
        if currRestrictionLayer.name() == "Signs":
            labelLayerName = []
        if currRestrictionLayer.name() == "RestrictionPolygons":
            labelLayerName = ["RestrictionPolygons.label_pos"]
        if currRestrictionLayer.name() == "CPZs":
            labelLayerName = ["CPZs.label_pos"]
        if currRestrictionLayer.name() == "ParkingTariffAreas":
            labelLayerName = ["ParkingTariffAreas.label_pos"]

        if len(labelLayerName) == 0:
            return [""]

        return labelLayerName

    def getCurrLabelLayerNames(self):
        # given a layer return the associated layer with label geometry
        # get the corresponding label layer

        return self.labelLayerName

    def setCurrLabelLeaderLayerNames(self, currRestrictionLayer):
        # given a layer return the associated layer with label geometry
        # get the corresponding label layer

        if currRestrictionLayer.name() == "Bays":
            labelLeaderLayersNames = ["Bays.label_ldr"]
        if currRestrictionLayer.name() == "Lines":
            labelLeaderLayersNames = ["Lines.label_ldr", "Lines.label_loading_ldr"]
        if currRestrictionLayer.name() == "Signs":
            labelLeaderLayersNames = []
        if currRestrictionLayer.name() == "RestrictionPolygons":
            labelLeaderLayersNames = ["RestrictionPolygons.label_ldr"]
        if currRestrictionLayer.name() == "CPZs":
            labelLeaderLayersNames = ["CPZs.label_ldr"]
        if currRestrictionLayer.name() == "ParkingTariffAreas":
            labelLeaderLayersNames = ["ParkingTariffAreas.label_ldr"]

        if len(labelLeaderLayersNames) == 0:
            return [""]

        return labelLeaderLayersNames

    def getCurrLabelLeaderLayerNames(self):
        return self.labelLeaderLayersNames
