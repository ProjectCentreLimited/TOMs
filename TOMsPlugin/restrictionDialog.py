# -----------------------------------------------------------
# Licensed under the terms of GNU GPL 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# -----------------------------------------------------------
# Oslandia 2023

import functools
import uuid

from qgis.core import (
    Qgis,
    QgsExpressionContextUtils,
    QgsFeature,
    QgsGeometry,
    QgsProject,
)
from qgis.PyQt.QtWidgets import (
    QComboBox,
    QDialogButtonBox,
    QDockWidget,
    QMessageBox,
)
from qgis.utils import iface

from .constants import RestrictionAction, UserPermission
from .core.tomsMessageLog import TOMsMessageLog
from .core.tomsTransaction import TOMsTransaction
from .generateGeometryUtils import GenerateGeometryUtils
from .restrictionTypeUtilsClass import TOMsLabelLayerNames
from .utils import (
    addRestrictionToProposal,
    getRestrictionLayerTableID,
    restrictionInProposal,
    saveLastSelectedValue,
    setupPanelTabs,
)


class RestrictionDialogWrapper:
    """
    This class creates the restriction dialog form
    and customizes the form with different behaviors of buttons and signals
    """

    def __init__(self, layer, feature):
        self.dialog = iface.getFeatureForm(layer, feature)
        if self.dialog is None:
            raise ValueError("Form dialog for this layer and this feature not found")

        self.layer = layer
        self.feature = feature
        self.proposalPanelDock = iface.mainWindow().findChild(QDockWidget, "ProposalPanelDockWidgetBase")

        # If we are here a TOMsTransaction has already been instanciated
        # and it's a singleton. Therefore we don't need to give any
        # parameter to the constructor.
        # FIXME: in future refactoring of TOMsTransaction it will be better
        self.transaction = TOMsTransaction()

        self.origFeature = QgsFeature(self.feature)

        buttonBox = self.dialog.findChild(QDialogButtonBox, "button_box")
        if buttonBox is None:
            raise ValueError("In setupRestrictionDialog. button box not found")
        self.dialog.attributeForm().attributeChanged.connect(
            functools.partial(saveLastSelectedValue, self.feature, self.layer)
        )

        buttonBox.accepted.connect(lambda: self.accept())
        buttonBox.rejected.connect(lambda: self.reject())

        # For the specific case of Electric Vehicle Charging Place
        # the PTA must be editable
        if self.layer.name() == "Bays":
            defaultPta, _, _ = GenerateGeometryUtils.getCurrentPTADetails(self.feature)
            self.checkElectricVehicleChargingPlace(defaultPta)
            self.dialog.findChild(QComboBox, "RestrictionTypeID").currentTextChanged.connect(
                functools.partial(
                    self.checkElectricVehicleChargingPlace,
                    defaultPta,
                )
            )

    def checkElectricVehicleChargingPlace(self, defaultPta):
        """
        If the restriction is an electric vehicle charging place
        the ParkingTariffArea must be editable
        """

        restrictionTypeIdCbx = self.dialog.findChild(QComboBox, "RestrictionTypeID")
        ptaCbx = self.dialog.findChild(QComboBox, "ParkingTariffArea")
        ptaCbx.setEnabled(restrictionTypeIdCbx.currentData() == 124)
        if restrictionTypeIdCbx.currentData() != 124:
            ptaCbx.setCurrentText(defaultPta)

    def accept(self):
        if not UserPermission.WRITE:
            QMessageBox.warning(
                None,
                "Read Only",
                "Nothing will be saved because you only have read access",
            )
            return

        currProposalID = QgsProject.instance().customVariables()["CurrentProposal"]
        if currProposalID <= 0:
            # Impossible because if no proposal selected the OK button is disabled
            raise RuntimeError("Can't accept a restriction form if no proposal selected")

        restrictionId = self.feature["RestrictionID"]
        currRestrictionLayerTableID = getRestrictionLayerTableID(self.layer)

        # If restriction is already part of the current proposal
        # simply make changes to the current restriction in the current layer
        if restrictionInProposal(
            restrictionId,
            currRestrictionLayerTableID,
            currProposalID,
        ):
            if not self.layer.updateFeature(self.feature):
                raise RuntimeError(f"Unable to update the feature {restrictionId}")
            self.saveAndClose()
            return

        # If it is a completely new feature that has been draw, need to:
        #    - enter the restriction into the table RestrictionInProposals, and
        #    - make a copy of the restriction in the current layer (with the new details)
        if self.feature["OpenDate"] is None:
            addRestrictionToProposal(
                restrictionId,
                currRestrictionLayerTableID,
                currProposalID,
                RestrictionAction.OPEN,
            )
            self.layer.addFeature(self.feature)  # TH (added for v3)
            self.saveAndClose()
            return

        # Arriving here, this feature was created before this proposal, in a previous proposal
        # that has been accepted. We need to:
        #  - close it in the RestrictionsInProposals table
        #  - clone it in the current Restrictions layer (with a new RestrictionID and no OpenDate)
        #  - reset the original feature
        addRestrictionToProposal(
            restrictionId,
            currRestrictionLayerTableID,
            currProposalID,
            RestrictionAction.CLOSE,
        )

        newFeature = QgsFeature(self.feature)
        newFeature["RestrictionID"] = str(uuid.uuid4())
        newFeature["OpenDate"] = None
        newFeature["GeometryID"] = None
        self.layer.addFeature(newFeature)
        self.layer.updateFeature(self.origFeature)

        addRestrictionToProposal(
            newFeature["RestrictionID"],
            currRestrictionLayerTableID,
            currProposalID,
            RestrictionAction.OPEN,
        )

        self.saveAndClose()

    def saveAndClose(self):
        self.transaction.commitTransactionGroup()
        for labelLayerName in TOMsLabelLayerNames(self.layer).getCurrLabelLayerNames():
            try:
                QgsProject.instance().mapLayersByName(labelLayerName)[0].reload()
            except IndexError:
                pass  # No label for Signs
        self.close()

    def close(self):
        self.dialog.reject()
        self.layer.removeSelection()
        setupPanelTabs(self.proposalPanelDock)

    def reject(self):
        self.dialog.reject()
        self.layer.removeSelection()
        self.transaction.rollBackTransactionGroup()
        setupPanelTabs(self.proposalPanelDock)

    def show(self):
        self.dialog.show()
