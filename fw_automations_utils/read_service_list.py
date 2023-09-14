import win32service

if __name__ == "__main__":
    returnValue = []
    servicesRaw = []
    serviceConfigManagerHandle = None
    try:
        serviceConfigManagerHandle = win32service.OpenSCManager('', None, win32service.SC_MANAGER_ENUMERATE_SERVICE)

        servicesRaw += win32service.EnumServicesStatusEx(serviceConfigManagerHandle)

        for service_dict in servicesRaw:
            service = win32service.OpenService(serviceConfigManagerHandle, service_dict['ServiceName'], win32service.SERVICE_QUERY_CONFIG)
            try:
                desc = win32service.QueryServiceConfig(service)
                service_dict['config1']=desc
                desc = win32service.QueryServiceConfig2(service, win32service.SERVICE_CONFIG_FAILURE_ACTIONS)
                service_dict['fail_action'] = desc
                desc = win32service.QueryServiceConfig2(service, win32service.SERVICE_CONFIG_DELAYED_AUTO_START_INFO)
                service_dict['start_info'] = desc
                desc = win32service.QueryServiceConfig2(service, win32service.SERVICE_CONFIG_DESCRIPTION)
                service_dict['start_info'] = desc

            finally:
                win32service.CloseServiceHandle(service)
    finally:
        if serviceConfigManagerHandle:
            win32service.CloseServiceHandle(serviceConfigManagerHandle)
    print(servicesRaw)
