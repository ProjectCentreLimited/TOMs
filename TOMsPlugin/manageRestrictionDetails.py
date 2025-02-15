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

from qgis.core import Qgis, QgsProject
from qgis.PyQt.QtCore import QCoreApplication, QTimer
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QDockWidget, QMessageBox
from qgis.utils import iface

from .constants import RestrictionAction, UserPermission
from .core.tomsMessageLog import TOMsMessageLog
from .mapTools import (
    CreateRestrictionTool,
    SelectRestrictionTool,
    checkEditedGeometries,
    checkSplitGeometries,
)

# Initialize Qt resources from file resources.py
from .resources import *  # pylint: disable=wildcard-import, unused-wildcard-import
from .restrictionDialog import RestrictionDialogWrapper
from .utils import (
    addRestrictionToProposal,
    deleteRestrictionInProposal,
    getRestrictionLayerTableID,
    restrictionInProposal,
    setupPanelTabs,
)


class ManageRestrictionDetails:
    def __init__(self, tomsToolbar, proposalsManager):
        TOMsMessageLog.logMessage("In manageRestrictionDetails::init", level=Qgis.Info)

        self.proposalsManager = proposalsManager
        self.tomsToolbar = tomsToolbar

        # This will set up the items on the toolbar
        # Create actions
        self.actionSelectRestriction = QAction(
            QIcon(":/plugins/TOMs/resources/mActionSelect.png"),
            QCoreApplication.translate("MyPlugin", "Select"),
            iface.mainWindow(),
        )
        self.actionSelectRestriction.setCheckable(True)

        self.actionRestrictionDetails = QAction(
            QIcon(":/plugins/TOMs/resources/mActionGetInfo.svg"),
            QCoreApplication.translate("MyPlugin", "Get Details"),
            iface.mainWindow(),
        )

        self.actionCreateBayRestriction = QAction(
            QIcon(":/plugins/TOMs/resources/mActionAddTrack.svg"),
            QCoreApplication.translate("MyPlugin", "Create Bay"),
            iface.mainWindow(),
        )
        self.actionCreateBayRestriction.setCheckable(True)

        self.actionCreateLineRestriction = QAction(
            QIcon(":/plugins/TOMs/resources/mActionAddLine.svg"),
            QCoreApplication.translate("MyPlugin", "Create Line"),
            iface.mainWindow(),
        )
        self.actionCreateLineRestriction.setCheckable(True)

        self.actionCreatePolygonRestriction = QAction(
            QIcon(":/plugins/TOMs/resources/rpolygonBy2Corners.svg"),
            QCoreApplication.translate("MyPlugin", "Create Polygon"),
            iface.mainWindow(),
        )
        self.actionCreatePolygonRestriction.setCheckable(True)

        self.actionCreateSignRestriction = QAction(
            QIcon(":/plugins/TOMs/resources/mActionSetEndPoint.svg"),
            QCoreApplication.translate("MyPlugin", "Create Sign"),
            iface.mainWindow(),
        )
        self.actionCreateSignRestriction.setCheckable(True)

        self.actionRemoveRestriction = QAction(
            QIcon(":/plugins/TOMs/resources/mActionDeleteTrack.svg"),
            QCoreApplication.translate("MyPlugin", "Remove Restriction"),
            iface.mainWindow(),
        )

        self.actionEditRestriction = QAction(
            QIcon(":/plugins/TOMs/resources/mActionEdit.svg"),
            QCoreApplication.translate("MyPlugin", "Edit Restriction"),
            iface.mainWindow(),
        )
        self.actionEditRestriction.setCheckable(True)

        self.actionSplitRestriction = QAction(
            QIcon(":/plugins/TOMs/resources/scissors.png"),
            QCoreApplication.translate("MyPlugin", "Split Restriction"),
            iface.mainWindow(),
        )
        self.actionSplitRestriction.setCheckable(True)

        self.actionCreateConstructionLine = QAction(
            QIcon(":/plugins/TOMs/resources/CreateConstructionLine.svg"),
            QCoreApplication.translate("MyPlugin", "Create construction line"),
            iface.mainWindow(),
        )
        self.actionCreateConstructionLine.setCheckable(True)

        # Add actions to the toolbar
        self.tomsToolbar.addAction(self.actionSelectRestriction)
        self.tomsToolbar.addAction(self.actionRestrictionDetails)

        if UserPermission.WRITE:
            self.tomsToolbar.addAction(self.actionCreateBayRestriction)
            self.tomsToolbar.addAction(self.actionCreateLineRestriction)
            self.tomsToolbar.addAction(self.actionCreatePolygonRestriction)
            self.tomsToolbar.addAction(self.actionCreateSignRestriction)
            self.tomsToolbar.addAction(self.actionRemoveRestriction)
            self.tomsToolbar.addAction(self.actionEditRestriction)
            self.tomsToolbar.addAction(self.actionSplitRestriction)
            self.tomsToolbar.addAction(self.actionCreateConstructionLine)

        # Connect action signals to slots
        self.actionRestrictionDetails.triggered.connect(self.doRestrictionDetails)
        self.actionCreateBayRestriction.triggered.connect(
            lambda: self.doCreateRestriction(self.actionCreateBayRestriction)
        )
        self.actionCreateLineRestriction.triggered.connect(
            lambda: self.doCreateRestriction(self.actionCreateLineRestriction)
        )
        self.actionCreatePolygonRestriction.triggered.connect(
            lambda: self.doCreateRestriction(self.actionCreatePolygonRestriction)
        )
        self.actionCreateSignRestriction.triggered.connect(
            lambda: self.doCreateRestriction(self.actionCreateSignRestriction)
        )
        self.actionRemoveRestriction.triggered.connect(self.doRemoveRestriction)
        self.actionEditRestriction.toggled.connect(self.doEditRestriction)
        self.actionSplitRestriction.toggled.connect(self.doSplitRestriction)
        self.actionCreateConstructionLine.triggered.connect(
            lambda: self.doCreateRestriction(self.actionCreateConstructionLine)
        )

        # MapTools
        self.geometryInfoMapTool = SelectRestrictionTool()
        self.geometryInfoMapTool.setAction(self.actionSelectRestriction)
        self.actionSelectRestriction.triggered.connect(lambda: iface.mapCanvas().setMapTool(self.geometryInfoMapTool))

        # deal with saving label changes ...
        self.restrictionTransaction = None
        self.mapTool = None
        self.currLayer = None
        self.currProposalID = None
        self._currentlyEdittedLabelLayers = None

        # timer for splitting more than once
        self.splitTimer = QTimer()
        self.splitTimer.setSingleShot(True)
        self.splitTimer.setInterval(1000)
        self.splitTimer.timeout.connect(lambda: self.actionSplitRestriction.setChecked(False))

    def enableTOMsToolbarItems(self, restrictionTransaction):
        TOMsMessageLog.logMessage("In enableTOMsToolbarItems", level=Qgis.Info)

        self.actionSelectRestriction.setEnabled(True)
        self.actionRestrictionDetails.setEnabled(True)
        self.actionCreateBayRestriction.setEnabled(True)
        self.actionCreateLineRestriction.setEnabled(True)
        self.actionCreatePolygonRestriction.setEnabled(True)
        self.actionCreateSignRestriction.setEnabled(True)
        self.actionRemoveRestriction.setEnabled(True)
        self.actionEditRestriction.setEnabled(True)
        self.actionSplitRestriction.setEnabled(True)
        self.actionCreateConstructionLine.setEnabled(True)

        # set up a Transaction object
        self.restrictionTransaction = restrictionTransaction

    def disableTOMsToolbarItems(self):
        TOMsMessageLog.logMessage("In disableTOMsToolbarItems", level=Qgis.Info)

        self.actionSelectRestriction.setEnabled(False)
        self.actionRestrictionDetails.setEnabled(False)
        self.actionCreateBayRestriction.setEnabled(False)
        self.actionCreateLineRestriction.setEnabled(False)
        self.actionCreatePolygonRestriction.setEnabled(False)
        self.actionCreateSignRestriction.setEnabled(False)
        self.actionRemoveRestriction.setEnabled(False)
        self.actionEditRestriction.setEnabled(False)
        self.actionSplitRestriction.setEnabled(False)
        self.actionCreateConstructionLine.setEnabled(False)

    def doRestrictionDetails(self):
        """Select point and then display details"""
        TOMsMessageLog.logMessage("In doRestrictionDetails", level=Qgis.Info)

        # Get the current proposal from the session variables
        currProposalID = self.proposalsManager.currentProposal()

        currRestrictionLayer = iface.activeLayer()

        if currRestrictionLayer and currRestrictionLayer.selectedFeatureCount() > 0:
            TOMsMessageLog.logMessage(
                "In doRestrictionDetails. currLayer: "
                + str(currRestrictionLayer.name() + " Nr feats: " + str(currRestrictionLayer.selectedFeatureCount())),
                level=Qgis.Info,
            )

            if currProposalID == 0:
                # Ensure that no updates can occur for Proposal = 0
                self.restrictionTransaction.rollBackTransactionGroup()  # stop any editing
            else:
                self.restrictionTransaction.startTransactionGroup()  # start editing

            selectedRestrictions = currRestrictionLayer.selectedFeatures()
            for currRestriction in selectedRestrictions:
                TOMsMessageLog.logMessage(
                    "In restrictionFormOpen. currRestrictionLayer: " + str(currRestrictionLayer.name()),
                    level=Qgis.Info,
                )

                dialog = RestrictionDialogWrapper(currRestrictionLayer, currRestriction)
                dialog.show()

        else:
            QMessageBox.information(
                iface.mainWindow(),
                "Information",
                "Select restriction first and then choose information button",
                QMessageBox.Ok,
            )

    def doCreateRestriction(self, createAction):
        TOMsMessageLog.logMessage("In doCreateRestriction", level=Qgis.Info)

        commitStatus = self.restrictionTransaction.rollBackTransactionGroup()
        TOMsMessageLog.logMessage(
            "In doCreateRestriction. Current transaction rolled back ... {}".format(commitStatus),
            level=Qgis.Warning,
        )

        if createAction is self.actionCreateSignRestriction:
            currLayer = self.proposalsManager.tableNames.tomsLayerDict.get("Signs")
        elif createAction is self.actionCreateBayRestriction:
            currLayer = self.proposalsManager.tableNames.tomsLayerDict.get("Bays")
        elif createAction is self.actionCreateLineRestriction:
            currLayer = self.proposalsManager.tableNames.tomsLayerDict.get("Lines")
        elif createAction is self.actionCreatePolygonRestriction:
            currLayer = self.proposalsManager.tableNames.tomsLayerDict.get("RestrictionPolygons")
        elif createAction is self.actionCreateConstructionLine:
            currLayer = QgsProject.instance().mapLayersByName("ConstructionLines")[0]
        else:
            raise ValueError("Action not found")

        if self.proposalsManager.currentProposal() == 0 and createAction is not self.actionCreateConstructionLine:
            QMessageBox.information(
                iface.mainWindow(),
                "Information",
                "Changes to current data is not allowed. Changes are made via Proposals",
                QMessageBox.Ok,
            )
            iface.actionPan().trigger()
            createAction.setChecked(False)
            return

        iface.setActiveLayer(currLayer)
        if createAction is self.actionCreateConstructionLine:
            currLayer.startEditing()
        else:
            self.restrictionTransaction.startTransactionGroup()

        self.mapTool = CreateRestrictionTool()
        iface.mapCanvas().setMapTool(self.mapTool)
        self.mapTool.setAction(createAction)

        TOMsMessageLog.logMessage(
            "In doCreateRestriction - tool activated on " + currLayer.name(),
            level=Qgis.Info,
        )

    def doRemoveRestriction(self):
        # pass control to MapTool and then deal with Proposals issues from there ??
        TOMsMessageLog.logMessage("In doRemoveRestriction", level=Qgis.Info)

        commitStatus = self.restrictionTransaction.rollBackTransactionGroup()
        TOMsMessageLog.logMessage(
            "In doRemoveRestriction. Current transaction rolled back ... {}".format(commitStatus),
            level=Qgis.Warning,
        )

        del self.mapTool
        self.mapTool = None

        # Get the current proposal from the session variables
        self.currProposalID = self.proposalsManager.currentProposal()

        if self.currProposalID > 0:
            currRestrictionLayer = iface.activeLayer()

            if currRestrictionLayer:
                TOMsMessageLog.logMessage(
                    "In doRemoveRestriction. currLayer: " + str(currRestrictionLayer.name()),
                    level=Qgis.Info,
                )

                if currRestrictionLayer.selectedFeatureCount() > 0:
                    selectedRestrictions = currRestrictionLayer.selectedFeatures()

                    self.restrictionTransaction.startTransactionGroup()

                    for currRestriction in selectedRestrictions:
                        if not self.onRemoveRestriction(currRestrictionLayer, currRestriction):
                            QMessageBox.information(None, "ERROR", ("Error deleting restriction ..."))
                            self.restrictionTransaction.rollBackTransactionGroup()
                            break

                    self.restrictionTransaction.commitTransactionGroup()

                else:
                    QMessageBox.information(
                        iface.mainWindow(),
                        "Information",
                        "Select restriction for delete",
                        QMessageBox.Ok,
                    )

        else:
            QMessageBox.information(
                iface.mainWindow(),
                "Information",
                "Changes to current data are not allowed. Changes are made via Proposals",
                QMessageBox.Ok,
            )

    def onRemoveRestriction(self, currRestrictionLayer, currRestriction):
        TOMsMessageLog.logMessage(
            "In onRemoveRestriction. currLayer: "
            + str(currRestrictionLayer.id())
            + " CurrFeature: "
            + str(currRestriction.id()),
            level=Qgis.Info,
        )

        currProposalID = self.proposalsManager.currentProposal()

        currRestrictionLayerID = getRestrictionLayerTableID(currRestrictionLayer)

        idxRestrictionID = currRestriction.fields().indexFromName("RestrictionID")

        if restrictionInProposal(currRestriction[idxRestrictionID], currRestrictionLayerID, currProposalID):
            # check to see whether or not the restriction has an OpenDate. If so, this should not be deleted.
            if currRestriction[currRestriction.fields().indexFromName("OpenDate")]:
                QMessageBox.information(
                    None,
                    "ERROR",
                    ("Something happened that shouldn't ... Error trying to delete restriction"),
                )
                return False
            # remove the restriction from the RestrictionsInProposals table
            # and from the currLayer, i.e., it is totally removed.
            # NB: This is the only case of a restriction being truly deleted

            TOMsMessageLog.logMessage(
                "In onRemoveRestriction. Removing from RestrictionsInProposals and currLayer.",
                level=Qgis.Info,
            )

            # Delete from RestrictionsInProposals
            if not deleteRestrictionInProposal(
                currRestriction[idxRestrictionID],
                currRestrictionLayerID,
                currProposalID,
            ):
                return False

            TOMsMessageLog.logMessage(
                "In onRemoveRestriction. Deleting restriction id: " + str(currRestriction.id()),
                level=Qgis.Info,
            )
            if not currRestrictionLayer.deleteFeature(currRestriction.id()):
                return False

        else:
            # need to:
            #    - enter the restriction into the table RestrictionInProposals as closed, and
            #
            TOMsMessageLog.logMessage("In onRemoveRestriction. Closing existing restriction.", level=Qgis.Info)

            if not addRestrictionToProposal(
                currRestriction[idxRestrictionID],
                currRestrictionLayerID,
                currProposalID,
                RestrictionAction.CLOSE,
            ):
                return False

        return True

    def doEditRestriction(self):
        TOMsMessageLog.logMessage("In doEditRestriction - starting", level=Qgis.Info)

        currRestrictionLayer = iface.activeLayer()
        if self.restrictionTransaction.currTransactionGroup.modified():
            if (
                QMessageBox.question(
                    iface.mainWindow(),
                    "Editing in progress",
                    "Do you want to save the changes?",
                )
                == QMessageBox.No
            ):
                self.restrictionTransaction.rollBackTransactionGroup()

        if self.actionEditRestriction.isChecked():
            TOMsMessageLog.logMessage("In actionEditRestriction - tool being activated", level=Qgis.Info)

            # Get the current proposal from the session variables
            if self.proposalsManager.currentProposal() <= 0:
                QMessageBox.information(
                    iface.mainWindow(),
                    "Information",
                    "Changes to current data are not allowed. Changes are made via Proposals",
                    QMessageBox.Ok,
                )
                self.actionEditRestriction.setChecked(False)
                return

            if currRestrictionLayer and currRestrictionLayer.selectedFeatureCount() > 0:
                TOMsMessageLog.logMessage(
                    "In doEditRestriction. currLayer: " + str(currRestrictionLayer.name()),
                    level=Qgis.Info,
                )
                self.restrictionTransaction.startTransactionGroup()
                iface.actionVertexToolActiveLayer().trigger()
                self.mapTool = iface.mapCanvas().mapTool()
                iface.actionVertexToolActiveLayer().toggled.connect(
                    lambda: self.actionEditRestriction.setChecked(False)
                )
                advancedDigitizingPanel = iface.cadDockWidget()
                advancedDigitizingPanel.setVisible(True)
                advancedDigitizingPanel.enable()
                if not advancedDigitizingPanel.enableAction().isChecked():
                    advancedDigitizingPanel.enableAction().trigger()
                setupPanelTabs(advancedDigitizingPanel)

            else:
                QMessageBox.information(
                    iface.mainWindow(),
                    "Information",
                    "Select restriction for edit",
                    QMessageBox.Ok,
                )
                self.actionEditRestriction.setChecked(False)

        else:
            try:
                iface.actionVertexToolActiveLayer().toggled.disconnect()
            except TypeError:
                pass
            if iface.mapCanvas().mapTool() is self.mapTool:
                iface.actionPan().trigger()

            if self.restrictionTransaction.currTransactionGroup.modified():
                checkEditedGeometries(self.proposalsManager.currentProposal())
            self.restrictionTransaction.commitTransactionGroup()  # to remove edit mode
            setupPanelTabs(iface.mainWindow().findChild(QDockWidget, "ProposalPanelDockWidgetBase"))

            TOMsMessageLog.logMessage("In doEditRestriction - tool deactivated", level=Qgis.Info)

        TOMsMessageLog.logMessage("In doEditRestriction - leaving", level=Qgis.Info)

    def doSplitRestriction(self):
        TOMsMessageLog.logMessage("In doSplitRestriction - starting", level=Qgis.Info)
        currRestrictionLayer = iface.activeLayer()

        if self.actionSplitRestriction.isChecked():
            TOMsMessageLog.logMessage("In actionSplitRestriction - tool being activated", level=Qgis.Info)

            # Get the current proposal from the session variables
            if self.proposalsManager.currentProposal() <= 0:
                QMessageBox.information(
                    iface.mainWindow(),
                    "Information",
                    "Changes to current data are not allowed. Changes are made via Proposals",
                    QMessageBox.Ok,
                )
                self.actionSplitRestriction.setChecked(False)
                return

            if currRestrictionLayer and currRestrictionLayer.selectedFeatureCount() > 0:
                TOMsMessageLog.logMessage(
                    "In doSplitRestriction. currLayer: " + str(currRestrictionLayer.name()),
                    level=Qgis.Info,
                )
                self.restrictionTransaction.startTransactionGroup()
                iface.actionSplitFeatures().trigger()
                self.mapTool = iface.mapCanvas().mapTool()
                currRestrictionLayer.editBuffer().featureAdded.connect(self.stopSplitting)
                advancedDigitizingPanel = iface.cadDockWidget()
                advancedDigitizingPanel.setVisible(True)
                advancedDigitizingPanel.enable()
                if not advancedDigitizingPanel.enableAction().isChecked():
                    advancedDigitizingPanel.enableAction().trigger()
                setupPanelTabs(advancedDigitizingPanel)

            else:
                QMessageBox.information(
                    iface.mainWindow(),
                    "Information",
                    "Select restriction for edit",
                    QMessageBox.Ok,
                )
                self.actionSplitRestriction.setChecked(False)

        else:
            if iface.mapCanvas().mapTool() is self.mapTool:
                iface.actionPan().trigger()

            if self.restrictionTransaction.currTransactionGroup.modified():
                checkSplitGeometries(self.proposalsManager.currentProposal())
            self.restrictionTransaction.commitTransactionGroup()  # to remove edit mode
            setupPanelTabs(iface.mainWindow().findChild(QDockWidget, "ProposalPanelDockWidgetBase"))

            TOMsMessageLog.logMessage("In doSplitRestriction - tool deactivated", level=Qgis.Info)

        TOMsMessageLog.logMessage("In doSplitRestriction - leaving", level=Qgis.Info)

    def stopSplitting(self):
        # We can receive many time the featureAdded from the layer buffer
        # if there is a multi-split, we want to commit the split only after
        # the last featureAdded signal has been emitted.
        # There is no signal for that situation, hence the timer.
        self.splitTimer.start()
