"""
Semantic Release Dagger Module

This Dagger module extends the functionality of the [semantic-release](https://github.com/semantic-release/semantic-release) 
project, providing a containerized and declarative pipeline for fully automated software release workflows. 
Built with [Dagger](https://dagger.io/), this module enables advanced CI/CD customization and composability 
while preserving the core principles of semantic versioning and automated changelog generation.

Features:
- Encapsulates semantic-release as a Dagger pipeline step
- Supports custom plugin injection and configuration
- Optimized for portability and reproducibility across CI environments
- Easily integrable with larger Dagger-based CI/CD pipelines

Attribution:
This module builds on the foundation provided by the [semantic-release](https://github.com/semantic-release/semantic-release) 
project, maintained by its contributors. All semantic-release core functionalities remain under their original 
[license and guidelines](https://github.com/semantic-release/semantic-release/blob/master/LICENSE).
"""

from typing import Annotated, Self
from dagger import Container, dag, Directory, Doc, field, function, object_type, Secret, DefaultPath, enum_type

from enum import Enum

from .releaserc import ReleaseRC

@enum_type
class CiProvider(Enum):
    NONE = "none"
    UNKNOWN = "unknown"
    GITHUB = "github"

SEMANTIC_RELEASE_IMAGE = f"ghcr.io/bcit-ltc/semantic-release:latest"
VERSION_OUTPUT_FILE = "version.txt"

@object_type
class SemanticRelease:
    releaserc = ReleaseRC()
    version = "0.0.0"
    @function
    async def run(self,
            source: Annotated[Directory, Doc("Source directory"), DefaultPath(".")], # source directory
            github_token: Annotated[Secret, Doc("Github Token")] | None,
            username: Annotated[str, Doc("Github Username")],  # GitHub username
            # branch: Annotated[str, Doc("Branch")],  # Default branch name
            # repository: Annotated[str, Doc("Repository")] # GitHub repository
            ) -> str:

        if github_token is not None:
            print("GITHUB_TOKEN detected")
            print("Running in GitHub Actions")
            self.ci_provider = CiProvider.GITHUB
            self.github_token = github_token
            self.branch = "main"
            self.username = username
        else:
            print("Running locally, Semantic Release skipped")
            self.ci_provider = CiProvider.NONE
            return None

        # Configure release parameters based on the CI provider
        self.configure_release_params()
        print(f"Configured release parameters: {self.releaserc.to_string()}")

        # Create a container for running semantic release
        container = await self.prepare_semantic_release_container(source)

        # Run semantic release for GitHub Actions
        if self.ci_provider == CiProvider.GITHUB:
            print("Running in GitHub Actions")
            container = await self.github_actions_runner(container)
        else:
            print("Running locally, Semantic Release skipped")
            return None
        
        #Getting the version from the output file
        version = await container.with_exec(["cat", VERSION_OUTPUT_FILE]).stdout()

        print(f"Version: {version}")
        return version

    def configure_release_params(self):
        self.releaserc.add_branch(self.branch)
        self.releaserc.add_plugin("@semantic-release/commit-analyzer")
        self.releaserc.add_plugin("@semantic-release/release-notes-generator")

        exec_plugin = [
            "@semantic-release/exec",
            {
                "verifyReleaseCmd": f"echo ${{nextRelease.version}} > {VERSION_OUTPUT_FILE}"
            }
        ]
        
        self.releaserc.add_plugin(exec_plugin)

        """Configure release parameters based on the CI provider."""
        if self.ci_provider == CiProvider.GITHUB:
            # see https://github.com/semantic-release/github?tab=readme-ov-file#options
            # for more information on the options
            github_plugin = [
                "@semantic-release/github",
                {
                    "addReleases": "top",
                }
            ]

            self.releaserc.add_plugin(github_plugin)
            self.releaserc.set_dry_run(False)
            self.releaserc.set_debug(False)
            self.releaserc.set_ci(True)
        else:
            print("No CI provider detected, running in local mode")
            self.releaserc.set_dry_run(True)
            self.releaserc.set_debug(True)
            self.releaserc.set_ci(False)


    async def prepare_semantic_release_container(self, source: Directory) -> Container:
        """Prepare the container for running semantic release.
        This functions specifies the container image and the working directory and
        copies the source directory to the container"""
        return await dag.container().from_(SEMANTIC_RELEASE_IMAGE).with_directory(
            "/app", source
        ).with_workdir("/app")


    async def github_actions_runner(self, container: Container) -> Container:
        """Run semantic release in GitHub Actions. This mimics the GitHub Actions environment
        by setting the GITHUB_REF and GITHUB_ACTIONS environment variables.
        This is needed by semantic release to determine the current branch and to indicate that
        this is a GitHub Actions environment"""
        return await container.with_new_file(
            ".releaserc", contents=self.releaserc.to_string()
        ).with_exec(
            ["ls", "-la"]
        ).with_exec(
            ["cat", ".releaserc"]
        ).with_secret_variable("GITHUB_TOKEN", self.github_token
        ).with_env_variable("GITHUB_USERNAME", self.username
        ).with_env_variable("GITHUB_ACTOR", self.username
        ).with_env_variable("GITHUB_REF", f"refs/heads/{self.branch}"
        ).with_env_variable("GITHUB_ACTIONS", "true"
        ).with_exec(["npx", "semantic-release"])
