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
from dagger import Container, dag, Directory, Doc, field, function, object_type, Secret, DefaultPath

from .releaserc import ReleaseRC

@object_type
class SemanticRelease:
    @function
    async def run(self,
            source: Annotated[Directory, Doc("Source directory"), DefaultPath(".")], # source directory
            branch: Annotated[str, Doc("Branch name")], # in which branch should we run the release
            username: Annotated[str, Doc("Username")],  #  GitHub username
            # repository_url: Annotated[str, Doc("Repository URL")],  # GitHub repository URL
            github_token: Annotated[Secret, Doc("Github Token")], # GitHub token
             ) -> None:
        
        releaserc = ReleaseRC()
        releaserc.add_branch(branch)
        releaserc.add_plugin("@semantic-release/commit-analyzer")
        releaserc.add_plugin("@semantic-release/release-notes-generator")
        releaserc.set_dry_run(True)
        releaserc.set_ci(True)
        releaserc.set_debug(True)
        print(releaserc.to_string())


    async def get_container(self) -> Container:
        """Get the container for running semantic release."""
        return await dag.container().from_("alpine:latest").with_directory(
            "/src",
            self.source,
        ).with_workdir("/src").with_exec(
            ["ls", "-la"]
        ).stdout()
    