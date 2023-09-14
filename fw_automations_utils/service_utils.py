import abc
from abc import ABC
from typing import Optional, Any

import win32service
#https://github.com/belvedere-trading/pywinservicemanager

class AbstactTyped(ABC):
    """ This class is the base class for all 'Configruations'. The basic idea of this
         base class is to 'box', the term being loosely used here, all of the constants to have easily readable
         and manipulated values that are mapped to their constant value.
     """

    @property
    @abc.abstractmethod
    def Mappings(self) -> Optional[dict]:
        '''
            An abstact property this returns either None or a dictionary of human readable strings
            that are then mapped to their constants for a given configuration
        '''
        raise NotImplementedError()

    def __init__(self, cls, value, listOfValidTypes, isWin32Value=False):
        self._className = cls.__class__.__name__
        self._mappings = cls.Mappings

        if isWin32Value:
            self.value = self._getWin32Value(value)
            return

        self.__validateMappedValue(value, listOfValidTypes)
        self.value = value

    def _getWin32Value(self, value):
        '''
            Should be used internally to the class. This method will return the human readable value given
            a valid win32 constant for the configuration in question
        '''
        if not self._mappings:
            return value

        # if value is not None and value not in self._mappings:
        #     AbstactTyped.__raiseMappingErrorException(self._mappings, self._className, value, isWin32Value=True)
        for key, win32value in self.iterate_items():
            if win32value == value:
                return key
        return None

    def iterate_keys(self):
        if self._mappings:
            return self._mappings.keys()
        return ()

    def iterate_items(self):
        if self._mappings:
            return self._mappings.items()
        return ()

    def __validateMappedValue(self, value, listOfValidTypes):
        '''
            Should be used internally to the class. This method validates that the value passed
            is a valid string that is mapped to a constant. If the value is invalid, and exception will be raised.
        '''
        AbstactTyped.__validateTypes(value, self._className, listOfValidTypes)
        if not self._mappings:
            return
        if value is not None and value not in self.iterate_keys():
            AbstactTyped.__raiseMappingErrorException(self._mappings, self._className, value, isWin32Value=False)

    @classmethod
    def _getPropertiesAsDict(cls):
        return dict((key, value) for (key, value) in cls._DerivedType().__dict__.items()
                    if not key.startswith('_') and not callable(value) and key != 'Mappings')

    @abc.abstractmethod
    def StringValue(self):
        """Retrieve the data as it's string Value"""
        return

    @abc.abstractmethod
    def Win32Value(self):
        """Retrieve the data as it's win32 api Value"""
        return

    @classmethod
    def _DerivedType(cls):
        '''
            This is the type of the derived class
        '''
        return cls

    def __eq__(self, other):
        if not isinstance(other, self._DerivedType()):
            return False
        return self.Win32Value() == other.Win32Value()

    def __ne__(self, other):
        result = self.__eq__(other)
        return not result

    def __str__(self):
        return str(self.StringValue())

    def __repr__(self):
        return str(self.StringValue())

    @staticmethod
    def __raiseMappingErrorException(mappingDictionary, parameterName, valueRecieved, isWin32Value):
        '''Should be used internally to the class. This method is a helper function that raises an exception
        given an incorrect mapping value
        '''
        if isWin32Value:
            validValues = ','.join([str(value) for value in mappingDictionary.values()])
        else:
            ls = list(mappingDictionary.values()) if mappingDictionary else []
            validValues = ','.join(ls + ['None'])

        errorMsg = 'The parameter {0} is not a valid value. Valid values are : {1}. Value received {2}'
        raise ValueError(errorMsg.format(parameterName, validValues, valueRecieved))

    @staticmethod
    def __validateTypes(value, derivedClassName, validTypes):
        '''Should be used internally to the class. This method does type checking for the given configuration.
        If the type of the value is passed is invalid, an excpetion will be raised.
        '''
        validTypeLength = len(validTypes)
        if not validTypes or validTypeLength == 0:
            return True

        isValid = False
        for validType in validTypes:
            if isinstance(value, validType):
                isValid = True

        if not isValid:
            validTypesAsStrings = [validType.__name__ for validType in validTypes]
            validTypesString = ','.join(validTypesAsStrings)
            errorMsg = '{0} is not a valid type. Valid Types are : {1}. Type received {2}'
            raise ValueError(errorMsg.format(derivedClassName, validTypesString, type(value)))
        return True


class ControlsAcceptedType(AbstactTyped):
    ACCEPT_NETBINDCHANGE = win32service.SERVICE_ACCEPT_NETBINDCHANGE
    ACCEPT_PARAMCHANGE = win32service.SERVICE_ACCEPT_PARAMCHANGE
    ACCEPT_PAUSE_CONTINUE = win32service.SERVICE_ACCEPT_PAUSE_CONTINUE
    ACCEPT_PRESHUTDOWN = win32service.SERVICE_ACCEPT_PRESHUTDOWN
    ACCEPT_SHUTDOWN = win32service.SERVICE_ACCEPT_SHUTDOWN
    ACCEPT_STOP = win32service.SERVICE_ACCEPT_STOP
    ACCEPT_HARDWAREPROFILECHANGE = win32service.SERVICE_ACCEPT_HARDWAREPROFILECHANGE
    ACCEPT_POWEREVENT = win32service.SERVICE_ACCEPT_POWEREVENT
    ACCEPT_SESSIONCHANGE = win32service.SERVICE_ACCEPT_SESSIONCHANGE

    @property
    def Mappings(self):
        return None

    @property
    def Types(self):
        returnValue = []
        for key, value in self._getPropertiesAsDict().items():
            if key == 'Types':
                continue
            if (value & self.value) == value:
                returnValue.append(key)
        return returnValue

    def __init__(self, value, isWin32Value=False):
        validTypes = [int]
        super(ControlsAcceptedType, self).__init__(self, value, validTypes, isWin32Value)

    def StringValue(self):
        """Retrieve the data as it's string Value"""
        return self.Types

    def Win32Value(self):
        """Retrieve the data as it's win32 api Value"""
        return self.value


class BinaryPathNameType(AbstactTyped):

    @property
    def Mappings(self):
        return None

    def __init__(self, value, isWin32Value=False):
        validTypes = [str, ]
        super(BinaryPathNameType, self).__init__(self, value, validTypes, isWin32Value)

    def StringValue(self):
        """Retrieve the data as it's string Value"""
        return self.value

    def Win32Value(self):
        """Retrieve the data as it's win32 api Value"""
        return self.value


class CheckPointType(AbstactTyped):

    @property
    def Mappings(self):
        return None

    def __init__(self, value, isWin32Value=False):
        validTypes = [int]
        super(CheckPointType, self).__init__(self, value, validTypes, isWin32Value)

    def StringValue(self):
        """Retrieve the data as it's string Value"""
        return self.value

    def Win32Value(self):
        """Retrieve the data as it's win32 api Value"""
        return self.value


class CurrentStateType(AbstactTyped):
    CONTINUE_PENDING = win32service.SERVICE_CONTINUE_PENDING
    PAUSE_PENDING = win32service.SERVICE_PAUSE_PENDING
    PAUSED = win32service.SERVICE_PAUSED
    RUNNING = win32service.SERVICE_RUNNING
    START_PENDING = win32service.SERVICE_START_PENDING
    STOP_PENDING = win32service.SERVICE_STOP_PENDING
    STOPPED = win32service.SERVICE_STOPPED

    @property
    def Mappings(self):
        return self._getPropertiesAsDict()

    def __init__(self, value, isWin32Value=False):
        validTypes = [int, str]
        super(CurrentStateType, self).__init__(self, value, validTypes, isWin32Value)

    def StringValue(self):
        """Retrieve the data as it's string Value"""
        return self.value

    def Win32Value(self):
        """Retrieve the data as it's win32 api Value"""
        return self.Mappings[self.value]


class ServiceNameType(AbstactTyped):

    @property
    def Mappings(self):
        return None

    def __init__(self, value, isWin32Value=False):
        validTypes = [str, ]
        super(ServiceNameType, self).__init__(self, value, validTypes, isWin32Value)

    def StringValue(self):
        """Retrieve the data as it's string Value"""
        return self.value

    def Win32Value(self):
        """Retrieve the data as it's win32 api Value"""
        return self.value


class ServiceSIDInfoType(AbstactTyped):
    SID_TYPE_NONE = win32service.SERVICE_SID_TYPE_NONE
    SID_TYPE_RESTRICTED = win32service.SERVICE_SID_TYPE_RESTRICTED
    SID_TYPE_UNRESTRICTED = win32service.SERVICE_SID_TYPE_UNRESTRICTED

    def __init__(self, value, isWin32Value=False):
        if value is None:
            value = 'SID_TYPE_NONE'
        super(ServiceSIDInfoType, self).__init__(self, value, [str], isWin32Value)

    @property
    def Mappings(self):
        return self._getPropertiesAsDict()

    def StringValue(self):
        """Retrieve the data as it's string Value"""
        return self.value

    def Win32Value(self):
        """Retrieve the data as it's win32 api Value"""
        return self.Mappings[self.value]


class ServiceStartNameType(AbstactTyped):

    @property
    def Mappings(self):
        return None

    def __init__(self, value, isWin32Value=False):
        validTypes = [str, type(None)]
        super(ServiceStartNameType, self).__init__(self, value, validTypes, isWin32Value)

        if value is None:
            self.value = u'LocalSystem'

    def StringValue(self):
        """Retrieve the data as it's string Value"""
        return self.value

    def Win32Value(self):
        """Retrieve the data as it's win32 api Value"""
        return self.value


class ServiceStartType(AbstactTyped):
    AUTO_START = win32service.SERVICE_AUTO_START
    DEMAND_START = win32service.SERVICE_DEMAND_START
    BOOT_START = win32service.SERVICE_BOOT_START
    DISABLED = win32service.SERVICE_DISABLED
    SYSTEM_START = win32service.SERVICE_SYSTEM_START

    @property
    def Mappings(self):
        return self._getPropertiesAsDict()

    def __init__(self, value, isWin32Value=False):
        if value is None:
            value = 'DEMAND_START'
        super(ServiceStartType, self).__init__(self, value, [], isWin32Value)

    def StringValue(self):
        """Retrieve the data as it's string Value"""
        return self.value

    def Win32Value(self):
        """Retrieve the data as it's win32 api Value"""
        return self.Mappings[self.value]


class ServiceType(AbstactTyped):
    WIN32_SHARE_PROCESS = win32service.SERVICE_WIN32_SHARE_PROCESS
    WIN32_OWN_PROCESS = win32service.SERVICE_WIN32_OWN_PROCESS
    KERNEL_DRIVER = win32service.SERVICE_KERNEL_DRIVER
    FILE_SYSTEM_DRIVER = win32service.SERVICE_FILE_SYSTEM_DRIVER
    INTERACTIVE_SHARE_PROCESS = win32service.SERVICE_INTERACTIVE_PROCESS | win32service.SERVICE_WIN32_SHARE_PROCESS
    INTERACTIVE_OWN_PROCESS = win32service.SERVICE_INTERACTIVE_PROCESS | win32service.SERVICE_WIN32_OWN_PROCESS

    @property
    def Mappings(self):
        return self._getPropertiesAsDict()

    def __init__(self, value, isWin32Value=False):
        if value is None:
            value = 'WIN32_OWN_PROCESS'
        super(ServiceType, self).__init__(self, value, [], isWin32Value)

    def StringValue(self):
        """Retrieve the data as it's string Value"""
        return self.value

    def Win32Value(self):
        """Retrieve the data as it's win32 api Value"""
        return self.Mappings[self.value]


class TagIdType(AbstactTyped):

    @property
    def Mappings(self):
        return None

    def __init__(self, value, isWin32Value=False):
        super(TagIdType, self).__init__(self, value, [], isWin32Value)

    def StringValue(self):
        """Retrieve the data as it's string Value"""
        return self.value

    def Win32Value(self):
        """Retrieve the data as it's win32 api Value"""
        return self.value


class WaitHintType(AbstactTyped):

    @property
    def Mappings(self):
        return None

    def __init__(self, value, isWin32Value=False):
        super(WaitHintType, self).__init__(self, value, [int], isWin32Value)

    def StringValue(self):
        """Retrieve the data as it's string Value"""
        return self.value

    def Win32Value(self):
        """Retrieve the data as it's win32 api Value"""
        return self.value


class Win32ExitCodeType(AbstactTyped):

    @property
    def Mappings(self):
        return None

    def __init__(self, value, isWin32Value=False):
        super(Win32ExitCodeType, self).__init__(self, value, [int], isWin32Value)

    def StringValue(self):
        """Retrieve the data as it's string Value"""
        return self.value

    def Win32Value(self):
        """Retrieve the data as it's win32 api Value"""
        return self.value


class FailureFlagType(AbstactTyped):

    @property
    def Mappings(self):
        return None

    def __init__(self, value, isWin32Value=False):
        if value is None:
            value = False
        validTypes = [bool]
        super(FailureFlagType, self).__init__(self, value, validTypes, isWin32Value)

    def StringValue(self):
        """Retrieve the data as it's string Value"""
        return self.value

    def Win32Value(self):
        """Retrieve the data as it's win32 api Value"""
        return self.value


class LoadOrderGroupType(AbstactTyped):

    @property
    def Mappings(self):
        return None

    def __init__(self, value, isWin32Value=False):
        if isinstance(value, str):
            value = str(value)
        if value is None:
            value = ''
        validTypes = [str, type(None)]
        super(LoadOrderGroupType, self).__init__(self, value, validTypes, isWin32Value)

    def StringValue(self):
        """Retrieve the data as it's string Value"""
        return self.value

    def Win32Value(self):
        """Retrieve the data as it's win32 api Value"""
        return self.value


class PreShutdownInfoType(AbstactTyped):

    @property
    def Mappings(self):
        return None

    def __init__(self, value, isWin32Value=False):
        validTypes = list(int, ) + [type(None)]
        super(PreShutdownInfoType, self).__init__(self, value, validTypes, isWin32Value)

    def StringValue(self):
        """Retrieve the data as it's string Value"""
        return self.value

    def Win32Value(self):
        """Retrieve the data as it's win32 api Value"""
        return self.value


class ProcessIdType(AbstactTyped):

    @property
    def Mappings(self):
        return None

    def __init__(self, value, isWin32Value=False):
        validTypes = [int]
        super(ProcessIdType, self).__init__(self, value, validTypes, isWin32Value)

    def StringValue(self):
        """Retrieve the data as it's string Value"""
        return self.value

    def Win32Value(self):
        """Retrieve the data as it's win32 api Value"""
        return self.value


class ServiceFlagsType(AbstactTyped):

    @property
    def Mappings(self):
        return None

    def __init__(self, value, isWin32Value=False):
        validTypes = [int]
        super(ServiceFlagsType, self).__init__(self, value, validTypes, isWin32Value)

    def StringValue(self):
        """Retrieve the data as it's string Value"""
        return self.value

    def Win32Value(self):
        """Retrieve the data as it's win32 api Value"""
        return self.value


class ErrorControlType(AbstactTyped):
    ERROR_IGNORE = win32service.SERVICE_ERROR_IGNORE
    ERROR_NORMAL = win32service.SERVICE_ERROR_NORMAL
    ERROR_SEVERE = win32service.SERVICE_ERROR_SEVERE
    ERROR_CRITICAL = win32service.SERVICE_ERROR_CRITICAL

    @property
    def Mappings(self):
        return self._getPropertiesAsDict()

    def __init__(self, value, isWin32Value=False):
        if value is None:
            value = 'ERROR_NORMAL'
        validTypes = []
        super(ErrorControlType, self).__init__(self, value, validTypes, isWin32Value)

    def StringValue(self):
        """Retrieve the data as it's string Value"""
        return self.value

    def Win32Value(self):
        """Retrieve the data as it's win32 api Value"""
        return self.Mappings[self.value]


class DependenciesType(AbstactTyped):

    @property
    def Mappings(self):
        return None

    def __init__(self, value, isWin32Value=False):
        validTypes = [list, type(None)]
        super(DependenciesType, self).__init__(self, value, validTypes, isWin32Value)

    def StringValue(self):
        """Retrieve the data as it's string Value"""
        return self.value

    def Win32Value(self):
        """Retrieve the data as it's win32 api Value"""
        return self.value


class DescriptionType(AbstactTyped):

    @property
    def Mappings(self):
        return None

    def __init__(self, value, isWin32Value=False):
        validTypes = [str, type(None)]
        super(DescriptionType, self).__init__(self, value, validTypes, isWin32Value)

    def StringValue(self):
        """Retrieve the data as it's string Value"""
        return self.value

    def Win32Value(self):
        """Retrieve the data as it's win32 api Value"""
        return self.value


class DisplayNameType(AbstactTyped):

    @property
    def Mappings(self):
        return None

    def __init__(self, value, isWin32Value=False):
        validTypes = [str, ]
        super(DisplayNameType, self).__init__(self, value, validTypes, isWin32Value)

    def StringValue(self):
        """Retrieve the data as it's string Value"""
        return self.value

    def Win32Value(self):
        """Retrieve the data as it's win32 api Value"""
        return self.value


class DelayedAutoStartInfoType(AbstactTyped):

    @property
    def Mappings(self):
        return None

    def __init__(self, value, isWin32Value=False):
        if value is None:
            value = False
        validTypes = [bool]
        super(DelayedAutoStartInfoType, self).__init__(self, value, validTypes, isWin32Value)

    def StringValue(self):
        """Retrieve the data as it's string Value"""
        return self.value

    def Win32Value(self):
        """Retrieve the data as it's win32 api Value"""
        return self.value


class FailureActionExecutionType(AbstactTyped):
    NONE = win32service.SC_ACTION_NONE
    RESTART = win32service.SC_ACTION_RESTART
    REBOOT = win32service.SC_ACTION_REBOOT
    RUN_COMMAND = win32service.SC_ACTION_RUN_COMMAND

    @property
    def Mappings(self):
        return self._getPropertiesAsDict()

    def __init__(self, value, isWin32Value=False):
        if value is None:
            value = 'NONE'
        super(FailureActionExecutionType, self).__init__(self, value, [], isWin32Value)

    def StringValue(self):
        """Retrieve the data as it's string Value"""
        return self.value

    def Win32Value(self):
        """Retrieve the data as it's win32 api Value"""
        return self.Mappings[self.value]


class FailureActionConfigurationCommandLineType(AbstactTyped):

    @property
    def Mappings(self):
        return None

    def __init__(self, value, isWin32Value=False):
        validTypes = [str, bytes, type(None)]
        super(FailureActionConfigurationCommandLineType, self).__init__(self, value, validTypes, isWin32Value)

    def StringValue(self):
        """Retrieve the data as it's string Value"""
        return self.value

    def Win32Value(self):
        """Retrieve the data as it's win32 api Value"""
        return self.value


class FailureActionConfigurationRebootMessageType(AbstactTyped):

    @property
    def Mappings(self):
        return None

    def __init__(self, value, isWin32Value=False):
        validTypes = [str, bytes, type(None)]
        super(FailureActionConfigurationRebootMessageType, self).__init__(self, value, validTypes, isWin32Value)

    def StringValue(self):
        """Retrieve the data as it's string Value"""
        return self.value

    def Win32Value(self):
        """Retrieve the data as it's win32 api Value"""
        return self.value


class FailureActionConfigurationResetPeriodType(AbstactTyped):

    @property
    def Mappings(self):
        return None

    def __init__(self, value, isWin32Value=False):
        validTypes = [int, type(None)]
        super(FailureActionConfigurationResetPeriodType, self).__init__(self, value, validTypes, isWin32Value)

    def StringValue(self):
        """Retrieve the data as it's string Value"""
        return self.value

    def Win32Value(self):
        """Retrieve the data as it's win32 api Value"""
        return self.value


class FailureActionDelayType(AbstactTyped):

    @property
    def Mappings(self):
        return None

    def __init__(self, value, isWin32Value=False):
        validTypes = list(int, ) + [type(None)]
        super(FailureActionDelayType, self).__init__(self, value, validTypes, isWin32Value)

    def StringValue(self):
        """Retrieve the data as it's string Value"""
        return self.value

    def Win32Value(self):
        """Retrieve the data as it's win32 api Value"""
        return self.value


class FailureActionType(AbstactTyped):

    @property
    def Mappings(self):
        return None

    def __init__(self, failureActionExecutionType, failureActionDelayType, isWin32Value=False):
        if not isinstance(failureActionExecutionType, FailureActionExecutionType) and \
                not isinstance(failureActionDelayType, FailureActionDelayType):
            msg = 'The argument "failureActionExecutionType" and "failureActionDelayType" are not of the types of their namesakes, '
            msg += 'and should be. failureActionExecutionType is of type {0} and failureActionDelayType is of type of {1}'
            raise ValueError(
                msg.format(type(failureActionExecutionType).__name__, type(failureActionDelayType).__name__))

        super(FailureActionType, self).__init__(self, None, [], isWin32Value)
        self.failureActionExecutionType = failureActionExecutionType if failureActionExecutionType else FailureActionExecutionType(
            None)
        self.failureActionDelayType = failureActionDelayType if failureActionDelayType else FailureActionDelayType(None)

    def StringValue(self):
        """Retrieve the data as it's string Value"""
        return {'FailureActionType': self.failureActionExecutionType.StringValue(),
                'Delay': self.failureActionDelayType.StringValue()}

    def Win32Value(self):
        """Retrieve the data as it's win32 api Value"""
        return (self.failureActionExecutionType.Win32Value(), self.failureActionDelayType.Win32Value())

    def __eq__(self, other):
        if not isinstance(other, FailureActionType):
            return False
        return self.failureActionExecutionType == other.failureActionExecutionType and \
            self.failureActionDelayType == other.failureActionDelayType


class FailureActionConfigurationType(AbstactTyped):

    @property
    def Mappings(self):
        return None

    # pylint: disable=R0913
    def __init__(self, failureActionsTypeList=None, resetPeriodType=None,
                 rebootMessageType=None, commandLineType=None, isWin32Value=False):
        self.__validateFailureActionsTypeListParameter(failureActionsTypeList)
        super(FailureActionConfigurationType, self).__init__(self, None, [], isWin32Value)

        if failureActionsTypeList is None:
            failureActionsTypeList = []
        self.failureActionsTypeList = failureActionsTypeList

        if not isinstance(resetPeriodType, FailureActionConfigurationResetPeriodType):
            resetPeriodType = FailureActionConfigurationResetPeriodType(resetPeriodType)
        self.resetPeriodType = resetPeriodType

        if not isinstance(rebootMessageType, FailureActionConfigurationRebootMessageType):
            rebootMessageType = FailureActionConfigurationRebootMessageType(rebootMessageType)
        self.rebootMessageType = rebootMessageType

        if not isinstance(commandLineType, FailureActionConfigurationCommandLineType):
            commandLineType = FailureActionConfigurationCommandLineType(commandLineType)
        self.commandLineType = commandLineType

    @staticmethod
    def GetInstanceFromDictionary(configruationAsDict):

        if 'ResetPeriod' in configruationAsDict:
            resetPeriod = configruationAsDict['ResetPeriod']

        if 'RebootMsg' in configruationAsDict:
            rebootMessage = configruationAsDict['RebootMsg']

        if 'Command' in configruationAsDict:
            commandLine = configruationAsDict['Command']

        failureActions = []
        if 'Actions' in configruationAsDict:
            for action in configruationAsDict['Actions']:
                failureActionExecutionType = FailureActionExecutionType(action[0], True)
                failureActionDelayType = FailureActionDelayType(action[1], True)
                failureAction = FailureActionType(failureActionExecutionType, failureActionDelayType)
                failureActions.append(failureAction)

        return FailureActionConfigurationType(failureActions,
                                              FailureActionConfigurationResetPeriodType(resetPeriod),
                                              FailureActionConfigurationRebootMessageType(rebootMessage),
                                              FailureActionConfigurationCommandLineType(commandLine))


class ConfigurationTypeFactory:

    @staticmethod
    def CreateConfigurationType(typeName, value, isWin32Value=False):
        typeMappings = {'ServiceName': ServiceNameType,
                        'DisplayName': DisplayNameType,
                        'BinaryPathName': BinaryPathNameType,
                        'StartType': ServiceStartType,
                        'ServiceType': ServiceType,
                        'ErrorControl': ErrorControlType,
                        'LoadOrderGroup': LoadOrderGroupType,
                        'Dependencies': DependenciesType,
                        'ServiceStartName': ServiceStartNameType,
                        'Description': DescriptionType,
                        'FailureActions': FailureActionConfigurationType,
                        'FailureFlag': FailureFlagType,
                        'PreShutdownInfo': PreShutdownInfoType,
                        'ServiceSIDInfo': ServiceSIDInfoType,
                        'DelayedAutoStartInfo': DelayedAutoStartInfoType,
                        'CurrentState': CurrentStateType,
                        'ControlsAccepted': ControlsAcceptedType,
                        'Win32ExitCode': Win32ExitCodeType,
                        'CheckPoint': CheckPointType,
                        'WaitHint': WaitHintType,
                        'ProcessId': ProcessIdType,
                        'ServiceFlags': ServiceFlagsType,
                        'TagId': TagIdType}

        if typeName in typeMappings.keys():
            if typeName == 'FailureActions':
               return FailureActionConfigurationType.GetInstanceFromDictionary(value)
            return typeMappings[typeName](value, isWin32Value)

        validValues = ','.join(typeMappings.keys())
        errorMsg = 'The parameter typeName is not a valid value. Value Passed: {0}. Valid values are : {1}'
        raise ValueError(errorMsg.format(value, validValues))


class ServiceStatusProcessEntity:
    __listOfStatusFields = ['ServiceType',
                            'CurrentState',
                            'ControlsAccepted',
                            'Win32ExitCode',
                            'CheckPoint',
                            'WaitHint',
                            'ProcessId',
                            'ServiceFlags',
                            'ServiceName',
                            'DisplayName']

    def __init__(self, **kwargs):
        self.Status = {}
        for field in self.__listOfStatusFields:
            if field not in kwargs:
                raise ValueError(
                    '"{0}" is not a field in the dictionary parameter "kwargs" and needs to be'.format(field))
            # self.Status[field] = kwargs[field]
            value = ConfigurationTypeFactory.CreateConfigurationType(field, kwargs[field], True)
            self.Status[field] = value
            setattr(self, field, value)



def QueryAllServicesStatus(includeDriverServices=False):
    returnValue = []
    servicesRaw = []
    serviceConfigManagerHandle = None
    try:
        serviceConfigManagerHandle = win32service.OpenSCManager('', None, win32service.SC_MANAGER_ALL_ACCESS)
        if includeDriverServices:
            servicesRaw += win32service.EnumServicesStatusEx(serviceConfigManagerHandle, win32service.SERVICE_DRIVER)

        servicesRaw += win32service.EnumServicesStatusEx(serviceConfigManagerHandle)
        for rawService in servicesRaw:
            serviceStatus = ServiceStatusProcessEntity(**rawService)
            returnValue.append(serviceStatus.Status)
        return returnValue
    finally:
        if serviceConfigManagerHandle:
            win32service.CloseServiceHandle(serviceConfigManagerHandle)
