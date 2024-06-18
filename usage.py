from azure import AzureProject, AzureAuth

project = AzureProject(
    project="TeamProject",
    azure_auth=AzureAuth(
        username="AzureUsername",
        access_token="AccessToken"
    )
)

# Get list of repositories
project.repositories

# Get list of piplines
project.piplines


