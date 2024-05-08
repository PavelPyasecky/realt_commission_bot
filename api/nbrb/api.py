from urllib.parse import urljoin

import settings
from api.common.api_client import APIClient
from api.common.http import HTTPMethods


class BaseCurrencyAPI(APIClient):
    def __init__(self,):
        super().__init__(communication=HTTPMethods, credential={})

    def get(self, resource, headers=None, query_params=None):
        uri = urljoin(settings.NBRB_BASE_URL, resource)
        return self.communication.get(uri, headers=headers, query_params=query_params)


class CurrencyAPI(BaseCurrencyAPI):
    DOLLAR_RATE_URL = 'rates/431'

    def get_dollar_rate_data(self):
        return self.get(self.DOLLAR_RATE_URL)
