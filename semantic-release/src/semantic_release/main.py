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
import os

@enum_type
class CiProvider(Enum):
    NONE = "none"
    UNKNOWN = "unknown"
    GITHUB = "github"



@object_type
class SemanticRelease:
    releaserc = ReleaseRC()
    @function
    async def run(self,
            source: Annotated[Directory, Doc("Source directory"), DefaultPath(".")], # source directory
            github_token: Annotated[Secret, Doc("Github Token")],
            username: Annotated[str, Doc("Github Username")],  # GitHub username with default value
            branch: Annotated[str, Doc("Branch")] = "main",  # Default branch name
            ) -> None:
        
        print(os.environ)
        
        if github_token is not None:
            print("GITHUB_TOKEN detected")
            print("Running in GitHub Actions")
            self.ci_provider = CiProvider.GITHUB
        else:
            print("Running locally")
            self.ci_provider = CiProvider.NONE

        self.branch = branch
        self.username = username
        self.github_token = github_token

        # Configure release parameters based on the CI provider
        self._configure_release_params()
        print(f"Configured release parameters: {self.releaserc.to_string()}")

        # Create a container for running semantic release
        container = await self.semantic_release_container(source)
        # Set environment variables for the container
        await container.with_new_file(
            ".releaserc", contents=self.releaserc.to_string()
        ).with_exec(
            ["ls", "-la"]
        ).stdout()


    def _configure_release_params(self):
        self.releaserc.add_branch(self.branch)
        self.releaserc.add_plugin("@semantic-release/commit-analyzer")
        self.releaserc.add_plugin("@semantic-release/release-notes-generator")
    
        """Configure release parameters based on the CI provider."""
        if self.ci_provider == CiProvider.GITHUB:
            self.releaserc.add_plugin("@semantic-release/github")
            self.releaserc.set_ci(True)
        else:
            print("No CI provider detected. Skipping GitHub configuration.")
            self.releaserc.set_dry_run(True)
            self.releaserc.set_debug(True)


    async def semantic_release_container(self, source: Directory) -> Container:
        """Get the container for running semantic release."""
        return await dag.container().from_("alpine:latest").with_directory(
            "/app", source
        ).with_workdir("/app")
