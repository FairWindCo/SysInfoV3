import requests
from requests_ntlm import HttpNtlmAuth
if __name__ == "__main__":



    session = requests.Session()
    session.auth = HttpNtlmAuth('erc\\cwrk_ShipmentOrder', 'Q/a7GoUb]uA1')
    session.post(url="https://common.sites.local.erc/api/TaxInvoice/TaxInvoiceSaveXmlAndConfirm")