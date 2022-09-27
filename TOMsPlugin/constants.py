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

import os
from enum import Enum


class UserPermission:
    FULL_CONTROL = False
    CONFIRM_ORDERS = False
    REPORT_BAY_DATA = False
    WRITE = False
    PRINT = False
    READ = False

    @staticmethod
    def initialize():
        user_elevation = os.environ.get("DEPLOY_USER_ELEVATION", "guest")
        if user_elevation == "admin":
            UserPermission.FULL_CONTROL = True
            UserPermission.CONFIRM_ORDERS = True
            UserPermission.REPORT_BAY_DATA = True
            UserPermission.WRITE = True
            UserPermission.PRINT = True
            UserPermission.READ = True
        elif user_elevation == "write_confirm_operator":
            UserPermission.FULL_CONTROL = False
            UserPermission.CONFIRM_ORDERS = True
            UserPermission.REPORT_BAY_DATA = True
            UserPermission.WRITE = True
            UserPermission.PRINT = True
            UserPermission.READ = True
        elif user_elevation == "write_no_confirm_operator":
            UserPermission.FULL_CONTROL = False
            UserPermission.CONFIRM_ORDERS = False
            UserPermission.REPORT_BAY_DATA = True
            UserPermission.WRITE = True
            UserPermission.PRINT = True
            UserPermission.READ = True
        elif user_elevation == "read_only_operator":
            UserPermission.FULL_CONTROL = False
            UserPermission.REPORT_BAY_DATA = False
            UserPermission.CONFIRM_ORDERS = False
            UserPermission.WRITE = False
            UserPermission.PRINT = True
            UserPermission.READ = True
        elif user_elevation == "guest":
            UserPermission.FULL_CONTROL = False
            UserPermission.REPORT_BAY_DATA = False
            UserPermission.CONFIRM_ORDERS = False
            UserPermission.WRITE = False
            UserPermission.PRINT = False
            UserPermission.READ = True
        else:
            raise ValueError(f"User elevation {user_elevation} is not valid")

    @staticmethod
    def prettyPrint():
        if UserPermission.FULL_CONTROL:
            return "ADMIN"
        if UserPermission.CONFIRM_ORDERS:
            return "WRITE (CAN CONFIRM)"
        if UserPermission.WRITE:
            return "WRITE"
        if UserPermission.PRINT:
            return "READ ONLY (CAN PRINT)"
        if UserPermission.READ:
            return "READ ONLY"


class ProposalStatus(Enum):
    IN_PREPARATION = 1
    ACCEPTED = 2
    REJECTED = 3


class RestrictionAction(Enum):
    OPEN = 1
    CLOSE = 2


class RestrictionLayers(Enum):
    BAYS = 2
    LINES = 3
    RESTRICTION_POLYGONS = 4
    SIGNS = 5
    CPZS = 6
    PTAS = 7
    MAPPING_UPDATES = 101
    MAPPING_UPDATE_MASKS = 102


class RestrictionGeometryTypes(Enum):
    PARALLEL_BAY = 1
    HALF_ON_HALF_OFF = 2
    ON_PAVEMENT = 3
    PERPENDICULAR = 4
    ECHELON = 5
    PERPENDICULAR_ON_PAVEMENT = 6
    OTHER = 7
    CENTRAL_PARKING = 8
    ECHELON_ON_PAVEMENT = 9
    PARALLEL_LINE = 10
    ZIG_ZAG = 12
    PARALLEL_BAY_POLYGON = 21
    HALF_ON_HALF_OFF_POLYGON = 22
    ON_PAVEMENT_POLYGON = 23
    PERPENDICULAR_POLYGON = 24
    ECHELON_POLYGON = 25
    PERPENDICULAR_ON_PAVEMENT_POLYGON = 26
    OUTLINE_BAY_POLYGON = 28
    ECHELON_ON_PAVEMENT_POLYGON = 29
    CROSSOVER = 35

    @staticmethod
    def isBay(restGeomType):
        if isinstance(restGeomType, RestrictionGeometryTypes):
            val = restGeomType.value
        elif isinstance(restGeomType, int):
            val = restGeomType
        else:
            raise NotImplementedError(f"Type {type(restGeomType)} not implemented here")
        return val < 10 or 20 <= val < 30


def singleton(myClass):
    # From https://www.youtube.com/watch?v=6IV_FYx6MQA
    instances = {}

    def getInstance(*args, **kwargs):
        if myClass not in instances:
            instances[myClass] = myClass(*args, **kwargs)
        return instances[myClass]

    return getInstance
