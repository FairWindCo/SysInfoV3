 export HTTPS_PROXY=http://fw01.bs.local.erc:8080/
 export https_proxy=http://fw01.bs.local.erc:8080/
 export HTTP_PROXY=http://fw01.bs.local.erc:8080/
 export http_proxy=http://fw01.bs.local.erc:8080/

 apt-get install libssl-dev
 apt install libkrb5-dev


/home/admin_root/SysInfoV3/.env/bin/python3 -m pip install rsa --proxy http://fw01.bs.local.erc:8080/
/home/admin_root/SysInfoV3/.env/bin/python3 -m pip install requests_kerberos --proxy http://fw01.bs.local.erc:8080/
/home/admin_root/SysInfoV3/.env/bin/python3 -m pip install pywinrm[kerberos] --proxy http://fw01.bs.local.erc:8080/

requests_ntlm



certifi==2023.7.22
cffi==1.15.1
charset-normalizer==3.2.0
cryptography==41.0.3
decorator==5.1.1
gssapi==1.8.3
idna==3.4
krb5==0.5.1
pyasn1==0.5.0
pycparser==2.21
pyspnego==0.9.2
requests==2.31.0
requests-kerberos==0.14.0
requests-ntlm==1.2.0
rsa==4.9
urllib3==2.0.4
