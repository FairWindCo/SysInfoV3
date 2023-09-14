import win32service

from fw_automations_utils.service_utils import ServiceStatusProcessEntity


def QueryAllServicesStatus(includeDriverServices=False):
    returnValue = []
    servicesRaw = []
    serviceConfigManagerHandle = None
    try:
        serviceConfigManagerHandle = win32service.OpenSCManager('', None, win32service.SC_MANAGER_ENUMERATE_SERVICE)
        if includeDriverServices:
            servicesRaw += win32service.EnumServicesStatusEx(serviceConfigManagerHandle, win32service.SERVICE_DRIVER)

        servicesRaw += win32service.EnumServicesStatusEx(serviceConfigManagerHandle)
        for rawService in servicesRaw:
            serviceStatus = ServiceStatusProcessEntity(**rawService)
            returnValue.append(serviceStatus)
        return returnValue
    finally:
        if serviceConfigManagerHandle:
            win32service.CloseServiceHandle(serviceConfigManagerHandle)


def get_services():
    services = QueryAllServicesStatus()
    # services = ServiceController.GetServices()
    return [str(service.DisplayName) for service in services
            if str(service.CurrentState) == 'RUNNING']
