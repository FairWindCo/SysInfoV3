import requests
from requests.adapters import HTTPAdapter
from requests_kerberos import HTTPKerberosAuth
from urllib3.util import parse_url

class HTTPAdapterWithProxyKerberosAuth(HTTPAdapter):
    def proxy_headers(self, proxy):
        headers = {}
        auth = HTTPKerberosAuth()
        negotiate_details = auth.generate_request_header(None, parse_url(proxy).host, is_preemptive=True)
        headers['Proxy-Authorization'] = negotiate_details
        return headers


if __name__ == "__main__":
    session = requests.Session()
    session.proxies = {'http': 'http://yourproxy:proxyport', 'https': 'http://yourproxy:proxyport'}
    session.mount('https://', HTTPAdapterWithProxyKerberosAuth())

    response = session.get(r"https://www.google.com/")