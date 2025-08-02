from urllib import response
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
        """
        token_str = await token.plaintext()
        url = f"https://api.github.com/repos/{organization}/{repo_name}/pulls/{pull_request_number}/codespaces"
        headers = {
            "Authorization": f"Bearer {token_str.strip()}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        payload = {
            "machine": "basicLinux32gb",
            "display_name": f"{repo_name}-{pull_request_number}-{branch_name}"
        }
        response = requests.post(url, json=payload, headers=headers)
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










    # @function
    # async def run(self,
    #     source: Annotated[Directory, Doc("Source directory"), DefaultPath(".")], # source directory
    #     github_token: Annotated[Secret | None, Doc("Github Token")],
    #     codespace_token: Annotated[Secret, Doc("Token for Codespace creation")],
    #     username: Annotated[str, Doc("Github Username")],  # GitHub username
    #     branch: Annotated[str, Doc("Current Branch")],  # Current branch
    #     organization: Annotated[str, Doc("Organization Name")] = "bcit-ltc",  # Organization name
    #     app_name: Annotated[str, Doc("Application Name")] = "SomeApp",  # Application name
    #         ) -> None:
    #     """
    #     Main Codespace manager entry point.
    #     """

    #     codespace_name = f"{app_name}-{branch}"
    #     codespace_exists = await self._check_if_exists(
    #         codespace_name, 
    #         app_name, 
    #         branch,
    #         organization,
    #         codespace_token)

    #     if not codespace_exists:
    #         print(f"Creating Codespace for {app_name} on branch {branch}...")
    #         # await self._create_codespace(app_name, branch, organization, codespace_token)
    #     else:
    #         print(f"Codespace for {app_name} already exists. No action taken.")


    # async def _check_if_exists(self,
    #     codespace_name: Annotated[str, Doc("Codespace Name")],
    #     app_name: Annotated[str, Doc("Application Name")],
    #     branch_name: Annotated[str, Doc("Current Branch")],
    #     organization: Annotated[str, Doc("Organization Name")],
    #     codespace_token: Annotated[Secret, Doc("Token for Codespace existence check")]
    # ) -> bool:
    #     """
    #     Check if a Codespace exists.
    #     """

    #     token_str = await codespace_token.plaintext()
    #     headers = {
    #         "Authorization": f"Bearer {token_str.strip()}",
    #         "Accept": "application/vnd.github+json"
    #     }

    #     url = "https://api.github.com/user/codespaces"
    #     response = requests.get(url, headers=headers)

    #     if response.status_code == 200:
    #         codespaces = response.json().get("codespaces", [])
    #         print(json.dumps(codespaces, indent=2))  # Debugging output
            
    #         for codespace in codespaces:
    #             print(f"Checking codespace: {codespace.get('name')}")
    #             print(f"Expected: {codespace_name}, Found: {codespace.get('name')}")
    #             if (codespace.get("repository", {}).get("full_name") == f"{organization}/{app_name}"
    #                 and codespace.get("branch") == branch_name
    #             ):
    #                 print(f"Codespace {codespace_name} exists.")
    #                 return True
    #             else:
    #                 print(f"Codespace {codespace_name} does not exist.")

    #         return False
    #     else:
    #         print(f"Failed to check codespace existence: {response.status_code} - {response.text}")
    #         raise Exception("Failed to check codespace existence")

        
        

    # async def _create_codespace(self,
    #     app_name: Annotated[str, Doc("Application Name")],  # Application name
    #     branch: Annotated[str, Doc("Current Branch")],  # Current branch
    #     organization: Annotated[str, Doc("Organization Name")],  # Organization name
    #     codespace_token: Annotated[Secret, Doc("Token for Codespace creation")]
    # ) -> None:
    #     """
    #     Create a new Codespace.
    #     """

    #     # Unwrap secret to a string value
    #     token_str = await codespace_token.plaintext()
    #     print("Received token length:", len(token_str))  # Do NOT print the token itself

    #     url = f"https://api.github.com/repos/{organization}/{app_name}/codespaces"
    #     headers = {
    #         "Authorization": f"Bearer {token_str.strip()}",
    #         "Accept": "application/vnd.github+json"
    #     }
    #     payload = {
    #         "ref": f"{branch}",
    #         "machine": "basicLinux32gb",
    #         "display_name": f"{app_name}-{branch}"
    #     }
    #     response = requests.post(url, json=payload, headers=headers)

    #     if response.status_code == 201 or response.status_code == 202:
    #         codespace_url = response.json().get("web_url")
    #         codespace_name = response.json().get("name")
    #         print(f"Codespace Name: {codespace_name}")
    #         print(f"Codespace created successfully: {codespace_url}")
    #     else:
    #         print(f"Failed to create codespace: {response.status_code} - {response.text}")
    #         raise Exception("Failed to create codespace")

    #     return None
    






















    # async def delete(self,
    #     codespace_name: Annotated[str, Doc("Codespace Name")],  # Codespace name to delete
    #     codespace_token: Annotated[Secret, Doc("Token for Codespace deletion")],
    #     ) -> None:
    #     """
    #     Delete an existing Codespace.
    #     """
    #     url = f"https://api.github.com/repos/${{ github.repository }}/codespaces/{codespace_name}"
    #     headers = {
    #         "Authorization": f"Bearer {codespace_token}",
    #         "Accept": "application/vnd.github+json"
    #     }
    #     response = requests.delete(url, headers=headers)

    #     if response.status_code == 204:
    #         print(f"Codespace {codespace_name} deleted successfully.")
    #     else:
    #         print(f"Failed to delete codespace: {response.status_code} - {response.text}")
    #         raise Exception("Failed to delete codespace")   