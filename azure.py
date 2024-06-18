from base64 import b64encode
from abc import ABC

import requests


class AzureAuth():
    def __init__(self, username, access_token, instance="azure.asax.ir/tfs", collection="AsaProjects"):
        self.username = username
        self.access_token = access_token
        self.instance = instance
        self.collection = collection
    
    def get_authorization_token(self):
        return b64encode(f"{self.username}:{self.access_token}".encode('utf-8')).decode("ascii")

    
class AzureEndpoints:
    def __init__(self, azure_auth) -> None:
        self.headers = {
                'Authorization' : f'Basic {azure_auth.get_authorization_token()}'
        }

    def get(self, url, **kwargs):
        headers = kwargs.pop('headers', {})
        headers.update(self.headers)
        response = requests.get(url, headers=headers, **kwargs)
        if response.status_code != 200:
            raise Exception(f"{response.status_code} status code.\n{response.text}")
        return response

    def post(self, url, **kwargs):
        headers = kwargs.pop('headers', {})
        headers.update(self.headers)
        response = requests.post(url, headers=headers, **kwargs)
        if response.status_code != 200:
            raise Exception(f"{response.status_code} status code.\n{response.text}")
        return response


class AzureBase(ABC):
    def __init__(self, azure_auth, **kwargs):
        self.azure_auth = azure_auth
        self.endpoint = f"https://{azure_auth.instance}/{azure_auth.collection}"
        self._data = None
        self.azure_endpoints = AzureEndpoints(azure_auth=azure_auth)

    @property
    def data(self):
        if not self._data:
            self._data = self.azure_endpoints.get(self.url).json()
        return self._data

    @property
    def url(self):
        return f"{self.endpoint}?api-version=6.0-preview.1"


class AzureProject(AzureBase):
    def __init__(self, project, **kwargs) -> None:
        super(AzureProject, self).__init__(**kwargs)
        self.endpoint = f"{self.endpoint}/{project}/_apis"

    @property
    def piplines(self):
        url = f"{self.endpoint}/pipelines?api-version=6.0-preview.1"
        azure_pipline_list = self.azure_endpoints.get(url).json().get('value')
        return [AzurePipline(azure_project=self, **data) for data in azure_pipline_list]

    @property
    def repositories(self):
        url = f"{self.endpoint}/git/repositories?api-version=6.0-preview.1"
        azure_repositories_list = self.azure_endpoints.get(url).json().get('value')
        return [AzureRepository(azure_project=self, **data) for data in azure_repositories_list]


    def create_pipline(self, yaml_path, name, folder, repo):
        url = f"{self.endpoint}/pipelines?api-version=6.0-preview.1"
        body = {
            "configuration": {
                "path": yaml_path,
                "repository": {
                    "id": repo.id,
                    "name": repo.name,
                    "type": "azureReposGit"
                },
                "type": "yaml"
            },
            "name": name,
            "folder": folder
        }
        return self.azure_endpoints.post(url, json=body)


class AzureRepository(AzureBase):
    def __init__(self, id, azure_project, name, **kwargs) -> None:
        super(AzureRepository, self).__init__(azure_auth=azure_project.azure_auth)
        self.id = id
        self.name = name
        self.metadata = kwargs
        self.azure_project = azure_project
        self.endpoint = f"{self.azure_project.endpoint}/git/repositories/{self.id}"


    @property
    def items(self):
        url = f"{self.endpoint}/items?api-version=6.0-preview.1"
        return self.azure_endpoints.get(url).json()

class AzurePipline(AzureBase):
    def __init__(self, id, azure_project, **kwargs) -> None:
        super(AzurePipline, self).__init__(azure_auth=azure_project.azure_auth)
        self.id = id
        self.name = kwargs.get('name')
        self.metadata = kwargs
        self.azure_project = azure_project
        self.endpoint = f"{self.azure_project.endpoint}/pipelines/{self.id}"

    @property
    def runs(self):
        url = f"{self.endpoint}/runs?api-version=6.0-preview.1"
        azure_pipline_runs_list = self.azure_endpoints.get(url).json().get('value')
        return [AzurePiplineRun(azure_pipline=self, **data) for data in azure_pipline_runs_list]

    @property
    def detail(self):
        url = f"{self.endpoint}?api-version=6.0-preview.1"
        return self.azure_endpoints.get(url).json()
        # return [AzurePiplineRun(azure_pipline=self, **data) for data in azure_pipline_runs_list]

class AzurePiplineRun(AzureBase):
    def __init__(self, id, azure_pipline, **kwargs) -> None:
        super(AzurePiplineRun, self).__init__(azure_auth=azure_pipline.azure_auth)
        self.id = id
        self.metadata = kwargs
        self.azure_pipline = azure_pipline
        self.endpoint = f"{self.azure_pipline.endpoint}/runs/{self.id}"

    @property
    def is_succeeded(self):
        return self.data.get('result') == 'succeeded'
    
    @property
    def is_completed(self):
        return self.data.get('state') == 'completed'