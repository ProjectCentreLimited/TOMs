from qgis.core import (
    Qgis,
    QgsFeature,
    QgsFeatureRequest,
    QgsProject,
    QgsSettings,
)
from qgis.PyQt.QtWidgets import QDockWidget, QMessageBox
from qgis.utils import iface

from .core.tomsMessageLog import TOMsMessageLog


def restrictionInProposal(currRestrictionID, currRestrictionLayerID, proposalID):
    """
    Returns True if restriction is in proposal, else returns False
    """

    TOMsMessageLog.logMessage("In restrictionInProposal.", level=Qgis.Info)

    restrictionsInProposalsLayer = QgsProject.instance().mapLayersByName("RestrictionsInProposals")[0]

    restrictionFound = (
        len(
            list(
                restrictionsInProposalsLayer.getFeatures(
                    QgsFeatureRequest().setFilterExpression(
                        f"\"RestrictionID\" = '{currRestrictionID}' and "
                        f'"RestrictionTableID" = {currRestrictionLayerID} and '
                        f'"ProposalID" = {proposalID}'
                    )
                )
            )
        )
        == 1
    )

    TOMsMessageLog.logMessage(
        "In restrictionInProposal. restrictionFound: " + str(restrictionFound),
        level=Qgis.Info,
    )

    return restrictionFound


def getRestrictionLayerTableID(currRestLayer):
    """
    Returns the layer ID (the Code in RestrictionLayers layer)
    """

    TOMsMessageLog.logMessage("In getRestrictionLayerTableID.", level=Qgis.Info)

    restrictionsLayers = QgsProject.instance().mapLayersByName("RestrictionLayers")[0]

    layersTableID = 0

    # not sure if there is better way to search for something, .e.g., using SQL ??

    for layer in restrictionsLayers.getFeatures():
        if layer.attribute("RestrictionLayerName") == str(currRestLayer.name()):
            layersTableID = layer.attribute("Code")

    TOMsMessageLog.logMessage(
        "In getRestrictionLayerTableID. layersTableID: " + str(layersTableID),
        level=Qgis.Info,
    )

    return layersTableID


def deleteRestrictionInProposal(currRestrictionID, currRestrictionLayerID, proposalID):
    """
    Delete the restriction data in the restrictionInProposals layer
    (does not delete the restriction itself)
    """

    TOMsMessageLog.logMessage("In deleteRestrictionInProposal: " + str(currRestrictionID), level=Qgis.Info)

    restrictionsInProposalsLayer = QgsProject.instance().mapLayersByName("RestrictionsInProposals")[0]

    features = list(
        restrictionsInProposalsLayer.getFeatures(
            f"\"RestrictionID\" = '{currRestrictionID}' and "
            f'"RestrictionTableID" = {currRestrictionLayerID} and '
            f'"ProposalID" = {proposalID}'
        )
    )
    if len(features) == 1:
        TOMsMessageLog.logMessage(
            "In deleteRestrictionInProposal - deleting ",
            level=Qgis.Info,
        )

        return restrictionsInProposalsLayer.deleteFeature(features[0].id())

    return False


def saveLastSelectedValue(currFeature, layer, fieldName, value):
    """
    Sets the value for the attribute, and update a setting to save last selected value
    """

    TOMsMessageLog.logMessage(
        "In FormOpen:onAttributeChangedClass 2 - layer: " + str(layer.name()) + " (" + fieldName + "): " + str(value),
        level=Qgis.Info,
    )

    try:

        currFeature[fieldName] = value

    except Exception as e:

        QMessageBox.information(
            None,
            "Error",
            "onAttributeChangedClass2. Update failed for: {}({}): {}; {}".format(layer.name(), fieldName, value, e),
            QMessageBox.Ok,
        )  # rollback all changes

    QgsSettings().setValue(f"{layer.name()}/{fieldName}", value)


def getLookupDescription(lookupLayer, code):
    """
    Returns the description of the given code,
    searching in the lookupLayer
    """

    if not code:
        return None

    query = '"Code" = ' + str(code)
    request = QgsFeatureRequest().setFilterExpression(query)

    for row in lookupLayer.getFeatures(request):
        return row.attribute("Description")  # make assumption that only one row

    return None


def setupPanelTabs(panel):
    """
    To select the panel in the interface if the panel is hidden or not selected
    """

    # https://gis.stackexchange.com/questions/257603/activate-a-panel-in-tabbed-panels?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa

    dws = iface.mainWindow().findChildren(QDockWidget)
    dockstate = iface.mainWindow().dockWidgetArea(panel)
    for dockWid in dws:
        if dockWid is not panel:
            if iface.mainWindow().dockWidgetArea(dockWid) == dockstate and not dockWid.isHidden():
                iface.mainWindow().tabifyDockWidget(panel, dockWid)
    panel.raise_()


def getRestrictionLayersList(tableNames):
    """
    Returns the restriction layer list
    """

    restrictionLayers = tableNames.getLayer("RestrictionLayers")

    layerTypeList = []
    for layerType in restrictionLayers.getFeatures():

        layerID = layerType["Code"]
        layerName = layerType["RestrictionLayerName"]

        layerTypeList.append([layerID, layerName])

    # Add the labels layers...
    layerTypeList.append([2, "Bays.label_pos"])
    layerTypeList.append([3, "Lines.label_pos"])
    layerTypeList.append([3, "Lines.label_loading_pos"])
    # layerTypeList.append([5, 'Signs.label_pos'])
    layerTypeList.append([4, "RestrictionPolygons.label_pos"])
    layerTypeList.append([6, "CPZs.label_pos"])
    layerTypeList.append([7, "ParkingTariffAreas.label_pos"])

    layerTypeList.append([2, "Bays.label_ldr"])
    layerTypeList.append([3, "Lines.label_ldr"])
    layerTypeList.append([3, "Lines.label_loading_ldr"])
    # layerTypeList.append([5, 'Signs.label_ldr'])
    layerTypeList.append([4, "RestrictionPolygons.label_ldr"])
    layerTypeList.append([6, "CPZs.label_ldr"])
    layerTypeList.append([7, "ParkingTariffAreas.label_ldr"])

    return layerTypeList


def addRestrictionToProposal(restrictionID, restrictionLayerTableID, proposalID, proposedAction):
    """
    Adds restriction to the "RestrictionsInProposals" layer
    """

    TOMsMessageLog.logMessage("In addRestrictionToProposal.", level=Qgis.Info)

    restrictionsInProposalsLayer = QgsProject.instance().mapLayersByName("RestrictionsInProposals")[0]

    newRestrictionsInProposal = QgsFeature(restrictionsInProposalsLayer.fields())
    newRestrictionsInProposal["ProposalID"] = proposalID
    newRestrictionsInProposal["RestrictionID"] = restrictionID
    newRestrictionsInProposal["RestrictionTableID"] = restrictionLayerTableID
    newRestrictionsInProposal["ActionOnProposalAcceptance"] = proposedAction.value

    TOMsMessageLog.logMessage(
        "In addRestrictionToProposal. Before record create. RestrictionID: " + str(restrictionID),
        level=Qgis.Info,
    )

    return restrictionsInProposalsLayer.addFeature(newRestrictionsInProposal)
