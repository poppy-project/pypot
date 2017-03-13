# This file is part of the REMOTE API
#
# Copyright 2006-2014 Coppelia Robotics GmbH. All rights reserved.
# marc@coppeliarobotics.com
# www.coppeliarobotics.com
#
# The REMOTE API is licensed under the terms of GNU GPL:
#
# -------------------------------------------------------------------
# The REMOTE API is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# THE REMOTE API IS DISTRIBUTED "AS IS", WITHOUT ANY EXPRESS OR IMPLIED
# WARRANTY. THE USER WILL USE IT AT HIS/HER OWN RISK. THE ORIGINAL
# AUTHORS AND COPPELIA ROBOTICS GMBH WILL NOT BE LIABLE FOR DATA LOSS,
# DAMAGES, LOSS OF PROFITS OR ANY OTHER KIND OF LOSS WHILE USING OR
# MISUSING THIS SOFTWARE.
#
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with the REMOTE API.  If not, see <http://www.gnu.org/licenses/>.
# -------------------------------------------------------------------
#
# This file was automatically created for V-REP release V3.1.3 on Sept. 30th 2014

import platform
import struct
from ctypes import *
from .vrepConst import *

#load library
libsimx = None

import os
import sys

basepath = os.path.join(os.path.dirname(__file__), 'lib')
version = '64Bit' if sys.maxsize > 2**32 else '32Bit'

if platform.system() == 'Windows':
    dyn_lib = os.path.join(basepath, 'windows', version, 'remoteApi.dll')
elif platform.system() == 'Darwin':
    dyn_lib = os.path.join(basepath, 'mac', version, 'remoteApi.dylib')
else:
    dyn_lib = os.path.join(basepath, 'linux', version, 'remoteApi.so')

libsimx = CDLL(dyn_lib)

#ctypes wrapper prototypes
c_GetJointPosition          = CFUNCTYPE(c_int32,c_int32, c_int32, POINTER(c_float), c_int32)(("simxGetJointPosition", libsimx))
c_SetJointPosition          = CFUNCTYPE(c_int32,c_int32, c_int32, c_float, c_int32)(("simxSetJointPosition", libsimx))
c_GetJointMatrix            = CFUNCTYPE(c_int32,c_int32, c_int32, POINTER(c_float), c_int32)(("simxGetJointMatrix", libsimx))
c_SetSphericalJointMatrix   = CFUNCTYPE(c_int32,c_int32, c_int32, POINTER(c_float), c_int32)(("simxSetSphericalJointMatrix", libsimx))
c_SetJointTargetVelocity    = CFUNCTYPE(c_int32,c_int32, c_int32, c_float, c_int32)(("simxSetJointTargetVelocity", libsimx))
c_SetJointTargetPosition    = CFUNCTYPE(c_int32,c_int32, c_int32, c_float, c_int32)(("simxSetJointTargetPosition", libsimx))
c_GetJointForce             = CFUNCTYPE(c_int32,c_int32, c_int32, POINTER(c_float), c_int32)(("simxGetJointForce", libsimx))
c_SetJointForce             = CFUNCTYPE(c_int32,c_int32, c_int32, c_float, c_int32)(("simxSetJointForce", libsimx))
c_ReadForceSensor           = CFUNCTYPE(c_int32,c_int32, c_int32, POINTER(c_ubyte), POINTER(c_float), POINTER(c_float), c_int32)(("simxReadForceSensor", libsimx))
c_BreakForceSensor          = CFUNCTYPE(c_int32,c_int32, c_int32, c_int32)(("simxBreakForceSensor", libsimx))
c_ReadVisionSensor          = CFUNCTYPE(c_int32,c_int32, c_int32, POINTER(c_ubyte), POINTER(POINTER(c_float)), POINTER(POINTER(c_int32)), c_int32)(("simxReadVisionSensor", libsimx))
c_GetObjectHandle           = CFUNCTYPE(c_int32,c_int32, POINTER(c_char), POINTER(c_int32), c_int32)(("simxGetObjectHandle", libsimx))
c_GetVisionSensorImage      = CFUNCTYPE(c_int32,c_int32, c_int32, POINTER(c_int32), POINTER(POINTER(c_byte)), c_ubyte, c_int32)(("simxGetVisionSensorImage", libsimx))
c_SetVisionSensorImage      = CFUNCTYPE(c_int32,c_int32, c_int32, POINTER(c_byte), c_int32, c_ubyte, c_int32)(("simxSetVisionSensorImage", libsimx))
c_GetVisionSensorDepthBuffer= CFUNCTYPE(c_int32,c_int32, c_int32, POINTER(c_int32), POINTER(POINTER(c_float)), c_int32)(("simxGetVisionSensorDepthBuffer", libsimx))
c_GetObjectChild            = CFUNCTYPE(c_int32,c_int32, c_int32, c_int32, POINTER(c_int32), c_int32)(("simxGetObjectChild", libsimx))
c_GetObjectParent           = CFUNCTYPE(c_int32,c_int32, c_int32, POINTER(c_int32), c_int32)(("simxGetObjectParent", libsimx))
c_ReadProximitySensor       = CFUNCTYPE(c_int32,c_int32, c_int32, POINTER(c_ubyte), POINTER(c_float), POINTER(c_int32), POINTER(c_float), c_int32)(("simxReadProximitySensor", libsimx))
c_LoadModel                 = CFUNCTYPE(c_int32,c_int32, POINTER(c_char), c_ubyte, POINTER(c_int32), c_int32)(("simxLoadModel", libsimx))
c_LoadUI                    = CFUNCTYPE(c_int32,c_int32, POINTER(c_char), c_ubyte, POINTER(c_int32), POINTER(POINTER(c_int32)), c_int32)(("simxLoadUI", libsimx))
c_LoadScene                 =  CFUNCTYPE(c_int32,c_int32, POINTER(c_char), c_ubyte, c_int32)(("simxLoadScene", libsimx))
c_StartSimulation           = CFUNCTYPE(c_int32,c_int32, c_int32)(("simxStartSimulation", libsimx))
c_PauseSimulation           = CFUNCTYPE(c_int32,c_int32, c_int32)(("simxPauseSimulation", libsimx))
c_StopSimulation            = CFUNCTYPE(c_int32,c_int32, c_int32)(("simxStopSimulation", libsimx))
c_GetUIHandle               = CFUNCTYPE(c_int32,c_int32, POINTER(c_char), POINTER(c_int32), c_int32)(("simxGetUIHandle", libsimx))
c_GetUISlider               = CFUNCTYPE(c_int32,c_int32, c_int32, c_int32, POINTER(c_int32), c_int32)(("simxGetUISlider", libsimx))
c_SetUISlider               = CFUNCTYPE(c_int32,c_int32, c_int32, c_int32, c_int32, c_int32)(("simxSetUISlider", libsimx))
c_GetUIEventButton          = CFUNCTYPE(c_int32,c_int32, c_int32, POINTER(c_int32), POINTER(c_int32), c_int32)(("simxGetUIEventButton", libsimx))
c_GetUIButtonProperty       = CFUNCTYPE(c_int32,c_int32, c_int32, c_int32, POINTER(c_int32), c_int32)(("simxGetUIButtonProperty", libsimx))
c_SetUIButtonProperty       = CFUNCTYPE(c_int32,c_int32, c_int32, c_int32, c_int32, c_int32)(("simxSetUIButtonProperty", libsimx))
c_AddStatusbarMessage       = CFUNCTYPE(c_int32,c_int32, POINTER(c_char), c_int32)(("simxAddStatusbarMessage", libsimx))
c_AuxiliaryConsoleOpen      = CFUNCTYPE(c_int32,c_int32, POINTER(c_char), c_int32, c_int32, POINTER(c_int32), POINTER(c_int32), POINTER(c_float), POINTER(c_float), POINTER(c_int32), c_int32)(("simxAuxiliaryConsoleOpen", libsimx))
c_AuxiliaryConsoleClose     = CFUNCTYPE(c_int32,c_int32, c_int32, c_int32)(("simxAuxiliaryConsoleClose", libsimx))
c_AuxiliaryConsolePrint     = CFUNCTYPE(c_int32,c_int32, c_int32, POINTER(c_char), c_int32)(("simxAuxiliaryConsolePrint", libsimx))
c_AuxiliaryConsoleShow      = CFUNCTYPE(c_int32,c_int32, c_int32, c_ubyte, c_int32)(("simxAuxiliaryConsoleShow", libsimx))
c_GetObjectOrientation      = CFUNCTYPE(c_int32,c_int32, c_int32, c_int32, POINTER(c_float), c_int32)(("simxGetObjectOrientation", libsimx))
c_GetObjectPosition         = CFUNCTYPE(c_int32,c_int32, c_int32, c_int32, POINTER(c_float), c_int32)(("simxGetObjectPosition", libsimx))
c_SetObjectOrientation      = CFUNCTYPE(c_int32,c_int32, c_int32, c_int32, POINTER(c_float), c_int32)(("simxSetObjectOrientation", libsimx))
c_SetObjectPosition         = CFUNCTYPE(c_int32,c_int32, c_int32, c_int32, POINTER(c_float), c_int32)(("simxSetObjectPosition", libsimx))
c_SetObjectParent           = CFUNCTYPE(c_int32,c_int32, c_int32, c_int32, c_ubyte, c_int32)(("simxSetObjectParent", libsimx))
c_SetUIButtonLabel          = CFUNCTYPE(c_int32,c_int32, c_int32, c_int32, POINTER(c_char), POINTER(c_char), c_int32)(("simxSetUIButtonLabel", libsimx))
c_GetLastErrors             = CFUNCTYPE(c_int32,c_int32, POINTER(c_int32), POINTER(POINTER(c_char)), c_int32)(("simxGetLastErrors", libsimx))
c_GetArrayParameter         = CFUNCTYPE(c_int32,c_int32, c_int32, POINTER(c_float), c_int32)(("simxGetArrayParameter", libsimx))
c_SetArrayParameter         = CFUNCTYPE(c_int32,c_int32, c_int32, POINTER(c_float), c_int32)(("simxSetArrayParameter", libsimx))
c_GetBooleanParameter       = CFUNCTYPE(c_int32,c_int32, c_int32, POINTER(c_ubyte), c_int32)(("simxGetBooleanParameter", libsimx))
c_SetBooleanParameter       = CFUNCTYPE(c_int32,c_int32, c_int32, c_ubyte, c_int32)(("simxSetBooleanParameter", libsimx))
c_GetIntegerParameter       = CFUNCTYPE(c_int32,c_int32, c_int32, POINTER(c_int32), c_int32)(("simxGetIntegerParameter", libsimx))
c_SetIntegerParameter       = CFUNCTYPE(c_int32,c_int32, c_int32, c_int32, c_int32)(("simxSetIntegerParameter", libsimx))
c_GetFloatingParameter      = CFUNCTYPE(c_int32,c_int32, c_int32, POINTER(c_float), c_int32)(("simxGetFloatingParameter", libsimx))
c_SetFloatingParameter      = CFUNCTYPE(c_int32,c_int32, c_int32, c_float, c_int32)(("simxSetFloatingParameter", libsimx))
c_GetStringParameter        = CFUNCTYPE(c_int32,c_int32, c_int32, POINTER(POINTER(c_char)), c_int32)(("simxGetStringParameter", libsimx))
c_GetCollisionHandle        = CFUNCTYPE(c_int32,c_int32, POINTER(c_char), POINTER(c_int32), c_int32)(("simxGetCollisionHandle", libsimx))
c_GetDistanceHandle         = CFUNCTYPE(c_int32,c_int32, POINTER(c_char), POINTER(c_int32), c_int32)(("simxGetDistanceHandle", libsimx))
c_ReadCollision             = CFUNCTYPE(c_int32,c_int32, c_int32, POINTER(c_ubyte), c_int32)(("simxReadCollision", libsimx))
c_ReadDistance              = CFUNCTYPE(c_int32,c_int32, c_int32, POINTER(c_float), c_int32)(("simxReadDistance", libsimx))
c_RemoveObject              = CFUNCTYPE(c_int32,c_int32, c_int32, c_int32)(("simxRemoveObject", libsimx))
c_RemoveModel               = CFUNCTYPE(c_int32,c_int32, c_int32, c_int32)(("simxRemoveModel", libsimx))
c_RemoveUI                  = CFUNCTYPE(c_int32,c_int32, c_int32, c_int32)(("simxRemoveUI", libsimx))
c_CloseScene                = CFUNCTYPE(c_int32,c_int32, c_int32)(("simxCloseScene", libsimx))
c_GetObjects                = CFUNCTYPE(c_int32,c_int32, c_int32, POINTER(c_int32), POINTER(POINTER(c_int32)), c_int32)(("simxGetObjects", libsimx))
c_DisplayDialog             = CFUNCTYPE(c_int32,c_int32, POINTER(c_char), POINTER(c_char), c_int32, POINTER(c_char), POINTER(c_float), POINTER(c_float), POINTER(c_int32), POINTER(c_int32), c_int32)(("simxDisplayDialog", libsimx))
c_EndDialog                 = CFUNCTYPE(c_int32,c_int32, c_int32, c_int32)(("simxEndDialog", libsimx))
c_GetDialogInput            = CFUNCTYPE(c_int32,c_int32, c_int32, POINTER(POINTER(c_char)), c_int32)(("simxGetDialogInput", libsimx))
c_GetDialogResult           = CFUNCTYPE(c_int32,c_int32, c_int32, POINTER(c_int32), c_int32)(("simxGetDialogResult", libsimx))
c_CopyPasteObjects          = CFUNCTYPE(c_int32,c_int32, POINTER(c_int32), c_int32, POINTER(POINTER(c_int32)), POINTER(c_int32), c_int32)(("simxCopyPasteObjects", libsimx))
c_GetObjectSelection        = CFUNCTYPE(c_int32,c_int32, POINTER(POINTER(c_int32)), POINTER(c_int32), c_int32)(("simxGetObjectSelection", libsimx))
c_SetObjectSelection        = CFUNCTYPE(c_int32,c_int32, POINTER(c_int32), c_int32, c_int32)(("simxSetObjectSelection", libsimx))
c_ClearFloatSignal          = CFUNCTYPE(c_int32,c_int32, POINTER(c_char), c_int32)(("simxClearFloatSignal", libsimx))
c_ClearIntegerSignal        = CFUNCTYPE(c_int32,c_int32, POINTER(c_char), c_int32)(("simxClearIntegerSignal", libsimx))
c_ClearStringSignal         = CFUNCTYPE(c_int32,c_int32, POINTER(c_char), c_int32)(("simxClearStringSignal", libsimx))
c_GetFloatSignal            = CFUNCTYPE(c_int32,c_int32, POINTER(c_char), POINTER(c_float), c_int32)(("simxGetFloatSignal", libsimx))
c_GetIntegerSignal          = CFUNCTYPE(c_int32,c_int32, POINTER(c_char), POINTER(c_int32), c_int32)(("simxGetIntegerSignal", libsimx))
c_GetStringSignal           = CFUNCTYPE(c_int32,c_int32, POINTER(c_char), POINTER(POINTER(c_ubyte)), POINTER(c_int32), c_int32)(("simxGetStringSignal", libsimx))
c_SetFloatSignal            = CFUNCTYPE(c_int32,c_int32, POINTER(c_char), c_float, c_int32)(("simxSetFloatSignal", libsimx))
c_SetIntegerSignal          = CFUNCTYPE(c_int32,c_int32, POINTER(c_char), c_int32, c_int32)(("simxSetIntegerSignal", libsimx))
c_SetStringSignal           = CFUNCTYPE(c_int32,c_int32, POINTER(c_char), POINTER(c_ubyte), c_int32, c_int32)(("simxSetStringSignal", libsimx))
c_AppendStringSignal        = CFUNCTYPE(c_int32,c_int32, POINTER(c_char), POINTER(c_ubyte), c_int32, c_int32)(("simxAppendStringSignal", libsimx))
c_WriteStringStream       	= CFUNCTYPE(c_int32,c_int32, POINTER(c_char), POINTER(c_ubyte), c_int32, c_int32)(("simxWriteStringStream", libsimx))
c_GetObjectFloatParameter   = CFUNCTYPE(c_int32,c_int32, c_int32, c_int32, POINTER(c_float), c_int32)(("simxGetObjectFloatParameter", libsimx))
c_SetObjectFloatParameter   = CFUNCTYPE(c_int32,c_int32, c_int32, c_int32, c_float, c_int32)(("simxSetObjectFloatParameter", libsimx))
c_GetObjectIntParameter     = CFUNCTYPE(c_int32,c_int32, c_int32, c_int32, POINTER(c_int32), c_int32)(("simxGetObjectIntParameter", libsimx))
c_SetObjectIntParameter     = CFUNCTYPE(c_int32,c_int32, c_int32, c_int32, c_int32, c_int32)(("simxSetObjectIntParameter", libsimx))
c_GetModelProperty          = CFUNCTYPE(c_int32,c_int32, c_int32, POINTER(c_int32), c_int32)(("simxGetModelProperty", libsimx))
c_SetModelProperty          = CFUNCTYPE(c_int32,c_int32, c_int32, c_int32, c_int32)(("simxSetModelProperty", libsimx))
c_Start                     = CFUNCTYPE(c_int32,POINTER(c_char), c_int32, c_ubyte, c_ubyte, c_int32, c_int32)(("simxStart", libsimx))
c_Finish                    = CFUNCTYPE(None, c_int32)(("simxFinish", libsimx))
c_GetPingTime               = CFUNCTYPE(c_int32,c_int32, POINTER(c_int32))(("simxGetPingTime", libsimx))
c_GetLastCmdTime            = CFUNCTYPE(c_int32,c_int32)(("simxGetLastCmdTime", libsimx))
c_SynchronousTrigger        = CFUNCTYPE(c_int32,c_int32)(("simxSynchronousTrigger", libsimx))
c_Synchronous               = CFUNCTYPE(c_int32,c_int32, c_ubyte)(("simxSynchronous", libsimx))
c_PauseCommunication        = CFUNCTYPE(c_int32,c_int32, c_ubyte)(("simxPauseCommunication", libsimx))
c_GetInMessageInfo          = CFUNCTYPE(c_int32,c_int32, c_int32, POINTER(c_int32))(("simxGetInMessageInfo", libsimx))
c_GetOutMessageInfo         = CFUNCTYPE(c_int32,c_int32, c_int32, POINTER(c_int32))(("simxGetOutMessageInfo", libsimx))
c_GetConnectionId           = CFUNCTYPE(c_int32,c_int32)(("simxGetConnectionId", libsimx))
c_CreateBuffer              = CFUNCTYPE(POINTER(c_ubyte), c_int32)(("simxCreateBuffer", libsimx))
c_ReleaseBuffer             = CFUNCTYPE(None, c_void_p)(("simxReleaseBuffer", libsimx))
c_TransferFile              = CFUNCTYPE(c_int32,c_int32, POINTER(c_char), POINTER(c_char), c_int32, c_int32)(("simxTransferFile", libsimx))
c_EraseFile                 = CFUNCTYPE(c_int32,c_int32, POINTER(c_char), c_int32)(("simxEraseFile", libsimx))
c_GetAndClearStringSignal   = CFUNCTYPE(c_int32,c_int32, POINTER(c_char), POINTER(POINTER(c_ubyte)), POINTER(c_int32), c_int32)(("simxGetAndClearStringSignal", libsimx))
c_ReadStringStream   		= CFUNCTYPE(c_int32,c_int32, POINTER(c_char), POINTER(POINTER(c_ubyte)), POINTER(c_int32), c_int32)(("simxReadStringStream", libsimx))
c_CreateDummy      			= CFUNCTYPE(c_int32,c_int32, c_float, POINTER(c_ubyte), POINTER(c_int32), c_int32)(("simxCreateDummy", libsimx))
c_Query           			= CFUNCTYPE(c_int32,c_int32, POINTER(c_char), POINTER(c_ubyte), c_int32, POINTER(c_char), POINTER(POINTER(c_ubyte)), POINTER(c_int32), c_int32)(("simxQuery", libsimx))
c_GetObjectGroupData		= CFUNCTYPE(c_int32,c_int32, c_int32, c_int32, POINTER(c_int32), POINTER(POINTER(c_int32)), POINTER(c_int32), POINTER(POINTER(c_int32)), POINTER(c_int32), POINTER(POINTER(c_float)), POINTER(c_int32), POINTER(POINTER(c_char)), c_int32)(("simxGetObjectGroupData", libsimx))
c_GetObjectVelocity         = CFUNCTYPE(c_int32,c_int32, c_int32, POINTER(c_float), POINTER(c_float), c_int32)(("simxGetObjectVelocity", libsimx))

import sys
p3 = sys.version_info >= (3,0)

def tbs(str):
    return bytes(str, 'ascii')


def py3compatible(f):
    if p3:
        def wrapped_f(*args, **kwargs):
            args = [tbs(a) if isinstance(a, str) else a for a in args]
            kwargs = {k: tbs(v) if isinstance(v, str) else v for k, v in kwargs.items()}

            return f(*args, **kwargs)

        return wrapped_f
    else:
        return f

#API functions
@py3compatible
def simxGetJointPosition(clientID, jointHandle, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''
    position = c_float()
    return c_GetJointPosition(clientID, jointHandle, byref(position), operationMode), position.value

@py3compatible
def simxSetJointPosition(clientID, jointHandle, position, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_SetJointPosition(clientID, jointHandle, position, operationMode)

@py3compatible
def simxGetJointMatrix(clientID, jointHandle, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''
    matrix = (c_float*12)()
    ret = c_GetJointMatrix(clientID, jointHandle, matrix, operationMode)
    arr = []
    for i in range(12):
        arr.append(matrix[i])
    return ret, arr

@py3compatible
def simxSetSphericalJointMatrix(clientID, jointHandle, matrix, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''
    matrix = (c_float*12)(*matrix)
    return c_SetSphericalJointMatrix(clientID, jointHandle, matrix, operationMode)

@py3compatible
def simxSetJointTargetVelocity(clientID, jointHandle, targetVelocity, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_SetJointTargetVelocity(clientID, jointHandle, targetVelocity, operationMode)

@py3compatible
def simxSetJointTargetPosition(clientID, jointHandle, targetPosition, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_SetJointTargetPosition(clientID, jointHandle, targetPosition, operationMode)

@py3compatible
def simxJointGetForce(clientID, jointHandle, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''
    force = c_float()
    return c_GetJointForce(clientID, jointHandle, byref(force), operationMode), force.value

@py3compatible
def simxGetJointForce(clientID, jointHandle, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''
    force = c_float()
    return c_GetJointForce(clientID, jointHandle, byref(force), operationMode), force.value

@py3compatible
def simxSetJointForce(clientID, jointHandle, force, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''
    return c_SetJointForce(clientID, jointHandle, force, operationMode)

@py3compatible
def simxReadForceSensor(clientID, forceSensorHandle, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''
    state = c_ubyte()
    forceVector  = (c_float*3)()
    torqueVector = (c_float*3)()
    ret = c_ReadForceSensor(clientID, forceSensorHandle, byref(state), forceVector, torqueVector, operationMode)
    arr1 = []
    for i in range(3):
        arr1.append(forceVector[i])
    arr2 = []
    for i in range(3):
        arr2.append(torqueVector[i])
    return ret, ord(state.value), arr1, arr2

@py3compatible
def simxBreakForceSensor(clientID, forceSensorHandle, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''
    return c_BreakForceSensor(clientID, forceSensorHandle, operationMode)

@py3compatible
def simxReadVisionSensor(clientID, sensorHandle, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    detectionState = c_ubyte()
    auxValues      = pointer(c_float())
    auxValuesCount = pointer(c_int())
    ret = c_ReadVisionSensor(clientID, sensorHandle, byref(detectionState), byref(auxValues), byref(auxValuesCount), operationMode)

    auxValues2 = []
    if ret == 0:
        s = 0
        for i in range(auxValuesCount[0]):
            auxValues2.append(auxValues[s:s+auxValuesCount[i+1]])
            s += auxValuesCount[i+1]

        #free C buffers
        c_ReleaseBuffer(auxValues)
        c_ReleaseBuffer(auxValuesCount)

    return ret, bool(detectionState.value!=0), auxValues2

@py3compatible
def simxGetObjectHandle(clientID, objectName, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''
    handle = c_int()
    return c_GetObjectHandle(clientID, objectName, byref(handle), operationMode), handle.value

@py3compatible
def simxGetVisionSensorImage(clientID, sensorHandle, options, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    resolution = (c_int*2)()
    c_image  = pointer(c_byte())
    bytesPerPixel = 3
    if (options and 1) != 0:
        bytesPerPixel = 1
    ret = c_GetVisionSensorImage(clientID, sensorHandle, resolution, byref(c_image), options, operationMode)

    reso = []
    image = []
    if (ret == 0):
        image = [None]*resolution[0]*resolution[1]*bytesPerPixel
        for i in range(resolution[0] * resolution[1] * bytesPerPixel):
            image[i] = c_image[i]
        for i in range(2):
            reso.append(resolution[i])
    return ret, reso, image

@py3compatible
def simxSetVisionSensorImage(clientID, sensorHandle, image, options, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''
    size = len(image)
    image_bytes  = (c_byte*size)(*image)
    return c_SetVisionSensorImage(clientID, sensorHandle, image_bytes, size, options, operationMode)

@py3compatible
def simxGetVisionSensorDepthBuffer(clientID, sensorHandle, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''
    c_buffer  = pointer(c_float())
    resolution = (c_int*2)()
    ret = c_GetVisionSensorDepthBuffer(clientID, sensorHandle, resolution, byref(c_buffer), operationMode)
    reso = []
    buffer = []
    if (ret == 0):
        buffer = [None]*resolution[0]*resolution[1]
        for i in range(resolution[0] * resolution[1]):
            buffer[i] = c_buffer[i]
        for i in range(2):
            reso.append(resolution[i])
    return ret, reso, buffer

@py3compatible
def simxGetObjectChild(clientID, parentObjectHandle, childIndex, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''
    childObjectHandle = c_int()
    return c_GetObjectChild(clientID, parentObjectHandle, childIndex, byref(childObjectHandle), operationMode), childObjectHandle.value

@py3compatible
def simxGetObjectParent(clientID, childObjectHandle, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    parentObjectHandle = c_int()
    return c_GetObjectParent(clientID, childObjectHandle, byref(parentObjectHandle), operationMode), parentObjectHandle.value

@py3compatible
def simxReadProximitySensor(clientID, sensorHandle, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    detectionState = c_ubyte()
    detectedObjectHandle = c_int()
    detectedPoint  = (c_float*3)()
    detectedSurfaceNormalVector = (c_float*3)()
    ret = c_ReadProximitySensor(clientID, sensorHandle, byref(detectionState), detectedPoint, byref(detectedObjectHandle), detectedSurfaceNormalVector, operationMode)
    arr1 = []
    for i in range(3):
        arr1.append(detectedPoint[i])
    arr2 = []
    for i in range(3):
        arr2.append(detectedSurfaceNormalVector[i])
    return ret, bool(detectionState.value!=0), arr1, detectedObjectHandle.value, arr2

@py3compatible
def simxLoadModel(clientID, modelPathAndName, options, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''
    baseHandle = c_int()
    return c_LoadModel(clientID, modelPathAndName, options, byref(baseHandle), operationMode), baseHandle.value

@py3compatible
def simxLoadUI(clientID, uiPathAndName, options, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    count = c_int()
    uiHandles = pointer(c_int())
    ret = c_LoadUI(clientID, uiPathAndName, options, byref(count), byref(uiHandles), operationMode)

    handles = []
    if ret == 0:
        for i in range(count.value):
            handles.append(uiHandles[i])
        #free C buffers
        c_ReleaseBuffer(uiHandles)

    return ret, handles

@py3compatible
def simxLoadScene(clientID, scenePathAndName, options, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_LoadScene(clientID, scenePathAndName, options, operationMode)

@py3compatible
def simxStartSimulation(clientID, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_StartSimulation(clientID, operationMode)

@py3compatible
def simxPauseSimulation(clientID, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_PauseSimulation(clientID, operationMode)

@py3compatible
def simxStopSimulation(clientID, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_StopSimulation(clientID, operationMode)

@py3compatible
def simxGetUIHandle(clientID, uiName, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    handle = c_int()
    return c_GetUIHandle(clientID, uiName, byref(handle), operationMode), handle.value

@py3compatible
def simxGetUISlider(clientID, uiHandle, uiButtonID, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    position = c_int()
    return c_GetUISlider(clientID, uiHandle, uiButtonID, byref(position), operationMode), position.value

@py3compatible
def simxSetUISlider(clientID, uiHandle, uiButtonID, position, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_SetUISlider(clientID, uiHandle, uiButtonID, position, operationMode)

@py3compatible
def simxGetUIEventButton(clientID, uiHandle, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    uiEventButtonID = c_int()
    auxValues = (c_int*2)()
    ret = c_GetUIEventButton(clientID, uiHandle, byref(uiEventButtonID), auxValues, operationMode)
    arr = []
    for i in range(2):
        arr.append(auxValues[i])
    return ret, uiEventButtonID.value, arr

@py3compatible
def simxGetUIButtonProperty(clientID, uiHandle, uiButtonID, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    prop = c_int()
    return c_GetUIButtonProperty(clientID, uiHandle, uiButtonID, byref(prop), operationMode), prop.value

@py3compatible
def simxSetUIButtonProperty(clientID, uiHandle, uiButtonID, prop, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_SetUIButtonProperty(clientID, uiHandle, uiButtonID, prop, operationMode)

@py3compatible
def simxAddStatusbarMessage(clientID, message, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_AddStatusbarMessage(clientID, message, operationMode)

@py3compatible
def simxAuxiliaryConsoleOpen(clientID, title, maxLines, mode, position, size, textColor, backgroundColor, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    consoleHandle = c_int()
    if position != None:
        c_position = (c_int*2)(*position)
    else:
        c_position = None
    if size != None:
        c_size = (c_int*2)(*size)
    else:
        c_size = None
    if textColor != None:
        c_textColor = (c_float*3)(*textColor)
    else:
        c_textColor = None
    if backgroundColor != None:
        c_backgroundColor = (c_float*3)(*backgroundColor)
    else:
        c_backgroundColor = None
    return c_AuxiliaryConsoleOpen(clientID, title, maxLines, mode, c_position, c_size, c_textColor, c_backgroundColor, byref(consoleHandle), operationMode), consoleHandle.value

@py3compatible
def simxAuxiliaryConsoleClose(clientID, consoleHandle, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_AuxiliaryConsoleClose(clientID, consoleHandle, operationMode)

@py3compatible
def simxAuxiliaryConsolePrint(clientID, consoleHandle, txt, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_AuxiliaryConsolePrint(clientID, consoleHandle, txt, operationMode)

@py3compatible
def simxAuxiliaryConsoleShow(clientID, consoleHandle, showState, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_AuxiliaryConsoleShow(clientID, consoleHandle, showState, operationMode)

@py3compatible
def simxGetObjectOrientation(clientID, objectHandle, relativeToObjectHandle, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''
    eulerAngles = (c_float*3)()
    ret = c_GetObjectOrientation(clientID, objectHandle, relativeToObjectHandle, eulerAngles, operationMode)
    arr = []
    for i in range(3):
        arr.append(eulerAngles[i])
    return ret, arr

@py3compatible
def simxGetObjectPosition(clientID, objectHandle, relativeToObjectHandle, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''
    position = (c_float*3)()
    ret = c_GetObjectPosition(clientID, objectHandle, relativeToObjectHandle, position, operationMode)
    arr = []
    for i in range(3):
        arr.append(position[i])
    return ret, arr

@py3compatible
def simxSetObjectOrientation(clientID, objectHandle, relativeToObjectHandle, eulerAngles, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    angles = (c_float*3)(*eulerAngles)
    return c_SetObjectOrientation(clientID, objectHandle, relativeToObjectHandle, angles, operationMode)

@py3compatible
def simxSetObjectPosition(clientID, objectHandle, relativeToObjectHandle, position, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    c_position = (c_float*3)(*position)
    return c_SetObjectPosition(clientID, objectHandle, relativeToObjectHandle, c_position, operationMode)

@py3compatible
def simxSetObjectParent(clientID, objectHandle, parentObject, keepInPlace, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_SetObjectParent(clientID, objectHandle, parentObject, keepInPlace, operationMode)

@py3compatible
def simxSetUIButtonLabel(clientID, uiHandle, uiButtonID, upStateLabel, downStateLabel, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_SetUIButtonLabel(clientID, uiHandle, uiButtonID, upStateLabel, downStateLabel, operationMode)

@py3compatible
def simxGetLastErrors(clientID, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''
    errors =[]
    errorCnt = c_int()
    errorStrings = pointer(c_char())
    ret = c_GetLastErrors(clientID, byref(errorCnt), byref(errorStrings), operationMode)

    if ret == 0:
        s = 0
        for i in range(errorCnt.value):
            a = bytearray()
            while errorStrings[s] != '\0':
                a.append(errorStrings[s])
                s += 1

            s += 1 #skip null
            errors.append(str(a))

    return ret, errors

@py3compatible
def simxGetArrayParameter(clientID, paramIdentifier, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''
    paramValues = (c_float*3)()
    ret = c_GetArrayParameter(clientID, paramIdentifier, paramValues, operationMode)
    arr = []
    for i in range(3):
        arr.append(paramValues[i])
    return ret, arr

@py3compatible
def simxSetArrayParameter(clientID, paramIdentifier, paramValues, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    c_paramValues = (c_float*3)(*paramValues)
    return c_SetArrayParameter(clientID, paramIdentifier, c_paramValues, operationMode)

@py3compatible
def simxGetBooleanParameter(clientID, paramIdentifier, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    paramValue = c_ubyte()
    return c_GetBooleanParameter(clientID, paramIdentifier, byref(paramValue), operationMode), bool(paramValue.value!=0)

@py3compatible
def simxSetBooleanParameter(clientID, paramIdentifier, paramValue, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_SetBooleanParameter(clientID, paramIdentifier, paramValue, operationMode)

@py3compatible
def simxGetIntegerParameter(clientID, paramIdentifier, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    paramValue = c_int()
    return c_GetIntegerParameter(clientID, paramIdentifier, byref(paramValue), operationMode), paramValue.value

@py3compatible
def simxSetIntegerParameter(clientID, paramIdentifier, paramValue, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_SetIntegerParameter(clientID, paramIdentifier, paramValue, operationMode)

@py3compatible
def simxGetFloatingParameter(clientID, paramIdentifier, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    paramValue = c_float()
    return c_GetFloatingParameter(clientID, paramIdentifier, byref(paramValue), operationMode), paramValue.value

@py3compatible
def simxSetFloatingParameter(clientID, paramIdentifier, paramValue, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_SetFloatingParameter(clientID, paramIdentifier, paramValue, operationMode)

@py3compatible
def simxGetStringParameter(clientID, paramIdentifier, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''
    paramValue = pointer(c_char())
    ret = c_GetStringParameter(clientID, paramIdentifier, byref(paramValue), operationMode)

    a = bytearray()
    if ret == 0:
        i = 0
        while paramValue[i] != '\0':
            a.append(paramValue[i])
            i=i+1

    return ret, str(a)

@py3compatible
def simxGetCollisionHandle(clientID, collisionObjectName, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    handle = c_int()
    return c_GetCollisionHandle(clientID, collisionObjectName, byref(handle), operationMode), handle.value

@py3compatible
def simxGetDistanceHandle(clientID, distanceObjectName, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    handle = c_int()
    return c_GetDistanceHandle(clientID, distanceObjectName, byref(handle), operationMode), handle.value

@py3compatible
def simxReadCollision(clientID, collisionObjectHandle, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''
    collisionState = c_ubyte()
    return c_ReadCollision(clientID, collisionObjectHandle, byref(collisionState), operationMode), bool(collisionState.value!=0)

@py3compatible
def simxReadDistance(clientID, distanceObjectHandle, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    minimumDistance = c_float()
    return c_ReadDistance(clientID, distanceObjectHandle, byref(minimumDistance), operationMode), minimumDistance.value

@py3compatible
def simxRemoveObject(clientID, objectHandle, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_RemoveObject(clientID, objectHandle, operationMode)

@py3compatible
def simxRemoveModel(clientID, objectHandle, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_RemoveModel(clientID, objectHandle, operationMode)

@py3compatible
def simxRemoveUI(clientID, uiHandle, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_RemoveUI(clientID, uiHandle, operationMode)

@py3compatible
def simxCloseScene(clientID, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_CloseScene(clientID, operationMode)

@py3compatible
def simxGetObjects(clientID, objectType, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    objectCount = c_int()
    objectHandles = pointer(c_int())

    ret = c_GetObjects(clientID, objectType, byref(objectCount), byref(objectHandles), operationMode)
    handles = []
    if ret == 0:
        for i in range(objectCount.value):
            handles.append(objectHandles[i])

    return ret, handles


@py3compatible
def simxDisplayDialog(clientID, titleText, mainText, dialogType, initialText, titleColors, dialogColors, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''
    if titleColors != None:
        c_titleColors  = (c_float*6)(*titleColors)
    else:
        c_titleColors  = None
    if dialogColors != None:
        c_dialogColors  = (c_float*6)(*dialogColors)
    else:
        c_dialogColors  = None

    c_dialogHandle = c_int()
    c_uiHandle = c_int()
    return c_DisplayDialog(clientID, titleText, mainText, dialogType, initialText, c_titleColors, c_dialogColors, byref(c_dialogHandle), byref(c_uiHandle), operationMode), c_dialogHandle.value, c_uiHandle.value

@py3compatible
def simxEndDialog(clientID, dialogHandle, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_EndDialog(clientID, dialogHandle, operationMode)

@py3compatible
def simxGetDialogInput(clientID, dialogHandle, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''
    inputText = pointer(c_char())
    ret = c_GetDialogInput(clientID, dialogHandle, byref(inputText), operationMode)

    a = bytearray()
    if ret == 0:
        i = 0
        while inputText[i] != '\0':
            a.append(inputText[i])
            i = i+1

    return ret, str(a)


@py3compatible
def simxGetDialogResult(clientID, dialogHandle, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''
    result = c_int()
    return c_GetDialogResult(clientID, dialogHandle, byref(result), operationMode), result.value

@py3compatible
def simxCopyPasteObjects(clientID, objectHandles, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''
    c_objectHandles  = (c_int*len(objectHandles))(*objectHandles)
    newObjectCount   = c_int()
    newObjectHandles = pointer(c_int())
    ret = c_CopyPasteObjects(clientID, c_objectHandles, len(objectHandles), byref(newObjectHandles), byref(newObjectCount), operationMode)

    newobj = []
    if ret == 0:
        for i in range(newObjectCount.value):
            newobj.append(newObjectHandles[i])

    return ret, newobj


@py3compatible
def simxGetObjectSelection(clientID, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''
    objectCount   = c_int()
    objectHandles = pointer(c_int())
    ret = c_GetObjectSelection(clientID, byref(objectHandles), byref(objectCount), operationMode)

    newobj = []
    if ret == 0:
        for i in range(objectCount.value):
            newobj.append(objectHandles[i])

    return ret, newobj



@py3compatible
def simxSetObjectSelection(clientID, objectHandles, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    c_objectHandles  = (c_int*len(objectHandles))(*objectHandles)
    return c_SetObjectSelection(clientID, c_objectHandles, len(objectHandles), operationMode)

@py3compatible
def simxClearFloatSignal(clientID, signalName, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_ClearFloatSignal(clientID, signalName, operationMode)

@py3compatible
def simxClearIntegerSignal(clientID, signalName, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_ClearIntegerSignal(clientID, signalName, operationMode)

@py3compatible
def simxClearStringSignal(clientID, signalName, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_ClearStringSignal(clientID, signalName, operationMode)

@py3compatible
def simxGetFloatSignal(clientID, signalName, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    signalValue = c_float()
    return c_GetFloatSignal(clientID, signalName, byref(signalValue), operationMode), signalValue.value

@py3compatible
def simxGetIntegerSignal(clientID, signalName, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    signalValue = c_int()
    return c_GetIntegerSignal(clientID, signalName, byref(signalValue), operationMode), signalValue.value

@py3compatible
def simxGetStringSignal(clientID, signalName, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    signalLength = c_int();
    signalValue = pointer(c_ubyte())
    ret = c_GetStringSignal(clientID, signalName, byref(signalValue), byref(signalLength), operationMode)

    a = bytearray()
    if ret == 0:
        for i in range(signalLength.value):
            a.append(signalValue[i])

    return ret, str(a)

@py3compatible
def simxGetAndClearStringSignal(clientID, signalName, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    signalLength = c_int();
    signalValue = pointer(c_ubyte())
    ret = c_GetAndClearStringSignal(clientID, signalName, byref(signalValue), byref(signalLength), operationMode)

    a = bytearray()
    if ret == 0:
        for i in range(signalLength.value):
            a.append(signalValue[i])

    return ret, str(a)

@py3compatible
def simxReadStringStream(clientID, signalName, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    signalLength = c_int();
    signalValue = pointer(c_ubyte())
    ret = c_ReadStringStream(clientID, signalName, byref(signalValue), byref(signalLength), operationMode)

    a = bytearray()
    if ret == 0:
        for i in range(signalLength.value):
            a.append(signalValue[i])

    return ret, str(a)

@py3compatible
def simxSetFloatSignal(clientID, signalName, signalValue, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_SetFloatSignal(clientID, signalName, signalValue, operationMode)

@py3compatible
def simxSetIntegerSignal(clientID, signalName, signalValue, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_SetIntegerSignal(clientID, signalName, signalValue, operationMode)

@py3compatible
def simxSetStringSignal(clientID, signalName, signalValue, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_SetStringSignal(clientID, signalName, signalValue, len(signalValue), operationMode)

@py3compatible
def simxAppendStringSignal(clientID, signalName, signalValue, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_AppendStringSignal(clientID, signalName, signalValue, len(signalValue), operationMode)

@py3compatible
def simxWriteStringStream(clientID, signalName, signalValue, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_WriteStringStream(clientID, signalName, signalValue, len(signalValue), operationMode)

@py3compatible
def simxGetObjectFloatParameter(clientID, objectHandle, parameterID, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    parameterValue = c_float()
    return c_GetObjectFloatParameter(clientID, objectHandle, parameterID, byref(parameterValue), operationMode), parameterValue.value

@py3compatible
def simxSetObjectFloatParameter(clientID, objectHandle, parameterID, parameterValue, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_SetObjectFloatParameter(clientID, objectHandle, parameterID, parameterValue, operationMode)

@py3compatible
def simxGetObjectIntParameter(clientID, objectHandle, parameterID, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    parameterValue = c_int()
    return c_GetObjectIntParameter(clientID, objectHandle, parameterID, byref(parameterValue), operationMode), parameterValue.value

@py3compatible
def simxSetObjectIntParameter(clientID, objectHandle, parameterID, parameterValue, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_SetObjectIntParameter(clientID, objectHandle, parameterID, parameterValue, operationMode)

@py3compatible
def simxGetModelProperty(clientID, objectHandle, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''
    prop = c_int()
    return c_GetModelProperty(clientID, objectHandle, byref(prop), operationMode), prop.value

@py3compatible
def simxSetModelProperty(clientID, objectHandle, prop, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_SetModelProperty(clientID, objectHandle, prop, operationMode)

@py3compatible
def simxStart(connectionAddress, connectionPort, waitUntilConnected, doNotReconnectOnceDisconnected, timeOutInMs, commThreadCycleInMs):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_Start(connectionAddress, connectionPort, waitUntilConnected, doNotReconnectOnceDisconnected, timeOutInMs, commThreadCycleInMs)

@py3compatible
def simxFinish(clientID):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_Finish(clientID)

@py3compatible
def simxGetPingTime(clientID):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''
    pingTime = c_int()
    return c_GetPingTime(clientID, byref(pingTime)), pingTime.value

@py3compatible
def simxGetLastCmdTime(clientID):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_GetLastCmdTime(clientID)

def simxSynchronousTrigger(clientID):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_SynchronousTrigger(clientID)

@py3compatible
def simxSynchronous(clientID, enable):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_Synchronous(clientID, enable)

@py3compatible
def simxPauseCommunication(clientID, enable):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_PauseCommunication(clientID, enable)

@py3compatible
def simxGetInMessageInfo(clientID, infoType):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''
    info = c_int()
    return c_GetInMessageInfo(clientID, infoType, byref(info)), info.value

@py3compatible
def simxGetOutMessageInfo(clientID, infoType):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''
    info = c_int()
    return c_GetOutMessageInfo(clientID, infoType, byref(info)), info.value

@py3compatible
def simxGetConnectionId(clientID):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_GetConnectionId(clientID)

@py3compatible
def simxCreateBuffer(bufferSize):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_CreateBuffer(bufferSize)

@py3compatible
def simxReleaseBuffer(buffer):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_ReleaseBuffer(buffer)

@py3compatible
def simxTransferFile(clientID, filePathAndName, fileName_serverSide, timeOut, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_TransferFile(clientID, filePathAndName, fileName_serverSide, timeOut, operationMode)

@py3compatible
def simxEraseFile(clientID, fileName_serverSide, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    return c_EraseFile(clientID, fileName_serverSide, operationMode)

@py3compatible
def simxCreateDummy(clientID, size, color, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    handle = c_int()
    if color != None:
        c_color = (c_ubyte*12)(*color)
    else:
        c_color = None
    return c_CreateDummy(clientID, size, c_color, byref(handle), operationMode), handle.value

@py3compatible
def simxQuery(clientID, signalName, signalValue, retSignalName, timeOutInMs):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    retSignalLength = c_int();
    retSignalValue = pointer(c_ubyte())

    ret = c_Query(clientID, signalName, signalValue, len(signalValue), retSignalName, byref(retSignalValue), byref(retSignalLength), timeOutInMs)

    a = bytearray()
    if ret == 0:
        for i in range(retSignalLength.value):
            a.append(retSignalValue[i])

    return ret, str(a)

@py3compatible
def simxGetObjectGroupData(clientID, objectType, dataType, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''

    handles =[]
    intData =[]
    floatData =[]
    stringData =[]
    handlesC = c_int()
    handlesP = pointer(c_int())
    intDataC = c_int()
    intDataP = pointer(c_int())
    floatDataC = c_int()
    floatDataP = pointer(c_float())
    stringDataC = c_int()
    stringDataP = pointer(c_char())
    ret = c_GetObjectGroupData(clientID, objectType, dataType, byref(handlesC), byref(handlesP), byref(intDataC), byref(intDataP), byref(floatDataC), byref(floatDataP), byref(stringDataC), byref(stringDataP), operationMode)

    if ret == 0:
        for i in range(handlesC.value):
            handles.append(handlesP[i])
        for i in range(intDataC.value):
            intData.append(intDataP[i])
        for i in range(floatDataC.value):
            floatData.append(floatDataP[i])
        s = 0
        for i in range(stringDataC.value):
            a = bytearray()
            while stringDataP[s] != '\0':
                a.append(stringDataP[s])
                s += 1
            s += 1 #skip null
            stringData.append(str(a))

    return ret, handles, intData, floatData, stringData

@py3compatible
def simxGetObjectVelocity(clientID, objectHandle, operationMode):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''
    linearVel  = (c_float*3)()
    angularVel = (c_float*3)()
    ret = c_GetObjectVelocity(clientID, objectHandle, linearVel, angularVel, operationMode)
    arr1 = []
    for i in range(3):
        arr1.append(linearVel[i])
    arr2 = []
    for i in range(3):
        arr2.append(angularVel[i])
    return ret, arr1, arr2

@py3compatible
def simxPackInts(intList):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''
    s=''
    for i in range(len(intList)):
        s+=struct.pack('<i',intList[i])
    return s

@py3compatible
def simxUnpackInts(intsPackedInString):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''
    b=[]
    for i in range(len(intsPackedInString)/4):
        b.append(struct.unpack('<i',intsPackedInString[4*i:4*(i+1)])[0])
    return b

@py3compatible
def simxPackFloats(floatList):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''
    s=''
    for i in range(len(floatList)):
        s+=struct.pack('<f',floatList[i])
    return s

@py3compatible
def simxUnpackFloats(floatsPackedInString):
    '''
    Please have a look at the function description/documentation in the V-REP user manual
    '''
    b=[]
    for i in range(len(floatsPackedInString)/4):
        b.append(struct.unpack('<f',floatsPackedInString[4*i:4*(i+1)])[0])
    return b
