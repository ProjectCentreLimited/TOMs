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
    onAttributeChangedClass2,
    restrictionInProposal,
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
        self.proposalPanelDock = iface.mainWindow().findChild(
            QDockWidget, "ProposalPanelDockWidgetBase"
        )

        # If we are here a TOMsTransaction has already been instanciated
        # and it's a singleton. Therefore we don't need to give any
        # parameter to the constructor.
        # FIXME: in future refactoring of TOMsTransaction it will be better
        self.transaction = TOMsTransaction()

        self.origFeature = QgsFeature(self.feature)

        buttonBox = self.dialog.findChild(QDialogButtonBox, "button_box")
        if buttonBox is None:
            raise ValueError("In setupRestrictionDialog. button box not found")
        buttonBox.accepted.connect(
            self.accept,
        )
        self.dialog.attributeForm().attributeChanged.connect(
            functools.partial(onAttributeChangedClass2, self.feature, self.layer)
        )
        buttonBox.rejected.connect(self.reject)

        # For the specific case of Electric Vehicle Charging Place
        # the PTA must be editable
        if self.layer.name() == "Bays":
            defaultPta, _, _ = GenerateGeometryUtils.getCurrentPTADetails(self.feature)
            self.checkElectricVehicleChargingPlace(defaultPta)
            self.dialog.findChild(
                QComboBox, "RestrictionTypeID"
            ).currentTextChanged.connect(
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
        TOMsMessageLog.logMessage(
            "In RestrictionDialogWrapper.accept: "
            + str(self.feature.attribute("GeometryID")),
            level=Qgis.Info,
        )

        currProposalID = int(
            QgsExpressionContextUtils.projectScope(QgsProject.instance()).variable(
                "CurrentProposal"
            )
        )

        if currProposalID > 0:

            currRestrictionLayerTableID = getRestrictionLayerTableID(self.layer)
            idxRestrictionID = self.feature.fields().indexFromName("RestrictionID")
            idxGeometryID = self.feature.fields().indexFromName("GeometryID")

            if restrictionInProposal(
                self.feature[idxRestrictionID],
                currRestrictionLayerTableID,
                currProposalID,
            ):

                # restriction already is part of the current proposal
                # simply make changes to the current restriction in the current layer
                TOMsMessageLog.logMessage(
                    "In RestrictionDialogWrapper.accept. Saving details straight from form."
                    + str(self.feature.attribute("GeometryID")),
                    level=Qgis.Info,
                )
                self.layer.updateFeature(self.feature)
                self.dialog.attributeForm().save()

            else:

                # restriction is NOT part of the current proposal

                # need to:
                #    - enter the restriction into the table RestrictionInProposals, and
                #    - make a copy of the restriction in the current layer (with the new details)

                # Create a new feature using the current details

                idxOpenDate = self.feature.fields().indexFromName("OpenDate")
                newRestrictionID = str(uuid.uuid4())

                TOMsMessageLog.logMessage(
                    "In RestrictionDialogWrapper.accept. Adding new restriction (1). ID: "
                    + str(newRestrictionID),
                    level=Qgis.Info,
                )

                if self.feature[idxOpenDate] is None:
                    # This is a feature that has just been created, i.e., it is not currently part
                    # of the proposal and did not previously exist

                    # Not quite sure what is happening here but think the following:
                    #  Feature does not yet exist, i.e., not saved to layer yet, so there is no id for it
                    # and can't use either feature or layer to save
                    #  So, need to continue to modify dialog value which will be eventually saved

                    self.dialog.attributeForm().changeAttribute(
                        "RestrictionID", newRestrictionID
                    )

                    TOMsMessageLog.logMessage(
                        "In RestrictionDialogWrapper.accept. Adding new restriction. ID: "
                        + str(self.feature[idxRestrictionID]),
                        level=Qgis.Info,
                    )

                    addRestrictionToProposal(
                        str(self.feature[idxRestrictionID]),
                        currRestrictionLayerTableID,
                        currProposalID,
                        RestrictionAction.OPEN,
                    )  # Open = 1

                    TOMsMessageLog.logMessage(
                        "In RestrictionDialogWrapper.accept. Transaction Status 1: "
                        + str(self.transaction.currTransactionGroup.modified()),
                        level=Qgis.Info,
                    )

                    # attributeForm saves to the layer. Has the feature been added to the layer?

                    self.dialog.attributeForm().save()  # this issues a commit on the transaction?
                    # TOMsMessageLog.logMessage("Form accepted", level=Qgis.Info)
                    TOMsMessageLog.logMessage(
                        "In RestrictionDialogWrapper.accept. Transaction Status 2: "
                        + str(self.transaction.currTransactionGroup.modified()),
                        level=Qgis.Info,
                    )
                    # currRestrictionLayer.updateFeature(currRestriction)  # TH (added for v3)
                    self.layer.addFeature(self.feature)  # TH (added for v3)

                else:

                    # this feature was created before this session, we need to:
                    #  - close it in the RestrictionsInProposals table
                    #  - clone it in the current Restrictions layer (with a new GeometryID and no OpenDate)
                    #  - and then stop any changes to the original feature

                    # ************* need to discuss: seems that new has become old !!!

                    TOMsMessageLog.logMessage(
                        "In RestrictionDialogWrapper.accept. Closing existing restriction. ID: "
                        + str(self.feature[idxRestrictionID]),
                        level=Qgis.Info,
                    )

                    addRestrictionToProposal(
                        self.feature[idxRestrictionID],
                        currRestrictionLayerTableID,
                        currProposalID,
                        RestrictionAction.CLOSE,
                    )  # Open = 1; Close = 2

                    newRestriction = QgsFeature(self.feature)

                    # TODO: Rethink logic here and need to unwind changes ... without triggering rollBack ??

                    newRestriction[idxRestrictionID] = newRestrictionID
                    newRestriction[idxOpenDate] = None
                    newRestriction[idxGeometryID] = None

                    self.layer.addFeature(newRestriction)

                    TOMsMessageLog.logMessage(
                        "In RestrictionDialogWrapper.accept. Clone restriction. New ID: "
                        + str(newRestriction[idxRestrictionID]),
                        level=Qgis.Info,
                    )

                    attrs2 = newRestriction.attributes()
                    TOMsMessageLog.logMessage(
                        "In RestrictionDialogWrapper.accept: clone Restriction: "
                        + str(attrs2),
                        level=Qgis.Info,
                    )
                    TOMsMessageLog.logMessage(
                        "In RestrictionDialogWrapper.accept. Clone: {}".format(
                            newRestriction.geometry().asWkt()
                        ),
                        level=Qgis.Info,
                    )

                    addRestrictionToProposal(
                        newRestriction[idxRestrictionID],
                        currRestrictionLayerTableID,
                        currProposalID,
                        RestrictionAction.OPEN,
                    )  # Open = 1; Close = 2

                    TOMsMessageLog.logMessage(
                        "In RestrictionDialogWrapper.accept. Opening clone. ID: "
                        + str(newRestriction[idxRestrictionID]),
                        level=Qgis.Info,
                    )

                    self.dialog.attributeForm().close()
                    self.feature = self.origFeature
                    self.layer.updateFeature(self.feature)
                    layerDetails = TOMsLabelLayerNames(self.layer)

                    for labelLayerName in layerDetails.getCurrLabelLayerNames():
                        labelLayer = QgsProject.instance().mapLayersByName(
                            labelLayerName
                        )[0]
                        labelLayer.reload()

            # Now commit changes and redraw

            attrs1 = self.feature.attributes()
            TOMsMessageLog.logMessage(
                "In RestrictionDialogWrapper.accept: currRestriction: " + str(attrs1),
                level=Qgis.Info,
            )
            TOMsMessageLog.logMessage(
                "In RestrictionDialogWrapper.accept. curr: {}".format(
                    self.feature.geometry().asWkt()
                ),
                level=Qgis.Info,
            )

            # Make sure that the saving will not be executed immediately, but
            # only when the event loop runs into the next iteration to avoid
            # problems

            TOMsMessageLog.logMessage(
                "In RestrictionDialogWrapper.accept. Transaction Status 3: "
                + str(self.transaction.currTransactionGroup.modified()),
                level=Qgis.Info,
            )

            self.transaction.commitTransactionGroup()
            TOMsMessageLog.logMessage(
                "In RestrictionDialogWrapper.accept. Transaction Status 4: "
                + str(self.transaction.currTransactionGroup.modified()),
                level=Qgis.Info,
            )

        self.dialog.reject()

        # ************* refresh the view. Might be able to set up a signal to get the proposals_panel to intervene

        TOMsMessageLog.logMessage(
            "In RestrictionDialogWrapper.accept. Finished", level=Qgis.Info
        )

        self.dialog.close()
        self.layer.removeSelection()

        setupPanelTabs(self.proposalPanelDock)

    def reject(self):
        TOMsMessageLog.logMessage("In RestrictionDialogWrapper.reject", level=Qgis.Info)
        self.dialog.reject()

        self.transaction.rollBackTransactionGroup()

        setupPanelTabs(self.proposalPanelDock)

    def show(self):
        self.dialog.show()
