import argparse
import json
import sys
from typing import Iterable, Union

from fw_automations_utils.logger_functionality import setup_logger
from fw_automations_utils.powershell.powershell import PowerShellCommand, PowerShellRunner


def parse_array(value_for_conversion: Union[str, Iterable[str]]):
    if not isinstance(value_for_conversion, str) and isinstance(value_for_conversion, Iterable):
        return value_for_conversion
    prepare_value = value_for_conversion.strip()
    if prepare_value.startswith('{'):
        prepare_value = prepare_value[1:-1].strip()
    return [v.strip() for v in prepare_value.split(',')]


def parse_bool(value_for_conversion: str):
    if isinstance(value_for_conversion, str):
        prepare_value = value_for_conversion.strip()
        if prepare_value == 'True' or prepare_value == '1':
            return True
        elif prepare_value == 'False' or prepare_value == '0':
            return False
        else:
            return None
    else:
        return value_for_conversion == 1


def convert_named_value(value_for_conversion: str, list_of_names):
    if isinstance(value_for_conversion, str):
        prepare_value = value_for_conversion.strip()
        if not value_for_conversion:
            return None
        if prepare_value.isdigit():
            numeric = int(prepare_value)
            if numeric < len(list_of_names):
                return numeric
            raise ValueError('Incorrect Value')
        else:
            for index, name in enumerate(list_of_names):
                if name == prepare_value:
                    return index
            raise ValueError(f'Incorrect Value {value_for_conversion} in {list_of_names}')
    else:
        if value_for_conversion < len(list_of_names):
            return value_for_conversion
        raise ValueError('Incorrect Value')


def form_named_value_conversion(*list_of_names: str):
    def __converter(_value):
        return convert_named_value(_value, list_of_names)

    return __converter


def form_named_value_conversion_array(*list_of_names: str):
    def __converter(_value):
        list_values = parse_array(_value)
        return [convert_named_value(val, list_of_names) for val in list_values]

    return __converter


add_command_keys = ('ExclusionPath', 'ExclusionExtension', 'ExclusionProcess',
                    'ExclusionIpAddress', 'ThreatIDDefaultAction_Ids',
                    'ThreatIDDefaultAction_Actions', 'AttackSurfaceReductionOnlyExclusions',
                    'ControlledFolderAccessAllowedApplications',
                    'ControlledFolderAccessProtectedFolders', 'AttackSurfaceReductionRules_Ids',
                    'AttackSurfaceReductionRules_Actions',
                    'AttackSurfaceReductionRules_RuleSpecificExclusions_Id',
                    'AttackSurfaceReductionRules_RuleSpecificExclusions')

set_command_keys = {
    'ExclusionPath': parse_array,
    'ExclusionExtension': parse_array,
    'ExclusionProcess': parse_array, 'ExclusionIpAddress': parse_array,
    'RealTimeScanDirection': form_named_value_conversion('Both', 'Incoming', 'Outcoming'),
    'QuarantinePurgeItemsAfterDelay': int,
    'RemediationScheduleDay': form_named_value_conversion('Everyday', 'Sunday', 'Monday', 'Tuesday', 'Wednesday',
                                                          'Thursday', 'Friday', 'Saturday', 'Never'),
    'RemediationScheduleTime': str,
    'ReportingAdditionalActionTimeOut': int,
    'ReportingCriticalFailureTimeOut': int, 'ReportingNonCriticalTimeOut': int,
    'ServiceHealthReportInterval': int,
    'ReportDynamicSignatureDroppedEvent': parse_bool,
    'ScanAvgCPULoadFactor': int, 'CheckForSignaturesBeforeRunningScan': parse_bool,
    'ScanPurgeItemsAfterDelay': int, 'ScanOnlyIfIdleEnabled': parse_bool,
    'ScanParameters': form_named_value_conversion('FullScan', 'QuickScan'),
    'ScanScheduleDay': form_named_value_conversion('Everyday', 'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday',
                                                   'Friday', 'Saturday', 'Never'),
    'ScanScheduleQuickScanTime': str,
    'ScanScheduleTime': str,
    'ThrottleForScheduledScanOnly': parse_bool,
    'SignatureFirstAuGracePeriod': int,
    'SignatureAuGracePeriod': int,
    'SignatureDefinitionUpdateFileSharesSources': str,
    'SignatureDisableUpdateOnStartupWithoutEngine': parse_bool,
    'SignatureFallbackOrder': str, 'SharedSignaturesPath': str,
    'SignatureScheduleDay': form_named_value_conversion('Everyday', 'Sunday', 'Monday', 'Tuesday', 'Wednesday',
                                                        'Thursday', 'Friday', 'Saturday', 'Never'),
    'SignatureScheduleTime': str,
    'SignatureUpdateCatchupInterval': int,
    'SignatureUpdateInterval': int,
    'SignatureBlobUpdateInterval': int,
    'SignatureBlobFileSharesSources': str,
    'MeteredConnectionUpdates': parse_bool, 'AllowNetworkProtectionOnWinServer': parse_bool,
    'DisableDatagramProcessing': parse_bool, 'DisableCpuThrottleOnIdleScans': parse_bool,
    'MAPSReporting': form_named_value_conversion('Disabled', 'Basic', 'Advanced'),
    'SubmitSamplesConsent': form_named_value_conversion('AlwaysPrompt', 'SendSafeSamples', 'NeverSend',
                                                        'SendAllSamples'),
    'DisableAutoExclusions': parse_bool, 'DisablePrivacyMode': parse_bool,
    'RandomizeScheduleTaskTimes': parse_bool,
    'SchedulerRandomizationTime': int, 'DisableBehaviorMonitoring': parse_bool,
    'DisableIntrusionPreventionSystem': parse_bool, 'DisableIOAVProtection': parse_bool,
    'DisableRealtimeMonitoring': parse_bool, 'DisableScriptScanning': parse_bool,
    'DisableArchiveScanning': parse_bool, 'DisableCatchupFullScan': parse_bool,
    'DisableCatchupQuickScan': parse_bool, 'DisableEmailScanning': parse_bool,
    'DisableRemovableDriveScanning': parse_bool, 'DisableRestorePoint': parse_bool,
    'DisableScanningMappedNetworkDrivesForFullScan': parse_bool,
    'DisableScanningNetworkFiles': parse_bool,
    'UILockdown': parse_bool,
    'ThreatIDDefaultAction_Ids': parse_array,
    'ThreatIDDefaultAction_Actions': form_named_value_conversion_array('Clean', 'Quarantine', 'Remove', 'Allow',
                                                                       'UserDefined', 'NoAction', 'Block'),
    # }]
    'UnknownThreatDefaultAction': form_named_value_conversion('Clean', 'Quarantine', 'Remove', 'Allow', 'UserDefined',
                                                              'NoAction', 'Block'),
    'LowThreatDefaultAction': form_named_value_conversion('Clean', 'Quarantine', 'Remove', 'Allow', 'UserDefined',
                                                          'NoAction', 'Block'),
    'ModerateThreatDefaultAction': form_named_value_conversion('Clean', 'Quarantine', 'Remove', 'Allow', 'UserDefined',
                                                               'NoAction', 'Block'),
    'HighThreatDefaultAction': form_named_value_conversion('Clean', 'Quarantine', 'Remove', 'Allow', 'UserDefined',
                                                           'NoAction', 'Block'),
    'SevereThreatDefaultAction': form_named_value_conversion('Clean', 'Quarantine', 'Remove', 'Allow', 'UserDefined',
                                                             'NoAction', 'Block'),
    'DisableBlockAtFirstSeen': parse_bool,
    'PUAProtection': form_named_value_conversion('Disabled', 'Enabled', 'AuditMode'),
    'CloudBlockLevel': form_named_value_conversion('Default', 'Moderate', 'High', 'HighPlus', 'ZeroTolerance'),
    'CloudExtendedTimeout': int,
    'EnableNetworkProtection': form_named_value_conversion('Disabled', 'Enabled', 'AuditMode'),
    'EnableControlledFolderAccess': form_named_value_conversion('Disabled', 'Enabled', 'AuditMode',
                                                                'BlockDiskModificationOnly',
                                                                'AuditDiskModificationOnly'),
    'AttackSurfaceReductionOnlyExclusions': parse_array,
    'ControlledFolderAccessAllowedApplications': parse_array,
    'ControlledFolderAccessProtectedFolders': parse_array,
    'AttackSurfaceReductionRules_Ids': parse_array,
    'AttackSurfaceReductionRules_Actions': form_named_value_conversion('Disabled', 'Enabled', 'AuditMode',
                                                                       'NotConfigured', 'Warn'),
    'EnableLowCpuPriority': parse_bool,
    'EnableFileHashComputation': parse_bool,
    'EnableFullScanOnBatteryPower': parse_bool,
    'ProxyPacUrl': str,
    'ProxyServer': str,
    'ProxyBypass': str,
    'ForceUseProxyOnly': parse_bool,
    'DisableTlsParsing': parse_bool,
    'DisableHttpParsing': parse_bool,
    'DisableDnsParsing': parse_bool,
    'DisableDnsOverTcpParsing': parse_bool,
    'DisableSshParsing': parse_bool,
    'PlatformUpdatesChannel': form_named_value_conversion('NotConfigured', 'Beta', 'Preview', 'Staged', 'Broad',
                                                          'Delayed'),
    'EngineUpdatesChannel': form_named_value_conversion('NotConfigured', 'Beta', 'Preview', 'Staged', 'Broad',
                                                        'Delayed'),
    'DefinitionUpdatesChannel': form_named_value_conversion('NotConfigured', 'Staged', 'Broad', 'Delayed'),
    'DisableGradualRelease': parse_bool,
    'AllowNetworkProtectionDownLevel': parse_bool,
    'AllowDatagramProcessingOnWinServer': parse_bool,
    'EnableDnsSinkhole': parse_bool,
    'DisableInboundConnectionFiltering': parse_bool,
    'DisableRdpParsing': parse_bool,
    'DisableNetworkProtectionPerfTelemetry': parse_bool,
    'TrustLabelProtectionStatus': int,
    'AllowSwitchToAsyncInspection': parse_bool,
    'ScanScheduleOffset': int,
    'DisableTDTFeature': parse_bool,
    'DisableTamperProtection': parse_bool,
    'DisableSmtpParsing': parse_bool, 'IntelTDTEnabled': parse_bool,
    'AttackSurfaceReductionRules_RuleSpecificExclusions_Id': str,
    'AttackSurfaceReductionRules_RuleSpecificExclusions': str,
}


def process_key_value(key_name: str, key_value):
    processor = set_command_keys.get(key_name, None)
    if processor is not None:
        try:
            converted = processor(key_value)
            return key_name, converted
        except ValueError as ve:
            print(f'{key_name}: {ve}')
    else:
        return key_name, None


def get_control_config(config: dict) -> dict:
    list_control_values = [process_key_value(_key, _value) for _key, _value in config.items()]
    return {_key: _value for _key, _value in list_control_values}


def convert_str(str_value: str):
    name_part, value_part = str_value.split(':', 1)
    value_name = name_part.strip()
    _value = value_part.strip()
    return process_key_value(value_name, _value)


def get_current_config(executor):
    get_config = PowerShellCommand('Get-MpPreference')
    _r = executor.run(get_config)
    if _r.success:
        list_configs = [convert_str(one_str) for one_str in _r.out.split('\r\n') if one_str]
        current_config = {_key: _value for _key, _value in list_configs}
        return current_config
    else:
        return {}


def test_config(need_config, executor, show_info=False):
    current_config = get_current_config(executor)
    for key, need_value in need_config.items():
        if key in current_config:
            if isinstance(need_value, Iterable) and not isinstance(need_value, str):
                for need_element in need_value:
                    found = False
                    for current_element in current_config[key]:
                        found = current_element == need_element
                        if found:
                            break

                    if not found:
                        if show_info:
                            print(f'{need_element} not found in {current_config[key]}')
            elif current_config[key] != need_value:
                if show_info:
                    print(f'{key}:{need_value} !={current_config[key]}')
                return True
        else:
            if show_info:
                print(f'key {key} not found in current config')
            return True
    if show_info:
        print(f'Configuration is same!')
    return False


if __name__ == '__main__':
    default_config = {
        'ExclusionPath': ['C:\\Program Files\\Windows Defender', 'C:\\Program Files\\Zabbix Agent 2'],
        'ScanOnlyIfIdleEnabled': 0,
        'ScanAvgCPULoadFactor': 25,
        'DisableRemovableDriveScanning': 1,
        'DisableScanningMappedNetworkDrivesForFullScan': 1,
        'DisableScanningNetworkFiles': 1,
        'MAPSReporting': 2,
        'ScanParameters': 'QuickScan',
        'ScanScheduleTime': '02:00:00',
        'ScanScheduleQuickScanTime': '02:00:00',
        'RandomizeScheduleTaskTimes': 1,
        'ScanScheduleDay': 8,
        'SubmitSamplesConsent': 2,
        'EnableLowCpuPriority': 1
    }
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--show_result', action='store_true')
    parser.add_argument('-s', '--strong_setup', action='store_true')
    parser.add_argument('-f', '--force', action='store_true')
    parser.add_argument('-d', '--debug_level', action='store', default='info')
    parser.add_argument('-j', '--control_json', action='store', default=None)
    parser.add_argument('-c', '--control_config_file', action='store', default=None)
    arguments = parser.parse_args()

    if arguments.control_config_file:
        with open(arguments.control_config_file, 'rt') as f:
            json_config = json.load(f)
        default_config.update(json_config)

    if arguments.control_json:
        json_config = json.loads(arguments.control_json)
        default_config.update(json_config)

    control_config = get_control_config(default_config)
    log = setup_logger({'log_level': arguments.debug_level})
    runner = PowerShellRunner(logger_service=log)
    if not arguments.force:
        result = test_config(control_config, runner, arguments.show_result)
    else:
        result = True
    if result:
        add_command_params = {}
        set_command_params = {}
        for key, value in default_config.items():
            if key in add_command_keys:
                if isinstance(value, Iterable) and not isinstance(value, str):
                    add_command_params[key] = ','.join(f"'{val}'" for val in value)
                else:
                    add_command_params[key] = f"'{value}'"
            else:
                set_command_params[key] = value
        log.debug(add_command_params)
        log.debug(set_command_params)
        if add_command_params:
            if arguments.strong_setup:
                set_command_params.update(add_command_params)
            else:
                add_command = PowerShellCommand('Add-MpPreference', 'Force', **add_command_params)
                r = runner.run(add_command)
                if not r.success:
                    if arguments.show_result:
                        print('Error in executing Add-MpPreference')
                        print(r.out)
                    sys.exit(-1)
        if set_command_params:
            set_command = PowerShellCommand('Set-MpPreference', 'Force', **set_command_params)
            r = runner.run(set_command)
            if not r.success:
                if arguments.show_result:
                    print('Error in executing Set-MpPreference')
                    print(r.out)
                sys.exit(-1)
        result = test_config(control_config, runner)
        if result:
            if arguments.show_result:
                print('Defender configuration not set correctly')
            sys.exit(2)
        else:
            if arguments.show_result:
                print('Defender configuration set correctly')
            sys.exit(1)
    else:
        if arguments.show_result:
            print('Defender configuration is already setup')
        sys.exit(0)

# .\config_protection.exe  -v -j '{\"SchedulerRandomizationTime\": 2}'
# .\config_protection.exe  -v -j '{\"SchedulerRandomizationTime\": 2}'
# .\config_protection.exe  -v -f -s
# .\config_protection.exe  -v -f -s
