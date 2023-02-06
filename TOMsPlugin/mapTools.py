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
from qgis.gui import QgsMapToolCapture, QgsMapToolIdentify
from qgis.PyQt.QtCore import Qt, QTimer
from qgis.PyQt.QtWidgets import QMessageBox, QToolTip
from qgis.utils import iface

from .constants import RestrictionAction
from .core.tomsMessageLog import TOMsMessageLog
from .generateGeometryUtils import GenerateGeometryUtils
from .restrictionDialog import RestrictionDialogWrapper
from .restrictionTypeUtilsClass import TOMsLabelLayerNames
from .utils import setupPanelTabs


class CreateRestrictionTool(QgsMapToolCapture):
    # helpful link - http://apprize.info/python/qgis/7.html ??
    def __init__(self, proposalsManager):

        QgsMapToolCapture.__init__(
            self,
            iface.mapCanvas(),
            iface.cadDockWidget(),
            QgsMapToolCapture.CaptureNone,
        )

        # self.dialog = dialog
        self.proposalsManager = proposalsManager

        self.setAdvancedDigitizingAllowed(True)
        self.setAutoSnapEnabled(True)

        # I guess at this point, it is possible to set things like capture mode,
        # snapping preferences, ... (not sure of all the elements that are required)
        # capture mode (... not sure if this has already been set? - or how to set it)

        # set up tracing configuration
        self.tomsTracer = QgsTracer()

        # set an extent for the Tracer
        tracerExtent = iface.mapCanvas().extent()
        tolerance = 1000.0
        tracerExtent.setXMaximum(tracerExtent.xMaximum() + tolerance)
        tracerExtent.setYMaximum(tracerExtent.yMaximum() + tolerance)
        tracerExtent.setXMinimum(tracerExtent.xMinimum() - tolerance)
        tracerExtent.setYMinimum(tracerExtent.yMinimum() - tolerance)

        self.tomsTracer.setExtent(tracerExtent)

        TOMsMessageLog.logMessage(
            "In CreateRestrictionTool. Finished init.", level=Qgis.Info
        )

    def activate(self):
        advancedDigitizingPanel = iface.cadDockWidget()
        advancedDigitizingPanel.setVisible(True)
        advancedDigitizingPanel.enable()
        if not advancedDigitizingPanel.enableAction().isChecked():
            advancedDigitizingPanel.enableAction().trigger()
        setupPanelTabs(advancedDigitizingPanel)

        self.layer().startEditing()
        traceLayers = [QgsProject.instance().mapLayersByName("RoadCasement")[0]]
        self.tomsTracer.setLayers(traceLayers)
        QgsMapToolCapture.activate(self)

        self.lastPoint = None
        self.currPoint = None
        self.lastEvent = None
        self.result = None
        self.nrPoints = None

        # Seems that this is important - or at least to create a point list that is used later to create Geometry
        self.sketchPoints = self.points()

        # Set up rubber band. In current implementation, it is not showing feeback for "next" location

        self.rubberBand = self.createRubberBand(
            QgsWkbTypes.LineGeometry
        )  # what about a polygon ??

        QgsMapToolCapture.activate(self)

    def cadCanvasReleaseEvent(self, event):
        QgsMapToolCapture.cadCanvasReleaseEvent(self, event)
        TOMsMessageLog.logMessage(
            ("In Create - cadCanvasReleaseEvent"), level=Qgis.Info
        )

        if event.button() == Qt.LeftButton:
            if not self.isCapturing():
                self.startCapturing()
            TOMsMessageLog.logMessage(
                f"In Create - cadCanvasReleaseEvent: checkSnapping = {event.isSnapped}",
                level=Qgis.Info,
            )

            # Now wanting to add point(s) to new shape. Take account of snapping and tracing
            self.currPoint = event.snapPoint()
            self.lastEvent = event

            if self.lastPoint is None:  # First point
                self.result = self.addVertex(self.currPoint)
                TOMsMessageLog.logMessage(
                    "In Create - cadCanvasReleaseEvent: adding vertex 0 "
                    + str(self.result),
                    level=Qgis.Info,
                )

            else:
                # check for shortest line
                resVectorList = self.tomsTracer.findShortestPath(
                    self.lastPoint, self.currPoint
                )

                TOMsMessageLog.logMessage(
                    "In Create - cadCanvasReleaseEvent: traceList" + str(resVectorList),
                    level=Qgis.Info,
                )
                TOMsMessageLog.logMessage(
                    "In Create - cadCanvasReleaseEvent: traceList"
                    + str(resVectorList[1]),
                    level=Qgis.Info,
                )
                if resVectorList[1] == 0:
                    # path found, add the points to the list
                    TOMsMessageLog.logMessage(
                        "In Create - cadCanvasReleaseEvent (found path) ",
                        level=Qgis.Info,
                    )

                    # self.points.extend(resVectorList)
                    initialPoint = True
                    for point in resVectorList[0]:
                        if not initialPoint:

                            TOMsMessageLog.logMessage(
                                (
                                    "In CreateRestrictionTool - cadCanvasReleaseEvent (found path) X:"
                                    + str(point.x())
                                    + " Y: "
                                    + str(point.y())
                                ),
                                level=Qgis.Info,
                            )

                            self.result = self.addVertex(point)

                        initialPoint = False

                    TOMsMessageLog.logMessage(
                        ("In Create - cadCanvasReleaseEvent (added shortest path)"),
                        level=Qgis.Info,
                    )

                else:
                    # error encountered, add just the curr point ??

                    self.result = self.addVertex(self.currPoint)
                    TOMsMessageLog.logMessage(
                        (
                            "In CreateRestrictionTool - (adding shortest path) X:"
                            + str(self.currPoint.x())
                            + " Y: "
                            + str(self.currPoint.y())
                        ),
                        level=Qgis.Info,
                    )

            self.lastPoint = self.currPoint

            TOMsMessageLog.logMessage(
                (
                    "In Create - cadCanvasReleaseEvent (AddVertex/Line) Result: "
                    + str(self.result)
                    + " X:"
                    + str(self.currPoint.x())
                    + " Y:"
                    + str(self.currPoint.y())
                ),
                level=Qgis.Info,
            )

        elif event.button() == Qt.RightButton:
            # Stop capture when right button or escape key is pressed
            # points = self.getCapturedPoints()
            self.getPointsCaptured()

            # Need to think about the default action here if none of these buttons/keys are pressed.

    def keyPressEvent(self, event):
        if (
            (event.key() == Qt.Key_Backspace)
            or (event.key() == Qt.Key_Delete)
            or (event.key() == Qt.Key_Escape)
        ):
            self.undo()
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            # TODO: Need to think about the default action here if none of these buttons/keys are pressed.
            pass

    def getPointsCaptured(self):
        TOMsMessageLog.logMessage(
            "In CreateRestrictionTool - getPointsCaptured", level=Qgis.Info
        )

        # Check the number of points
        self.nrPoints = self.size()
        TOMsMessageLog.logMessage(
            (
                "In CreateRestrictionTool - getPointsCaptured; Stopping: "
                + str(self.nrPoints)
            ),
            level=Qgis.Info,
        )

        self.sketchPoints = self.points()

        for point in self.sketchPoints:
            TOMsMessageLog.logMessage(
                (
                    "In CreateRestrictionTool - getPointsCaptured X:"
                    + str(point.x())
                    + " Y: "
                    + str(point.y())
                ),
                level=Qgis.Info,
            )

        # stop capture activity
        self.stopCapturing()

        if self.nrPoints > 0:

            # take points from the rubber band and copy them into the "feature"

            fields = self.layer().dataProvider().fields()
            feature = QgsFeature()
            feature.setFields(fields)

            TOMsMessageLog.logMessage(
                (
                    "In CreateRestrictionTool. getPointsCaptured, layerType: "
                    + str(self.layer().geometryType())
                ),
                level=Qgis.Info,
            )

            if self.layer().geometryType() == 0:  # Point
                feature.setGeometry(QgsGeometry.fromPointXY(self.sketchPoints[0]))
            elif self.layer().geometryType() == 1:  # Line
                if len(self.sketchPoints) < 2:
                    QMessageBox.information(
                        None, "Error", "Line with only one point", QMessageBox.Ok
                    )
                    return
                feature.setGeometry(QgsGeometry.fromPolylineXY(self.sketchPoints))
            elif self.layer().geometryType() == 2:  # Polygon
                feature.setGeometry(QgsGeometry.fromPolygonXY([self.sketchPoints]))
            else:
                TOMsMessageLog.logMessage(
                    ("In CreateRestrictionTool - no geometry type found"),
                    level=Qgis.Info,
                )
                return

            # Currently geometry is not being created correct. Might be worth checking co-ord values ...

            TOMsMessageLog.logMessage(
                (
                    "In Create - getPointsCaptured; geometry prepared; "
                    + str(feature.geometry().asWkt())
                ),
                level=Qgis.Info,
            )

            if self.layer().name() == "ConstructionLines":
                self.layer().addFeature(feature)
            else:

                self.setDefaultRestrictionDetails(feature, self.layer())
                TOMsMessageLog.logMessage(
                    "In CreateRestrictionTool - getPointsCaptured. currRestrictionLayer: "
                    + str(self.layer().name()),
                    level=Qgis.Info,
                )

                newRestrictionID = str(uuid.uuid4())
                feature["RestrictionID"] = newRestrictionID

                dialog = RestrictionDialogWrapper(self.layer(), feature)
                dialog.show()

    def setDefaultRestrictionDetails(self, currRestriction, currRestrictionLayer):
        # FIXME: tellement de commentaire, au final pas de date settée ?
        TOMsMessageLog.logMessage("In setDefaultRestrictionDetails: ", level=Qgis.Info)

        GenerateGeometryUtils.setRoadName(currRestriction)
        if currRestrictionLayer.geometryType() == 1:  # Line or Bay
            GenerateGeometryUtils.setAzimuthToRoadCentreLine(currRestriction)
            # currRestriction.setAttribute("RestrictionLength", currRestriction.geometry().length())

        currentCPZ, cpzWaitingTimeID = GenerateGeometryUtils.getCurrentCPZDetails(
            currRestriction
        )
        currentED, edWaitingTimeID = GenerateGeometryUtils.getCurrentEventDayDetails(
            currRestriction
        )

        if currRestrictionLayer.name() != "Signs":
            currRestriction.setAttribute("CPZ", currentCPZ)
            currRestriction.setAttribute("MatchDayEventDayZone", currentED)

        # TODO: get the last used values ... look at field ...

        if currRestrictionLayer.name() == "Lines":
            # currRestriction.setAttribute("RestrictionTypeID", 224)  # 10 = SYL (Lines)
            currRestriction.setAttribute(
                "RestrictionTypeID", QgsSettings().value("Lines/RestrictionTypeID", 224)
            )
            # currRestriction.setAttribute("GeomShapeID", 10)   # 10 = Parallel Line
            currRestriction.setAttribute(
                "GeomShapeID", QgsSettings().value("Lines/GeomShapeID", 10)
            )
            currRestriction.setAttribute("NoWaitingTimeID", cpzWaitingTimeID)
            currRestriction.setAttribute("MatchDayTimePeriodID", edWaitingTimeID)
            # currRestriction.setAttribute("Lines_DateTime", currDate)

        elif currRestrictionLayer.name() == "Bays":
            # currRestriction.setAttribute("RestrictionTypeID", 101)  # 28 = Permit Holders Bays (Bays)
            currRestriction.setAttribute(
                "RestrictionTypeID",
                QgsSettings().value("Bays/RestrictionTypeID", 101),
            )  # 28 = Permit Holders Bays (Bays)
            currRestriction.setAttribute(
                "GeomShapeID",
                QgsSettings().value("Bays/GeomShapeID", 21),
            )  # 21 = Parallel Bay (Polygon)
            # currRestriction.setAttribute("GeomShapeID", 21)   # 21 = Parallel Bay (Polygon)
            currRestriction.setAttribute("NrBays", -1)

            currRestriction.setAttribute("TimePeriodID", cpzWaitingTimeID)
            currRestriction.setAttribute("MatchDayTimePeriodID", edWaitingTimeID)

            (
                currentPTA,
                ptaMaxStayID,
                ptaNoReturnID,
            ) = GenerateGeometryUtils.getCurrentPTADetails(currRestriction)

            currRestriction.setAttribute("MaxStayID", ptaMaxStayID)
            currRestriction.setAttribute("NoReturnID", ptaNoReturnID)
            currRestriction.setAttribute("ParkingTariffArea", currentPTA)

            try:
                payParkingAreasLayer = QgsProject.instance().mapLayersByName(
                    "PayParkingAreas"
                )[0]
                currPayParkingArea = GenerateGeometryUtils.getPolygonForRestriction(
                    currRestriction, payParkingAreasLayer
                )
                currRestriction.setAttribute(
                    "PayParkingAreaID", currPayParkingArea.attribute("Code")
                )
            except Exception as e:
                TOMsMessageLog.logMessage(
                    "In setDefaultRestrictionDetails:payParkingArea: error: {}".format(
                        e
                    ),
                    level=Qgis.Info,
                )

        elif currRestrictionLayer.name() == "Signs":
            # currRestriction.setAttribute("SignType_1", 28)  # 28 = Permit Holders Only (Signs)
            currRestriction.setAttribute(
                "SignType_1",
                QgsSettings().value("Signs/SignType_1", 28),
            )

        elif currRestrictionLayer.name() == "RestrictionPolygons":
            # currRestriction.setAttribute("RestrictionTypeID", 4)  # 28 = Residential mews area (RestrictionPolygons)
            currRestriction.setAttribute(
                "RestrictionTypeID",
                QgsSettings().value("RestrictionPolygons/RestrictionTypeID", 4),
            )
            currRestriction.setAttribute("MatchDayTimePeriodID", edWaitingTimeID)


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
