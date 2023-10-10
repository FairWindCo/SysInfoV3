import subprocess


def compile_file(file_path):
    subprocess.run(['pyinstaller', '--noconfirm', '--onefile', '--console', '--clean', '--distpath', 'd:\output',
                    file_path])


if __name__ == "__main__":
    list_compile = [
        # 'send_message.py',
        # 'send_mail.py',
        'check_powerbi.py',
        'system_info.py',
        # 'clear_profile.py',
        # 'zabbix_agent_uninstaller.py',
        # 'inactive_sessions.py',
        # 'multi_dns_record.py',
        # 'broken_session_check.py',
        # 'os_ping.py',
        # 'config_protection.py',
        # 'ad_integration\get_ad_user_emails.py',
    ]
    for compile in list_compile:
        compile_file(compile)
