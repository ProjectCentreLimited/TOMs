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

import functools
import os
import re

from qgis.core import (
    Qgis,
    QgsFeature,
    QgsProject,
    QgsVectorLayer,
)
from qgis.PyQt.QtCore import QCoreApplication, QDate, Qt
from qgis.PyQt.QtGui import QIcon

# Import the PyQt and QGIS libraries
from qgis.PyQt.QtWidgets import (
    QAction,
    QComboBox,
    QDialogButtonBox,
    QLabel,
    QMessageBox,
    QToolButton,
)
from qgis.utils import OverrideCursor, iface

from .constants import ProposalStatus, RestrictionAction, UserPermission
from .core.proposalsManager import TOMsProposalsManager
from .core.tomsMessageLog import TOMsMessageLog
from .core.tomsTransaction import TOMsTransaction
from .instantPrint.tomsInstantPrintTool import TOMsInstantPrintTool
from .manageRestrictionDetails import ManageRestrictionDetails
from .restrictionTypeUtilsClass import TOMsConfigFile
from .searchBar import SearchBar
from .ui.proposalPanelDockwidget import ProposalPanelDockWidget
from .utils import saveLastSelectedValue, setupPanelTabs


class ProposalsPanel:
    def __init__(self, tomsToolbar):
        # Save reference to the QGIS interface
        self.canvas = iface.mapCanvas()
        self.tomsToolbar = tomsToolbar

        self.actionProposalsPanel = QAction(
            QIcon(":/plugins/TOMs/resources/TOMsStart.png"),
            QCoreApplication.translate("MyPlugin", "Start TOMs"),
            iface.mainWindow(),
        )
        self.actionProposalsPanel.setCheckable(True)

        self.tomsToolbar.addAction(self.actionProposalsPanel)

        self.actionProposalsPanel.triggered.connect(self.onInitProposalsPanel)

        self.newProposalRequired = False

        self.proposalsManager = TOMsProposalsManager()
        self.tableNames = self.proposalsManager.tableNames

        # Now set up the toolbar

        self.restrictionTools = ManageRestrictionDetails(self.tomsToolbar, self.proposalsManager)

        self.searchBar = SearchBar(self.tomsToolbar)

        # Add print to the search toolbar

        self.tool = TOMsInstantPrintTool(self.proposalsManager)

        # Add in details of the Instant Print plugin
        self.toolButton = QToolButton()
        self.toolButton.setIcon(QIcon(":/plugins/TOMs/InstantPrint/icons/icon.png"))
        self.toolButton.setCheckable(True)
        self.toolButton.setToolTip("Print")

        if UserPermission.PRINT:
            self.tomsToolbar.addWidget(self.toolButton)

        if UserPermission.FULL_CONTROL:
            self.mappingUpdatesAction = QAction("MU")
            self.mappingUpdatesAction.triggered.connect(self.makeMappingUpdatesInProposal)
            self.tomsToolbar.addAction(self.mappingUpdatesAction)
            self.mappingUpdatesAction.setToolTip("Make mapping updates and masks live")
        else:
            self.mappingUpdatesAction = None

        self.toolButton.toggled.connect(self.__enablePrintTool)
        iface.mapCanvas().mapToolSet.connect(self.__onPrintToolSet)

        statusLabel = QLabel(
            "&nbsp;&nbsp;<b>"
            + UserPermission.prettyPrint()
            + " - "
            + os.environ.get("DEPLOY_STAGE", "UNKNOWN DEPLOY STAGE").upper()
            + "&nbsp;&nbsp;</b>"
        )
        statusLabel.setStyleSheet("background-color: lightblue; color: black")
        self.tomsToolbar.addWidget(statusLabel)

        self.searchBar.disableSearchBar()
        # print tool
        self.toolButton.setEnabled(False)
        if self.mappingUpdatesAction:
            self.mappingUpdatesAction.setEnabled(False)
        self.restrictionTools.disableTOMsToolbarItems()

        self.closeTOMs = False
        self.tomsConfigFileObject = None
        self.dock = None
        self.proposals = None
        self.idxProposalTitle = None
        self.idxCreateDate = None
        self.idxOpenDate = None
        self.idxProposalStatusID = None
        self.proposalTransaction = None
        self.newProposalObject = None
        self.newProposal = None
        self.proposalDialog = None
        self.buttonBox = None
        self.currProposalObject = None
        self.currProposal = None

        TOMsMessageLog.logMessage("Finished proposalsPanel init ...", level=TOMsMessageLog.DEBUG)

    def __enablePrintTool(self, active):  # pylint: disable=invalid-name
        self.tool.setEnabled(active)

    def __onPrintToolSet(self, tool):  # pylint: disable=invalid-name
        if tool != self.tool:
            self.toolButton.setChecked(False)

    def onInitProposalsPanel(self):
        """Filter main layer based on date and state options"""

        TOMsMessageLog.logMessage("In onInitProposalsPanel", level=Qgis.Info)

        if self.actionProposalsPanel.isChecked():
            TOMsMessageLog.logMessage("In onInitProposalsPanel. Activating ...", level=Qgis.Info)

            self.openTOMsTools()

        else:
            TOMsMessageLog.logMessage("In onInitProposalsPanel. Deactivating ...", level=Qgis.Info)

            self.closeTOMsTools()

    def openTOMsTools(self):
        # actions when the Proposals Panel is closed or the toolbar "start" is toggled

        TOMsMessageLog.logMessage("In openTOMsTools. Activating ...", level=Qgis.Info)
        self.closeTOMs = False

        # Check that tables are present
        TOMsMessageLog.logMessage("In onInitProposalsPanel. Checking tables", level=Qgis.Info)
        self.tableNames.tomsLayersNotFound.connect(self.setCloseTOMsFlag)

        self.tomsConfigFileObject = TOMsConfigFile()
        self.tomsConfigFileObject.tomsConfigFileNotFound.connect(self.setCloseTOMsFlag)
        self.tomsConfigFileObject.initialiseTOMsConfigFile()

        self.tableNames.setLayers(self.tomsConfigFileObject)

        if self.closeTOMs:
            QMessageBox.information(iface.mainWindow(), "ERROR", ("Unable to start TOMs ..."))
            self.actionProposalsPanel.setChecked(False)
            return

        self.proposalsManager.tomsActivated.emit()

        self.dock = ProposalPanelDockWidget()
        iface.addDockWidget(Qt.LeftDockWidgetArea, self.dock)

        # set up tabbing for Panels
        setupPanelTabs(self.dock)

        self.proposalsManager.dateChanged.connect(self.onDateChanged)
        self.dock.filterDate.setDisplayFormat("dd-MM-yyyy")
        self.dock.filterDate.setDate(QDate.currentDate())

        self.proposals = self.tableNames.getLayer("Proposals")

        # Set up field details for table  ** what about errors here **
        self.idxProposalTitle = self.proposals.fields().indexFromName("ProposalTitle")
        self.idxCreateDate = self.proposals.fields().indexFromName("ProposalCreateDate")
        self.idxOpenDate = self.proposals.fields().indexFromName("ProposalOpenDate")
        self.idxProposalStatusID = self.proposals.fields().indexFromName("ProposalStatusID")

        self.createProposalcb()

        # set CurrentProposal to be 0

        # self.proposalsManager.setCurrentProposal(0)

        # set up action for when the date is changed from the user interface
        self.dock.filterDate.dateChanged.connect(lambda: self.proposalsManager.setDate(self.dock.filterDate.date()))

        # set up action for "New Proposal"
        self.dock.btn_NewProposal.clicked.connect(self.onNewProposal)
        self.dock.btn_NewProposal.setEnabled(UserPermission.WRITE)

        # set up action for "View Proposal"
        self.dock.btn_ViewProposal.clicked.connect(self.onProposalDetails)

        self.proposalsManager.newProposalCreated.connect(self.onNewProposalCreated)

        # Create a transaction object for the Proposals

        self.proposalTransaction = TOMsTransaction(self.proposalsManager)

        self.restrictionTools.enableTOMsToolbarItems(self.proposalTransaction)
        self.searchBar.enableSearchBar()
        # print tool
        self.toolButton.setEnabled(True)
        self.setLabelUpdateTriggers()

        # setup use of "Escape" key to deactive map tools
        # https://gis.stackexchange.com/questions/133228/how-to-deactivate-my-custom-tool-by-pressing-the-escape-key-using-pyqgis

        self.proposalsManager.setCurrentProposal(0)
        if self.mappingUpdatesAction:
            self.mappingUpdatesAction.setEnabled(True)

        # TODO: Deal with the change of project ... More work required on this
        # self.TOMsProject = QgsProject.instance()
        # self.TOMsProject.cleared.connect(self.closeTOMsTools)

    def setCloseTOMsFlag(self):
        self.closeTOMs = True

    def closeTOMsTools(self):
        # actions when the Proposals Panel is closed or the toolbar "start" is toggled

        TOMsMessageLog.logMessage("In closeTOMsTools. Deactivating ...", level=Qgis.Info)

        # TODO: Delete any objects that are no longer needed

        try:
            self.proposalTransaction.rollBackTransactionGroup()
            del self.proposalTransaction  # There is another call to this function from the dock.close()
        except Exception as e:
            TOMsMessageLog.logMessage("closeTOMsTools: issue with transactions {}".format(e), level=Qgis.Info)

        # Now disable the items from the Toolbar

        self.restrictionTools.disableTOMsToolbarItems()
        self.searchBar.disableSearchBar()
        # print tool
        self.toolButton.setEnabled(False)
        if self.mappingUpdatesAction:
            self.mappingUpdatesAction.setEnabled(False)

        self.actionProposalsPanel.setChecked(False)

        self.unsetLabelUpdateTriggers()

        # Now close the proposals panel

        self.dock.close()

        # Now clear the filters

        self.proposalsManager.clearRestrictionFilters()

        # reset path names
        self.tableNames.removePathFromLayerForms()

    def createProposalcb(self):
        TOMsMessageLog.logMessage("In createProposalcb", level=Qgis.Info)
        # set up a "NULL" field for "No proposals to be shown"

        self.dock.cb_ProposalsList.clear()

        currProposalID = 0
        currProposalTitle = "0 - No proposal shown"

        TOMsMessageLog.logMessage("In createProposalcb: Adding 0", level=Qgis.Info)

        self.dock.cb_ProposalsList.addItem(currProposalTitle, currProposalID)

        for (currProposalID, currProposalTitle, _, _, _,) in sorted(
            self.proposalsManager.getProposalsListWithStatus(ProposalStatus.IN_PREPARATION),
            key=lambda f: f[1],
        ):
            TOMsMessageLog.logMessage(
                "In createProposalcb: proposalID: " + str(currProposalID) + ":" + currProposalTitle,
                level=Qgis.Info,
            )
            self.dock.cb_ProposalsList.addItem(currProposalTitle, currProposalID)

        # set up action for when the proposal is changed
        self.dock.cb_ProposalsList.currentIndexChanged.connect(self.onProposalListIndexChanged)

    def makeMappingUpdatesInProposal(self):
        """makeMappingUpdatesInProposal.

        Add MappingUpdates and MappingUpdateMasks restrictions in current proposal
        """

        currProposalId = self.proposalsManager.currentProposal()
        if currProposalId == 0:
            QMessageBox.warning(None, "ERROR", "Trying to push mapping updates into 'No Proposals'")
            return

        # Get layers without filters to have all features
        try:
            mappingUpdatesLayer = QgsVectorLayer(
                self.tableNames.getLayer("MappingUpdates").source(), providerLib="postgres"
            )
            mappingUpdateMasksLayer = QgsVectorLayer(
                self.tableNames.getLayer("MappingUpdateMasks").source(), providerLib="postgres"
            )
            ripLayer = self.tableNames.getLayer("RestrictionsInProposals")
        except Exception:
            raise RuntimeError("A layer is missing!")

        i = 0
        counts = [0, 0]
        self.proposalTransaction.startTransactionGroup()
        for layer, layerId in [(mappingUpdatesLayer, 101), (mappingUpdateMasksLayer, 102)]:
            layer.startEditing()
            # For each mapping update that does not have a RestrictionID in this proposal
            for restriction in layer.getFeatures(f""""ProposalID" = {currProposalId} and "RestrictionID" is NULL"""):
                restriction["RestrictionID"] = restriction["GeometryID"]  # Copy the GeometryID
                if not layer.updateFeature(restriction):
                    QMessageBox.warning(None, "ERROR", "Unable to copy GeometryID into RestrictionID")
                    self.proposalTransaction.rollBackTransactionGroup()
                    return

                # Add the restriction in RestrictionsInProposals table
                newRip = QgsFeature(ripLayer.fields())
                newRip["ProposalID"] = currProposalId
                newRip["RestrictionTableID"] = layerId
                newRip["RestrictionID"] = restriction["RestrictionID"]
                newRip["ActionOnProposalAcceptance"] = RestrictionAction.OPEN.value
                if not ripLayer.addFeature(newRip):
                    QMessageBox.warning(None, "ERROR", "Unable to add feature in RestrictionsInProposals table")
                    self.proposalTransaction.rollBackTransactionGroup()
                    return

                counts[i] += 1
            layer.commitChanges()
            i += 1

        self.proposalTransaction.commitTransactionGroup()
        QMessageBox.information(
            None, "Features added", f"Added {counts[0]} mapping updates, and {counts[1]} mapping update masks"
        )

    def onNewProposal(self):
        TOMsMessageLog.logMessage("In onNewProposal", level=Qgis.Info)

        # set up a transaction
        self.proposalTransaction.startTransactionGroup()

        # create a new Proposal

        self.newProposalObject = self.proposalsManager.currentProposalObject().initialiseProposal()
        self.newProposal = self.proposalsManager.currentProposalObject().getProposalRecord()

        self.proposalDialog = iface.getFeatureForm(self.proposals, self.newProposal)

        # self.proposalDialog.attributeForm().disconnectButtonBox()
        self.buttonBox = self.proposalDialog.findChild(QDialogButtonBox, "button_box")

        if self.buttonBox is None:
            TOMsMessageLog.logMessage("In onNewProposal. button box not found", level=Qgis.Info)

            # self.button_box.accepted.disconnect()
        self.buttonBox.accepted.connect(
            functools.partial(
                self.onSaveProposalFormDetails,
                self.newProposal,
                self.newProposalObject,
                self.proposals,
                self.proposalDialog,
                self.proposalTransaction,
            )
        )

        self.buttonBox.rejected.connect(self.onRejectProposalDetailsFromForm)

        self.proposalDialog.attributeForm().attributeChanged.connect(
            functools.partial(saveLastSelectedValue, self.newProposal, self.proposals)
        )

        self.proposalDialog.show()

    def onNewProposalCreated(self, proposal):
        TOMsMessageLog.logMessage("In onNewProposalCreated. New proposal = " + str(proposal), level=Qgis.Info)

        self.createProposalcb()

        # change the list to show the new proposal

        for currIndex in range(self.dock.cb_ProposalsList.count()):
            currProposalID = self.dock.cb_ProposalsList.itemData(currIndex)
            if currProposalID == proposal:
                TOMsMessageLog.logMessage(
                    "In onNewProposalCreated. index found as " + str(currIndex),
                    level=Qgis.Info,
                )
                self.dock.cb_ProposalsList.setCurrentIndex(currIndex)
                return

        return

    def onRejectProposalDetailsFromForm(self):
        self.proposals.destroyEditCommand()
        self.proposalDialog.reject()

        # self.rollbackCurrentEdits()

        self.proposalTransaction.rollBackTransactionGroup()

    def onProposalDetails(self):
        TOMsMessageLog.logMessage("In onProposalDetails", level=Qgis.Info)

        # set up transaction
        self.proposalTransaction.startTransactionGroup()

        # https://gis.stackexchange.com/questions/94135/how-to-populate-a-combobox-with-layers-in-toc
        currProposalCbIndex = self.dock.cb_ProposalsList.currentIndex()

        if currProposalCbIndex == 0:
            return  # there is nothing to see

        # self.currProposal = self.getProposal(currProposalID)
        self.currProposalObject = self.proposalsManager.currentProposalObject()
        self.currProposal = self.proposalsManager.currentProposalObject().getProposalRecord()
        self.proposalDialog = iface.getFeatureForm(self.proposals, self.currProposal)

        self.buttonBox = self.proposalDialog.findChild(QDialogButtonBox, "button_box")

        if self.buttonBox is None:
            TOMsMessageLog.logMessage("In onNewProposal. button box not found", level=Qgis.Info)

        self.buttonBox.accepted.disconnect()
        self.buttonBox.accepted.connect(
            functools.partial(
                self.onSaveProposalFormDetails,
                self.currProposal,
                self.currProposalObject,
                self.proposals,
                self.proposalDialog,
                self.proposalTransaction,
            )
        )

        self.buttonBox.rejected.disconnect()
        self.buttonBox.rejected.connect(self.onRejectProposalDetailsFromForm)

        self.proposalDialog.attributeForm().attributeChanged.connect(
            functools.partial(saveLastSelectedValue, self.currProposal, self.proposals)
        )

        def proposalStatusCallback():
            # Only users with the right privilege can reject or accept a proposal
            currentStatusId = self.proposalDialog.findChild(QComboBox, "ProposalStatusID").currentData()
            self.proposalDialog.findChild(QDialogButtonBox, "button_box").button(QDialogButtonBox.Ok).setEnabled(
                UserPermission.CONFIRM_ORDERS
                or (
                    currentStatusId
                    not in [
                        ProposalStatus.ACCEPTED.value,
                        ProposalStatus.REJECTED.value,
                    ]
                )
            )

        self.proposalDialog.findChild(QComboBox, "ProposalStatusID").currentIndexChanged.connect(proposalStatusCallback)

        self.proposalDialog.setEnabled(UserPermission.WRITE)
        self.proposalDialog.show()

    def onSaveProposalFormDetails(
        self,
        currProposalRecord,
        currProposalObject,
        proposalsLayer,
        proposalsDialog,
        proposalTransaction,
    ):
        TOMsMessageLog.logMessage("In onSaveProposalFormDetails.", level=Qgis.Info)

        self.proposals = proposalsLayer

        # set up field indexes
        idxProposalID = self.proposals.fields().indexFromName("ProposalID")
        idxProposalTitle = self.proposals.fields().indexFromName("ProposalTitle")
        idxProposalStatusID = self.proposals.fields().indexFromName("ProposalStatusID")
        idxProposalOpenDate = self.proposals.fields().indexFromName("ProposalOpenDate")

        currProposalID = currProposalObject.getProposalNr()
        currProposalStatusID = currProposalObject.getProposalStatusID()
        currProposalTitle = currProposalObject.getProposalTitle()

        newProposalStatusID = currProposalRecord[idxProposalStatusID]
        newProposalOpenDate = currProposalRecord[idxProposalOpenDate]
        TOMsMessageLog.logMessage(
            "In onSaveProposalFormDetails. currProposalStatus = " + str(currProposalStatusID),
            level=Qgis.Info,
        )

        newProposal = False
        proposalAcceptedRejected = False

        if newProposalStatusID == ProposalStatus.ACCEPTED.value:  # 2 = accepted
            reply = QMessageBox.question(
                None,
                "Confirm changes to Proposal",
                # How do you access the main window to make the popup ???
                "Do you want to ACCEPT this proposal? Accepting will make all the proposed changes permanent.",
                QMessageBox.Yes,
                QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                currProposalObject.setProposalOpenDate(newProposalOpenDate)

                if not currProposalObject.acceptProposal():
                    proposalTransaction.rollBackTransactionGroup()
                    proposalsDialog.reject()
                    reply = QMessageBox.information(None, "Error", "Error in accepting proposal ...", QMessageBox.Ok)
                    TOMsMessageLog.logMessage(
                        "In onSaveProposalFormDetails. Error in transaction",
                        level=Qgis.Info,
                    )
                    return

                proposalsDialog.attributeForm().save()
                proposalsDialog.close()
                proposalAcceptedRejected = True

            else:
                proposalsDialog.reject()

        elif currProposalStatusID == ProposalStatus.REJECTED.value:  # 3 = rejected
            reply = QMessageBox.question(
                None,
                "Confirm changes to Proposal",
                # How do you access the main window to make the popup ???
                "Do you want to REJECT this proposal? This will remove it from the "
                "Proposal list (although it will remain in the system).",
                QMessageBox.Yes,
                QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                if not currProposalObject.rejectProposal():
                    proposalTransaction.rollBackTransactionGroup()
                    proposalsDialog.reject()
                    TOMsMessageLog.logMessage(
                        "In onSaveProposalFormDetails. Error in transaction",
                        level=Qgis.Info,
                    )
                    return

                proposalsDialog.attributeForm().save()
                proposalsDialog.close()
                proposalAcceptedRejected = True

            else:
                proposalsDialog.reject()

        else:
            TOMsMessageLog.logMessage(
                "In onSaveProposalFormDetails. currProposalID = " + str(currProposalID),
                level=Qgis.Info,
            )
            proposalsDialog.attributeForm().save()

            # anything else can be saved.
            if currProposalID == 0:  # We should not be here if this is the current proposal ... 0 is place holder ...
                # This is a new proposal ...

                newProposal = True
                TOMsMessageLog.logMessage("In onSaveProposalFormDetails. New Proposal ... ", level=Qgis.Info)

            else:
                pass
                # self.Proposals.updateFeature(currProposalObject.getProposalRecord())  # TH (added for v3)

            proposalsDialog.reject()

            TOMsMessageLog.logMessage(
                "In onSaveProposalFormDetails. ProposalTransaction modified Status: "
                + str(proposalTransaction.currTransactionGroup.modified()),
                level=Qgis.Info,
            )

        TOMsMessageLog.logMessage(
            "In onSaveProposalFormDetails. Before save. "
            + str(currProposalTitle)
            + " Status: "
            + str(currProposalStatusID),
            level=Qgis.Info,
        )

        proposalTransaction.commitTransactionGroup()

        proposalsDialog.close()

        # For some reason the committedFeaturesAdded signal for layer "Proposals" is not
        # firing at this point and so the cbProposals is not refreshing ...

        if newProposal:
            TOMsMessageLog.logMessage(
                "In onSaveProposalFormDetails. newProposalID = " + str(currProposalID),
                level=Qgis.Info,
            )

            for proposal in self.proposals.getFeatures():
                if proposal[idxProposalTitle] == currProposalTitle:
                    TOMsMessageLog.logMessage(
                        "In onSaveProposalFormDetails. newProposalID = " + str(proposal.id()),
                        level=Qgis.Info,
                    )
                    newProposalID = proposal[idxProposalID]

            self.proposalsManager.newProposalCreated.emit(newProposalID)

        elif proposalAcceptedRejected:
            # refresh the cbProposals and set current Proposal to 0
            self.createProposalcb()
            self.proposalsManager.setCurrentProposal(0)

        else:
            self.proposalsManager.newProposalCreated.emit(currProposalID)

    def onProposalListIndexChanged(self):
        TOMsMessageLog.logMessage("In onProposalListIndexChanged.", level=Qgis.Info)

        currProposalCbIndex = self.dock.cb_ProposalsList.currentIndex()
        TOMsMessageLog.logMessage(
            "In onProposalListIndexChanged. Current Index = " + str(currProposalCbIndex),
            level=Qgis.Info,
        )
        currProposalID = self.dock.cb_ProposalsList.currentData()

        with OverrideCursor(Qt.WaitCursor):
            self.proposalsManager.setCurrentProposal(currProposalID)

        TOMsMessageLog.logMessage("In onProposalChanged. Zoom to extents", level=Qgis.Info)

    def onDateChanged(self):
        TOMsMessageLog.logMessage("In onDateChanged.", level=Qgis.Info)
        date = self.proposalsManager.date()
        self.dock.filterDate.setDate(date)

    def getProposal(self, proposalID):
        TOMsMessageLog.logMessage("In getProposal.", level=Qgis.Info)

        # proposalsLayer = QgsMapLayerRegistry.instance().mapLayersByName("Proposals")[0]  -- v2
        proposalsLayer = QgsProject.instance().mapLayersByName("Proposals")[0]

        # not sure if there is better way to search for something, .e.g., using SQL ??

        for currProposal in proposalsLayer.getFeatures():
            if currProposal.attribute("ProposalID") == proposalID:
                return currProposal

        return None

    def setLabelUpdateTriggers(self):
        TOMsMessageLog.logMessage("In setLabelUpdateTriggers ...", level=Qgis.Info)

        # find any layers with the name "%.label%"
        # https://gis.stackexchange.com/questions/312040/stuck-on-how-to-list-loaded-layers-in-qgis-3-via-python

        layerList = QgsProject.instance().layerTreeRoot().findLayers()

        for layer in layerList:
            if re.findall(".label", layer.name()):
                try:
                    layer.layer().setRefreshOnNotifyEnabled(True)
                except Exception as e:
                    TOMsMessageLog.logMessage(
                        "Error in setLabelUpdateTriggers ...{}".format(e),
                        level=Qgis.Warning,
                    )

    def unsetLabelUpdateTriggers(self):
        TOMsMessageLog.logMessage("In setLabelUpdateTriggers ...", level=Qgis.Info)

        # find any layers with the name "%.label%"
        # https://gis.stackexchange.com/questions/312040/stuck-on-how-to-list-loaded-layers-in-qgis-3-via-python

        layerList = QgsProject.instance().layerTreeRoot().findLayers()

        for layer in layerList:
            if re.findall(".label", layer.name()):
                try:
                    layer.layer().setRefreshOnNotifyEnabled(False)
                except Exception as e:
                    TOMsMessageLog.logMessage(
                        "Error in setLabelUpdateTriggers ...{}".format(e),
                        level=Qgis.Warning,
                    )
