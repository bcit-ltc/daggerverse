from dagger import dag, function, object_type, Secret, Doc, QueryError
from typing import Annotated
import json

@object_type
class ChartUpdater:
    async def _fetch_chart_version(self, chart_yaml_url: str, github_token: Secret = None) -> str:
        """
        Fetch the current Helm chart version from a remote Chart.yaml file.
        Supports private repositories if github_token is provided.
        """
        container = (
            dag.container()
            ._from_("alpine:latest")
            .with_exec(["apk", "add", "--no-cache", "curl", "yq"])
        )
        if github_token:
            container = container.with_secret_variable("GITHUB_TOKEN", github_token)
            curl_cmd = f"curl -s -H 'Authorization: Bearer $GITHUB_TOKEN' {chart_yaml_url} | yq '.version'"
        else:
            curl_cmd = f"curl -s {chart_yaml_url} | yq '.version'"
    
        chart_version = await (
            container
            .with_exec(["sh", "-c", curl_cmd])
            .stdout()
        )
        return chart_version.strip()

    async def _update_chart_files(
        self,
        github_token: Secret,
        username: str,
        repository_url: str,
        branch: str,
        app_name: str,
        new_app_version: str,
        new_chart_version: str,
        values_file: str,
    ) -> None:
        """
        Clone the repo, update Chart.yaml and values file, commit and push changes.
        """
        repo_path = "/repo"
        chart_path = f"{repo_path}/charts/{app_name}"

        container = (
            dag.container()
            ._from_("alpine:latest")
            .with_exec(["apk", "add", "--no-cache", "git", "yq"])
            .with_secret_variable("GITHUB_TOKEN", github_token)
            .with_env_variable("GITHUB_USERNAME", username)
            .with_env_variable("GITHUB_ACTOR", username)
            # .with_env_variable("GITHUB_REF", f"refs/heads/{branch}")
            .with_env_variable("GITHUB_ACTIONS", "true")
            .with_workdir(repo_path)
            .with_exec(["git", "clone", repository_url, "."])
            .with_workdir(chart_path)
            .with_exec(["yq", "-i", f'.version = "{new_chart_version}"', "Chart.yaml"])
            .with_exec(["yq", "-i", f'.appVersion = "{new_app_version}"', "Chart.yaml"])
            .with_exec(["yq", "-i", f'.image.tag = "{new_app_version}"', values_file])
            .with_exec(["git", "add", "."])
            .with_exec([
                "git", "commit", "-m",
                f"Update {app_name}:{new_app_version} chart version to {new_chart_version}"
            ])
            .with_exec(["git", "push", "origin", branch])
        )
        await container.stdout()

    def _increment_patch_version(self, version: str) -> str:
        """
        Increment the patch part of a semantic version string.
        """
        parts = version.strip().split(".")
        if len(parts) == 3:
            major, minor, patch = parts
            return f"{major}.{minor}.{int(patch) + 1}"
        raise ValueError(f"Invalid version format: {version}")

    @function
    async def update_chart(
        self,
        json_string: str,
        chart_yaml_url: str,
        github_token: Annotated[Secret, Doc("Github Token")],
        username: Annotated[str, Doc("Github Username")],
        repository_url: Annotated[str, Doc("Repository URL")],
        branch: Annotated[str, Doc("Branch Name")],
        values_file: Annotated[str, Doc("Values file path")],
    ) -> None:
        """
        Update the Helm chart version and app version in Chart.yaml and values file.
        """
        data = json.loads(json_string)
        app_name = data["app_name"]
        app_version = data["app_version"]

        try:
            current_chart_version = await self._fetch_chart_version(chart_yaml_url, github_token)
            new_chart_version = self._increment_patch_version(current_chart_version)
        except Exception as e:
            raise QueryError(f"Failed to get or increment chart version: {e}")

        await self._update_chart_files(
            github_token=github_token,
            username=username,
            repository_url=repository_url,
            branch=branch,
            app_name=app_name,
            new_app_version=app_version,
            new_chart_version=new_chart_version,
            values_file=values_file,
        )