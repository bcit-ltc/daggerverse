from urllib import response
from wsgiref import headers
import dagger
from dagger import dag, function, object_type, DefaultPath, Directory, Doc, Secret, Container
from typing import Annotated
import requests
import json

@object_type
class CodespaceManager:
    @function
    async def create_codespace_pull_request(self,
        source: Annotated[Directory, Doc("Source directory"), DefaultPath(".")], # source directory
        token: Annotated[Secret, Doc("Token for Codespace creation")],
        organization: Annotated[str, Doc("Organization Name")],  # Organization name
        repo_name: Annotated[str, Doc("Repository Name")],  # Repository name
        branch_name: Annotated[str, Doc("Branch Name")],  # Branch name
        pull_request_number: Annotated[int, Doc("Pull Request Number")]  # Pull request number
        ) -> None:
        """
        Create a Codespace from a pull request.
        Check if the Codespace already exists, and if not, create a new one.
        Assumes there can only be one Codespace per pull request.
        """
        token_str = await token.plaintext()
        headers = {
            "Authorization": f"Bearer {token_str.strip()}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        # Check if the Codespace already exists
        codespace_name = f"PR-{pull_request_number}"
        url = f"https://api.github.com/repos/{organization}/{repo_name}/codespaces"
        response = requests.get(url, headers=headers)
        response.json().get("codespaces", [])
        if response.status_code == 200:
            for codespace in response.json().get("codespaces", []):
                print(f"Checking codespace: {codespace.get('display_name')}")
                if codespace_name in codespace.get("display_name", ""):
                    print(f"Codespace {codespace_name} already exists.")
                    print(f"Codespace URL: {codespace.get('web_url')}")
                    print(f"Codespace Name: {codespace.get('name')}")
                    print(f"Branch: {codespace.get('git_status', {}).get('ref', '')}")
                    print(f"Created at: {codespace.get('created_at')}")
                    return None
        else:
            print(f"Failed to check codespace existence: {response.status_code} - {response.text}")
            raise Exception("Failed to check codespace existence")

        # Create a new Codespace
        url = f"https://api.github.com/repos/{organization}/{repo_name}/pulls/{pull_request_number}/codespaces"
        body = {
            # "location": # The requested location for a new codespace. Best efforts are made to respect this upon creation. Assigned by IP if not provided.
            # "geo":
            # "client_ip": # IP for location auto-detection when proxying a request
            # "machine": "basicLinux32gb", # Machine type to use for this codespace
            # "devcontainer_path": source.path,  # Path to devcontainer.json config to use for this codespace
            # "multi_repo_permissions_opt_out": True, # Whether to authorize requested permissions from devcontainer.json
            # "working_directory": f"/home/codespace/workspace/{repo_name}",  # Working directory for the codespace
            # "idle_timeout_minutes": 30,  # Idle timeout for the codespace
            "display_name": f"PR-{pull_request_number}"
            # "retention_period_minutes": 60,  # Retention period for the codespace
        }
        response = requests.post(url, json=body, headers=headers)
        print(f"Creating Codespace for PR #{pull_request_number} on branch {branch_name}...")

        if response.status_code in [201, 202]:
            codespace_url = response.json().get("web_url")
            codespace_name = response.json().get("name")
            print(f"Codespace Name: {codespace_name}")
            print(f"Codespace created successfully: {codespace_url}")
        else:
            print(f"Failed to create codespace: {response.status_code} - {response.text}")
            raise Exception("Failed to create codespace")

        return None


    @function
    async def delete_codespace_on_pr_close(self,
        source: Annotated[Directory, Doc("Source directory"), DefaultPath(".")], # source directory
        token: Annotated[Secret, Doc("Token for Codespace creation")],
        organization: Annotated[str, Doc("Organization Name")],  # Organization name
        repo_name: Annotated[str, Doc("Repository Name")],  # Repository name
        branch_name: Annotated[str, Doc("Branch Name")],  # Branch name
        pull_request_number: Annotated[int, Doc("Pull Request Number")]  # Pull request number
        ) -> None:
        """        
        Delete a Codespace when a pull request is closed.
        """
        token_str = await token.plaintext()
        headers = {
            "Authorization": f"Bearer {token_str.strip()}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        # Check if the Codespace already exists
        codespace_name = f"PR-{pull_request_number}"
        url = f"https://api.github.com/repos/{organization}/{repo_name}/codespaces"
        response = requests.get(url, headers=headers)
        response.json().get("codespaces", [])
        if response.status_code == 200:
            for codespace in response.json().get("codespaces", []):
                print(f"Checking codespace: {codespace.get('display_name')}")
                if codespace_name in codespace.get("display_name", ""):
                    print(f"Codespace {codespace_name} already exists.")
                    print(f"Codespace URL: {codespace.get('web_url')}")
                    print(f"Codespace Name: {codespace.get('name')}")
                    print(f"Branch: {codespace.get('git_status', {}).get('ref', '')}")
                    print(f"Created at: {codespace.get('created_at')}")

                    # Delete the Codespace
                    delete_url = f"https://api.github.com/{organization}/codespaces/{codespace.get('name')}"
                    print(f"Deleting Codespace: {delete_url}")
                    delete_response = requests.delete(delete_url, headers=headers)
                    if delete_response.status_code == 202:
                        print(f"Codespace {codespace_name} deleted successfully.")
                        return None
                    else:
                        print(f"Failed to delete codespace: {delete_response.status_code} - {delete_response.text}")
                        raise Exception("Failed to delete codespace")
        else:
            print(f"Failed to check codespace existence: {response.status_code} - {response.text}")
            raise Exception("Failed to check codespace existence")

        
