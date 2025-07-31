import dagger
from dagger import dag, function, object_type, DefaultPath, Directory, Doc, Secret, Container
from typing import Annotated
import requests

@object_type
class CodespaceManager:

    @function
    async def run(self,
        source: Annotated[Directory, Doc("Source directory"), DefaultPath(".")], # source directory
        github_token: Annotated[Secret | None, Doc("Github Token")],
        codespace_token: Annotated[Secret, Doc("Token for Codespace creation")],
        username: Annotated[str, Doc("Github Username")],  # GitHub username
        branch: Annotated[str, Doc("Current Branch")],  # Current branch
        app_name: Annotated[str, Doc("Application Name")],  # Application name
        codespace_name: Annotated[str | None, Doc("Codespace Name")],  # Codespace name
            ) -> None:
        """
        Main Codespace manager entry point.
        """

        # Unwrap secret to a string value
        token_str = codespace_token.plaintext()
        print("Received token length:", len(token_str))  # Do NOT print the token itself

        url = "https://api.github.com/repos/${{ github.repository }}/codespaces"
        headers = {
            "Authorization": f"Bearer {token_str}",
            "Accept": "application/vnd.github+json"
        }
        payload = {
            "ref": f"{branch}",
            "machine": "basicLinux32gb",
            "display_name": f"{app_name}-{branch}"
        }
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 201 or response.status_code == 202:
            codespace_url = response.json().get("web_url")
            codespace_name = response.json().get("name")
            print(f"Codespace Name: {codespace_name}")
            print(f"Codespace created successfully: {codespace_url}")
        else:
            print(f"Failed to create codespace: {response.status_code} - {response.text}")
            raise Exception("Failed to create codespace")
        
    # async def create(self, 
    #     ) -> None:
    #     """
    #     Create a new Codespace.
    #     """
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