"""
ChartUpdater: Dagger object for automating Helm chart version updates in GitHub repositories.
- Fetches current chart version from remote Chart.yaml (supports private repos)
- Increments semantic version
- Updates Chart.yaml and values file in repo, commits, and pushes changes
"""
from dagger import dag, function, object_type, Secret, Doc, QueryError
from typing import Annotated
import json

@object_type
class ChartUpdater:
    async def _fetch_chart_version(
        self,
        chart_yaml_url: Annotated[str, Doc("URL to Chart.yaml file, e.g. 'https://raw.githubusercontent.com/org/repo/Chart.yaml'")],
        github_token: Annotated[Secret, Doc("GitHub token for private repo access (optional)")] = None,
    ) -> str:
        """
        Fetch the current Helm chart version from a remote Chart.yaml file.
        Uses authentication if github_token is provided.
        Returns the current chart version string.
        """
        # Prepare container with curl and yq for fetching and parsing YAML
        container = (
            dag.container()
            .from_("alpine:latest")
            .with_exec(["apk", "add", "--no-cache", "curl", "yq"])
        )
        # Use token if provided for private repo access
        if github_token:
            container = container.with_secret_variable("GITHUB_TOKEN", github_token)
            curl_cmd = f"curl -s -H 'Authorization: Bearer $GITHUB_TOKEN' {chart_yaml_url} | yq '.version'"
        else:
            curl_cmd = f"curl -s {chart_yaml_url} | yq '.version'"
        # Execute command in container and parse version
        chart_version = await (
            container
            .with_exec(["sh", "-c", curl_cmd])
            .stdout()
        )
        return chart_version.strip()

    async def _update_chart_files(
        self,
        github_token: Annotated[Secret, Doc("GitHub token for authentication")],
        repository_url: Annotated[str, Doc("GitHub repository URL, e.g. 'https://github.com/org/repo.git'")],
        branch: Annotated[str, Doc("Branch to update, e.g. 'main'")],
        app_name: Annotated[str, Doc("Name of the Helm chart/app, e.g. 'my-app'")],
        new_app_version: Annotated[str, Doc("New application version, e.g. '1.2.3'")],
        new_chart_version: Annotated[str, Doc("New chart version, e.g. '1.2.4'")],
        values_file: Annotated[str, Doc("Path to values file to update, e.g. 'values.yaml'")],
    ) -> None:
        """
        Clone the repository, update Chart.yaml and values file with new versions, commit, and push changes.
        """
        repo_path = "/repo"
        chart_path = f"{repo_path}/charts/{app_name}"

        # Prepare container for git and yq operations
        container = (
            dag.container()
            .from_("alpine:latest")
            .with_exec(["apk", "add", "--no-cache", "git", "yq"])
            .with_secret_variable("GITHUB_TOKEN", github_token)
            .with_exec(["git", "config", "--global", "user.email", "github-actions[bot]@users.noreply.github.com"])
            .with_exec(["git", "config", "--global", "user.name", "github-actions[bot]"])
            .with_workdir(repo_path)
            .with_exec(["git", "clone", "--branch", branch, repository_url, "."])
            .with_workdir(chart_path)
            # Update Chart.yaml and values file with new versions
            .with_exec(["yq", "-i", f'.version = "{new_chart_version}"', "Chart.yaml"])
            .with_exec(["yq", "-i", f'.appVersion = "{new_app_version}"', "Chart.yaml"])
            .with_exec(["yq", "-i", f'.image.tag = "{new_app_version}"', values_file])
            # Set remote URL with token for push
            .with_exec([
                "sh", "-c",
                f'git remote set-url origin "https://x-access-token:$GITHUB_TOKEN@github.com/{repository_url.split("/")[-2]}/{repository_url.split("/")[-1]}.git"'
            ])
            .with_exec(["git", "add", "."])
            .with_exec([
                "git", "commit", "-m",
                f"Update {app_name}:{new_app_version} chart version to {new_chart_version}"
            ])
            .with_exec(["git", "push", "origin", branch])
        )
        await container.stdout()

    def _increment_patch_version(self, version: Annotated[str, Doc("Semantic version string, e.g. '1.2.3'")]) -> str:
        """
        Increment the patch part of a semantic version string (e.g., 1.2.3 -> 1.2.4).
        Returns the incremented version string.
        Raises ValueError if version format is invalid.
        """
        parts = version.strip().split(".")
        if len(parts) == 3:
            major, minor, patch = parts
            return f"{major}.{minor}.{int(patch) + 1}"
        raise ValueError(f"Invalid version format: {version}")

    @function
    async def updatechart(
        self,
        json_string: Annotated[str, Doc("JSON string with app_name and app_version, e.g. '{\"app_name\": \"my-app\", \"app_version\": \"1.2.3\"}'")],
        chart_yaml_url: Annotated[str, Doc("URL to Chart.yaml, e.g. 'https://raw.githubusercontent.com/org/repo/Chart.yaml'")],
        github_token: Annotated[Secret, Doc("GitHub token for authentication")],
        repository_url: Annotated[str, Doc("GitHub repository URL, e.g. 'https://github.com/org/repo.git'")],
        branch: Annotated[str, Doc("Branch to update, e.g. 'main'")],
        values_file: Annotated[str, Doc("Path to values file to update, e.g. 'values.yaml'")],
    ) -> None:
        """
        Main entrypoint: Update the Helm chart version and app version in Chart.yaml and values file.
        Raises QueryError if fetching or incrementing chart version fails.
        """
        data = json.loads(json_string)
        app_name = data["app_name"]
        app_version = data["app_version"]
        try:
            # Fetch current chart version and increment it
            current_chart_version = await self._fetch_chart_version(chart_yaml_url, github_token)
            new_chart_version = self._increment_patch_version(current_chart_version)
        except Exception as e:
            raise QueryError(f"Failed to get or increment chart version: {e}")
        
        # Update chart files in the repository
        await self._update_chart_files(
            github_token=github_token,
            repository_url=repository_url,
            branch=branch,
            app_name=app_name,
            new_app_version=app_version,
            new_chart_version=new_chart_version,
            values_file=values_file,
        )