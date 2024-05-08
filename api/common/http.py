import requests


class GET:
    @staticmethod
    def get(uri, headers=None, query_params=None, auth=None):
        response = requests.get(uri, headers=headers, params=query_params, auth=auth)
        response.raise_for_status()
        return response.json()


class POST:
    @staticmethod
    def post(uri, headers, body, query_params):
        response = requests.post(uri, headers=headers, json=body, query_params=query_params)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def post_data(uri, headers, body):
        response = requests.post(uri, headers=headers, data=body)
        response.raise_for_status()
        return response.json()


class DELETE:
    @staticmethod
    def delete(uri, headers):
        response = requests.delete(uri, headers=headers)
        response.raise_for_status()
        return True


class HEAD:
    @staticmethod
    def head(uri, headers):
        response = requests.head(uri, headers=headers)
        response.raise_for_status()
        return True


class HTTPMethods(POST, GET, HEAD, DELETE):
    @staticmethod
    def build_headers(access_token):
        headers = {'Content-Type': 'application/json'}
        if access_token:
            headers.update({'Authorization': f'Bearer {access_token}'})
        return headers

