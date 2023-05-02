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

import uuid

from qgis.core import (
    Qgis,
    QgsExpression,
    QgsExpressionContext,
    QgsExpressionContextUtils,
    QgsFeature,
    QgsFeatureRequest,
    QgsGeometry,
    QgsProject,
    QgsSettings,
    QgsTracer,
    QgsUnitTypes,
    QgsVectorLayer,
    QgsWkbTypes,
)
from qgis.gui import QgsMapToolDigitizeFeature, QgsMapToolIdentify
from qgis.PyQt.QtCore import Qt, QTimer
from qgis.PyQt.QtWidgets import QMessageBox, QToolTip
from qgis.utils import iface

from .constants import RestrictionAction
from .core.tomsMessageLog import TOMsMessageLog
from .generateGeometryUtils import GenerateGeometryUtils
from .restrictionDialog import RestrictionDialogWrapper
from .restrictionTypeUtilsClass import TOMsLabelLayerNames
from .utils import setupPanelTabs


class CreateRestrictionTool(QgsMapToolDigitizeFeature):
    def __init__(self):

        super().__init__(iface.mapCanvas(), iface.cadDockWidget())
        self.setAdvancedDigitizingAllowed(True)
        self.setAutoSnapEnabled(True)
        self.digitizingCompleted.connect(self.addFeature)

        TOMsMessageLog.logMessage(
            "In CreateRestrictionTool. Finished init.", level=Qgis.Info
        )

    def addFeature(self, feature):
        layerName = self.layer().name()

        if layerName == "ConstructionLines":
            self.layer().addFeature(feature)
            self.layer().commitChanges()
            return

        TOMsMessageLog.logMessage("In setDefaultRestrictionDetails: ", level=Qgis.Info)

        restrictionId = str(uuid.uuid4())
        feature["RestrictionID"] = restrictionId
        GenerateGeometryUtils.setRoadName(feature)

        if self.layer().geometryType() == 1:  # Line or Bay
            GenerateGeometryUtils.setAzimuthToRoadCentreLine(feature)

        currentCPZ, cpzWaitingTimeID = GenerateGeometryUtils.getCurrentCPZDetails(
            feature
        )
        currentED, edWaitingTimeID = GenerateGeometryUtils.getCurrentEventDayDetails(
            feature
        )

        if layerName != "Signs":
            feature.setAttribute("CPZ", currentCPZ)
            feature.setAttribute("MatchDayEventDayZone", currentED)

        # TODO: get the last used values ... look at field ...

        if layerName == "Lines":
            # feature.setAttribute("RestrictionTypeID", 224)  # 10 = SYL (Lines)
            feature.setAttribute(
                "RestrictionTypeID", QgsSettings().value("Lines/RestrictionTypeID", 224)
            )
            # feature.setAttribute("GeomShapeID", 10)   # 10 = Parallel Line
            feature.setAttribute(
                "GeomShapeID", QgsSettings().value("Lines/GeomShapeID", 10)
            )
            feature.setAttribute("NoWaitingTimeID", cpzWaitingTimeID)
            feature.setAttribute("MatchDayTimePeriodID", edWaitingTimeID)
            # feature.setAttribute("Lines_DateTime", currDate)

        elif layerName == "Bays":
            # feature.setAttribute("RestrictionTypeID", 101)  # 28 = Permit Holders Bays (Bays)
            feature.setAttribute(
                "RestrictionTypeID",
                QgsSettings().value("Bays/RestrictionTypeID", 101),
            )  # 28 = Permit Holders Bays (Bays)
            feature.setAttribute(
                "GeomShapeID",
                QgsSettings().value("Bays/GeomShapeID", 21),
            )  # 21 = Parallel Bay (Polygon)
            # feature.setAttribute("GeomShapeID", 21)   # 21 = Parallel Bay (Polygon)
            feature.setAttribute("NrBays", -1)

            feature.setAttribute("TimePeriodID", cpzWaitingTimeID)
            feature.setAttribute("MatchDayTimePeriodID", edWaitingTimeID)

            (
                currentPTA,
                ptaMaxStayID,
                ptaNoReturnID,
            ) = GenerateGeometryUtils.getCurrentPTADetails(feature)

            feature.setAttribute("MaxStayID", ptaMaxStayID)
            feature.setAttribute("NoReturnID", ptaNoReturnID)
            feature.setAttribute("ParkingTariffArea", currentPTA)

            try:
                payParkingAreasLayer = QgsProject.instance().mapLayersByName(
                    "PayParkingAreas"
                )[0]
                currPayParkingArea = GenerateGeometryUtils.getPolygonForRestriction(
                    feature, payParkingAreasLayer
                )
                feature.setAttribute(
                    "PayParkingAreaID", currPayParkingArea.attribute("Code")
                )
            except Exception as e:
                TOMsMessageLog.logMessage(
                    "In setDefaultRestrictionDetails:payParkingArea: error: {}".format(
                        e
                    ),
                    level=Qgis.Info,
                )

        elif layerName == "Signs":
            # feature.setAttribute("SignType_1", 28)  # 28 = Permit Holders Only (Signs)
            feature.setAttribute(
                "SignType_1",
                QgsSettings().value("Signs/SignType_1", 28),
            )

        elif layerName == "RestrictionPolygons":
            # feature.setAttribute("RestrictionTypeID", 4)  # 28 = Residential mews area (RestrictionPolygons)
            feature.setAttribute(
                "RestrictionTypeID",
                QgsSettings().value("RestrictionPolygons/RestrictionTypeID", 4),
            )
            feature.setAttribute("MatchDayTimePeriodID", edWaitingTimeID)

        else:
            raise NotImplementedError(f"Layer {layerName} not implemented")

        dialog = RestrictionDialogWrapper(self.layer(), feature)
        dialog.show()


class SelectRestrictionTool(QgsMapToolIdentify):
    """
    This tool is needed because we only need to select a restriction but with
    a pop-up menu like QGIS info tool creates.
    Also, we need to take into account the symbol and not the real feature
    geometry for bays and restriction lines, for searching features around the
    mouse pointer.
    This tool also pops up the selection menu when the mouse does not move for
    a little delay.
    """

    def __init__(self):
        super().__init__(iface.mapCanvas())

        # If mouse did not move for <interval> milliseconds, process
        self.timer = QTimer(self.canvas())
        self.timer.setSingleShot(True)
        self.timer.setInterval(700)
        self.timer.timeout.connect(self.showMapTip)

        self.layers = None
        self.deltaSearchRadius = None

        self.identifyMenu().setExecWithSingleResult(True)
        self.identifyMenu().setAllowMultipleReturn(False)

    def activate(self):
        super().activate()

        # We want to search with a radius of <deltaSearchRadius> meters more than the default radius
        if self.canvas().mapUnits() != QgsUnitTypes.Standard:
            QMessageBox.critical(
                None, "Errror", "Need a map with a standard measurement unit"
            )
            self.canvas().unsetMapTool(self)
            return

        self.deltaSearchRadius = 4 * QgsUnitTypes.fromUnitToUnitFactor(
            QgsUnitTypes.DistanceMeters, self.canvas().mapUnits()
        )

        # Find layers
        try:
            restrictionLayers = QgsProject.instance().mapLayersByName(
                "RestrictionLayers"
            )[0]
        except IndexError:
            QMessageBox.critical(
                None, "Errror", "RestrictionLayers layer is not loaded"
            )
            self.canvas().unsetMapTool(self)
            return

        self.layers = []
        for layerDetails in restrictionLayers.getFeatures():
            if (
                layerDetails.attribute("Code") >= 6
            ):  # CPZs, PTAs  - TODO: Need to improve
                allowZoneEditing = QgsExpressionContextUtils.projectScope(
                    QgsProject.instance()
                ).variable("AllowZoneEditing")
                if allowZoneEditing != "True":
                    continue
                TOMsMessageLog.logMessage(
                    "In getRestrictionsUnderPoint: Zone editing enabled: ",
                    level=Qgis.Info,
                )

            self.layers.append(
                QgsProject.instance().mapLayersByName(
                    layerDetails.attribute("RestrictionLayerName")
                )[0]
            )

    def showMapTip(self):
        pos = self.canvas().mouseLastXY()
        textList = []
        for identifyResult in self.process(pos):
            expContext = QgsExpressionContext(
                QgsExpressionContextUtils.globalProjectLayerScopes(
                    identifyResult.mLayer
                )
            )
            expContext.setFeature(identifyResult.mFeature)
            exp = QgsExpression(identifyResult.mLayer.displayExpression())
            textList.append(exp.evaluate(expContext))
        QToolTip.showText(
            self.canvas().mapToGlobal(pos),
            "\n".join([text for text in textList if text is not None]),
        )

    def canvasMoveEvent(self, event):  # pylint: disable=unused-argument
        self.timer.start()

    def canvasReleaseEvent(self, event):
        self.timer.stop()

        # Show menu and get the feature selected by the user
        selectedResults = self.identifyMenu().exec(
            self.process(event.pos()),
            self.canvas().mapToGlobal(event.pos()),
        )
        if len(selectedResults) != 1:
            return

        # Select the feature
        iface.activeLayer().removeSelection()
        iface.setActiveLayer(selectedResults[0].mLayer)
        selectedResults[0].mLayer.selectByIds([selectedResults[0].mFeature.id()])

    def process(self, pos):
        point = QgsGeometry.fromPointXY(self.toMapCoordinates(pos))
        defaultSearchRadius = QgsMapToolIdentify.searchRadiusMU(self.canvas())

        # First find features within default search radius + delta
        self.setCanvasPropertiesOverrides(defaultSearchRadius + self.deltaSearchRadius)
        largeResults = self.identify(
            pos.x(), pos.y(), self.layers, QgsMapToolIdentify.TopDownAll
        )

        # Switch line geometries (i.e. bays and restriction lines) into generated symbols
        # and keep features which intersects the default search radius
        exp = QgsExpression("generateDisplayGeometry()")
        expContext = QgsExpressionContext()
        finalResults = []
        for identifyResult in largeResults:
            if identifyResult.mFeature.geometry().type() == QgsWkbTypes.LineGeometry:
                expContext.setFeature(identifyResult.mFeature)
                identifyResult.mFeature.setGeometry(exp.evaluate(expContext))
            if (
                identifyResult.mFeature.geometry().distance(point)
                <= defaultSearchRadius
            ):
                finalResults.append(identifyResult)

        return finalResults


def checkSplitGeometries(currentProposal):
    """
    When a geometry is split we need to deal with the new feature, and check whether
    or not the feature is part of the current proposal
    """

    TOMsMessageLog.logMessage("In checkSplitGeometries ... ", level=Qgis.Info)
    origLayer = iface.activeLayer()

    # Getting split feature and new features
    featList = list(origLayer.editBuffer().changedGeometries().keys())
    if len(featList) > 1:
        raise ValueError("More than one feature split")
    modifiedFeature = origLayer.getFeature(featList[0])
    newFeatures = list(origLayer.editBuffer().addedFeatures().values())

    restrictionsInProposalsLayer = QgsProject.instance().mapLayersByName(
        "RestrictionsInProposals"
    )[0]
    restrictionsLayers = QgsProject.instance().mapLayersByName("RestrictionLayers")[0]
    currRestrictionLayerID = next(
        restrictionsLayers.getFeatures(
            QgsFeatureRequest().setFilterExpression(
                f'"RestrictionLayerName" = \'{origLayer.name().split(".")[0]}\''
            )
        )
    ).attribute("code")

    for newFeature in newFeatures:
        restrictionId = newFeature["RestrictionID"]
        origLayer.changeAttributeValues(
            newFeature.id(),
            {
                newFeature.fieldNameIndex("OpenDate"): None,
                newFeature.fieldNameIndex("CloseDate"): None,
            },
        )
        newRestrictionInProposal = QgsFeature(restrictionsInProposalsLayer.fields())
        newRestrictionInProposal.setGeometry(QgsGeometry())
        newRestrictionInProposal["ProposalID"] = currentProposal
        newRestrictionInProposal["RestrictionID"] = restrictionId
        newRestrictionInProposal["RestrictionTableID"] = currRestrictionLayerID
        newRestrictionInProposal[
            "ActionOnProposalAcceptance"
        ] = RestrictionAction.OPEN.value
        if not restrictionsInProposalsLayer.addFeature(newRestrictionInProposal):
            raise Exception(
                "Unable to add feature\n"
                + "\n".join(restrictionsInProposalsLayer.commitErrors())
            )

    # Check if the split feature was in the current proposal
    restrictionFound = (
        len(
            list(
                restrictionsInProposalsLayer.getFeatures(
                    QgsFeatureRequest().setFilterExpression(
                        f'"RestrictionID" = \'{modifiedFeature["RestrictionID"]}\' and '
                        f'"RestrictionTableID" = {currRestrictionLayerID} and '
                        f'"ProposalID" = {currentProposal}'
                    )
                )
            )
        )
        == 1
    )
    if not restrictionFound:
        #  This one is not in the current Proposal, so now we need to:
        #  - create a new feature, duplicate of modifiedFeature but with a new ID
        #  - add it to the layer
        #  - give back the original geometry to the modified feature
        #  - add the details to RestrictionsInProposal

        newFeature = QgsFeature(origLayer.fields())
        newFeature.setAttributes(modifiedFeature.attributes())
        newFeature.setGeometry(modifiedFeature.geometry())
        restrictionId = str(uuid.uuid4())
        newFeature["RestrictionID"] = restrictionId
        newFeature["OpenDate"] = None
        newFeature["CloseDate"] = None
        if not origLayer.addFeature(newFeature):
            raise Exception(
                "Unable to add feature\n" + "\n".join(origLayer.commitErrors())
            )

        for action, currRestrictionId in [
            (RestrictionAction.CLOSE, modifiedFeature["RestrictionID"]),
            (RestrictionAction.OPEN, restrictionId),
        ]:
            newRestrictionInProposal = QgsFeature(restrictionsInProposalsLayer.fields())
            newRestrictionInProposal.setGeometry(QgsGeometry())
            newRestrictionInProposal["ProposalID"] = currentProposal
            newRestrictionInProposal["RestrictionID"] = currRestrictionId
            newRestrictionInProposal["RestrictionTableID"] = currRestrictionLayerID
            newRestrictionInProposal["ActionOnProposalAcceptance"] = action.value
            if not restrictionsInProposalsLayer.addFeature(newRestrictionInProposal):
                raise Exception(
                    "Unable to add feature\n"
                    + "\n".join(restrictionsInProposalsLayer.commitErrors())
                )

        unmodifiedLayer = QgsVectorLayer(origLayer.source(), "", "postgres")
        originalGeometry = list(
            unmodifiedLayer.getFeatures(
                f'"RestrictionID" = \'{modifiedFeature["RestrictionID"]}\''
            )
        )[0].geometry()
        origLayer.changeGeometry(modifiedFeature.id(), originalGeometry)

    else:
        # Clear dates but keep everything else
        modifiedFeature["OpenDate"] = None
        modifiedFeature["CloseDate"] = None

    origLayer.removeSelection()


def checkEditedGeometries(currentProposal):
    """
    When a geometry is changed we need to check whether or not the feature is part of the current proposal
    """

    TOMsMessageLog.logMessage("In checkEditedGeometries ... ", level=Qgis.Info)
    origLayer = iface.activeLayer()

    restrictionsInProposalsLayer = QgsProject.instance().mapLayersByName(
        "RestrictionsInProposals"
    )[0]
    restrictionsLayers = QgsProject.instance().mapLayersByName("RestrictionLayers")[0]

    featList = list(origLayer.editBuffer().changedGeometries().keys())
    if len(featList) > 1:
        raise ValueError("More than one feature edited")
    featId = featList[0]
    currRestriction = origLayer.getFeature(featId)
    currRestrictionLayerID = next(
        restrictionsLayers.getFeatures(
            QgsFeatureRequest().setFilterExpression(
                f'"RestrictionLayerName" = \'{origLayer.name().split(".")[0]}\''
            )
        )
    ).attribute("code")
    restrictionFound = (
        len(
            list(
                restrictionsInProposalsLayer.getFeatures(
                    QgsFeatureRequest().setFilterExpression(
                        f'"RestrictionID" = \'{currRestriction["RestrictionID"]}\' and '
                        f'"RestrictionTableID" = {currRestrictionLayerID} and '
                        f'"ProposalID" = {currentProposal}'
                    )
                )
            )
        )
        == 1
    )
    if not restrictionFound:
        #  This one is not in the current Proposal, so now we need to:
        #  - generate a new ID and assign it to the feature for which the geometry has changed
        #  - switch the geometries arround so that the original feature has the original geometry
        #    and the new feature has the new geometry
        #  - add the details to RestrictionsInProposal

        # Create a copy of the feature
        newFeature = QgsFeature(origLayer.fields())
        newFeature.setAttributes(currRestriction.attributes())
        newFeature.setGeometry(currRestriction.geometry())
        newRestrictionID = str(uuid.uuid4())
        newFeature["RestrictionID"] = newRestrictionID
        newFeature["OpenDate"] = None
        newFeature["GeometryID"] = None
        if not origLayer.addFeature(newFeature):
            raise Exception(
                "Unable to add feature\n" + "\n".join(origLayer.commitErrors())
            )

        unmodifiedLayer = QgsVectorLayer(origLayer.source(), "", "postgres")
        originalGeometry = list(
            unmodifiedLayer.getFeatures(
                f'"RestrictionID" = \'{currRestriction["RestrictionID"]}\''
            )
        )[0].geometry()
        origLayer.changeGeometry(featId, originalGeometry)

        for action, restrictionId in [
            (RestrictionAction.CLOSE, currRestriction["RestrictionID"]),
            (RestrictionAction.OPEN, newRestrictionID),
        ]:
            newRestrictionInProposal = QgsFeature(restrictionsInProposalsLayer.fields())
            newRestrictionInProposal.setGeometry(QgsGeometry())
            newRestrictionInProposal["ProposalID"] = currentProposal
            newRestrictionInProposal["RestrictionID"] = restrictionId
            newRestrictionInProposal["RestrictionTableID"] = currRestrictionLayerID
            newRestrictionInProposal["ActionOnProposalAcceptance"] = action.value
            if not restrictionsInProposalsLayer.addFeature(newRestrictionInProposal):
                raise Exception(
                    "Unable to add feature\n"
                    + "\n".join(restrictionsInProposalsLayer.commitErrors())
                )

        # If there are label layers, update those so that new feature is available
        layerDetails = TOMsLabelLayerNames(origLayer)
        for labelLayerName in layerDetails.getCurrLabelLayerNames():
            try:
                labelLayer = QgsProject.instance().mapLayersByName(labelLayerName)[0]
                labelLayer.reload()
            except IndexError:
                pass
