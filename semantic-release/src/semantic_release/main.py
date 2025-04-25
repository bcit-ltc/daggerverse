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

import json
from typing import Annotated
from enum import Enum
from dagger import Container, dag, Directory, Doc, function, object_type, Secret, DefaultPath, enum_type, QueryError
from .releaserc import ReleaseRC


@enum_type
class CiProvider(Enum):
    NONE = "none"
    UNKNOWN = "unknown"
    GITHUB = "github"

SEMANTIC_RELEASE_IMAGE = f"ghcr.io/bcit-ltc/semantic-release:latest"
NEXT_RELEASE_FILE = "next-release.txt"
LAST_RELEASE_FILE = "last-release.txt"
APP_DIR = "/app"

@object_type
class SemanticRelease:
    releaserc = ReleaseRC()
    branch = "main"

    @function
    async def semanticrelease(self,
            source: Annotated[Directory, Doc("Source directory"), DefaultPath(".")], # source directory
            github_token: Annotated[Secret, Doc("Github Token")] | None,
            username: Annotated[str, Doc("Github Username")] = "local",  # GitHub username
            dry_run: Annotated[bool, Doc("Dry run mode")] = False, # dry run mode, ignored in local mode(defaults True)
            debug: Annotated[bool, Doc("Debug mode")] = False, # debug mode, ignored in local mode(defaults True)
            ci: Annotated[bool, Doc("CI mode")] = True, # CI mode defaults to true, ignored in local mode(defaults False)
            ) -> str:
        
        self.github_token = github_token
        self.username = username
        self.dry_run = dry_run
        self.debug = debug
        self.ci = ci

        if github_token is not None:
            print("GITHUB_TOKEN detected")
            print("Running in GitHub Actions")
            self.ci_provider = CiProvider.GITHUB
        else:
            print("Running locally, Semantic Release dry run mode with commit analyzer")
            self.ci_provider = CiProvider.NONE

        # Configure release parameters based on the CI provider
        self._configure_release_params()
        print(f"Configured release parameters: {self.releaserc.to_string()}")

        # Create a container for running semantic release
        container = await self._prepare_semantic_release_container(source)

        # Run semantic release for GitHub Actions
        if self.ci_provider == CiProvider.GITHUB:
            print("Running in GitHub Actions")
            container = await self._github_actions_runner(container)
        else:
            print("Running locally")
            container = await self._local_runner(container)
        
        #Getting the version from the output file
        try:
            output_directory = container.directory(APP_DIR)
            last_release_file = output_directory.file(LAST_RELEASE_FILE)
            last_version = (await last_release_file.contents()).strip()
            print(f"Last release version: {last_version}")
        except QueryError as e:
            print(f"Last Release Error: {e}")
            last_version = None
        
        try:
            next_release_file = output_directory.file(NEXT_RELEASE_FILE)
            next_version = (await next_release_file.contents()).strip()
            print(f"Next release version: {next_version}")
        except QueryError as e:
            print("Next Release Error: ", e)
            next_version = None
        
        result_json = { "last_release": last_version, "next_release": next_version }

        return json.dumps(result_json)
        


    def _configure_release_params(self):
        self.releaserc.add_branch(self.branch)
        self.releaserc.add_plugin("@semantic-release/commit-analyzer")

        exec_plugin = [
            "@semantic-release/exec",
            {
                "analyzeCommitsCmd": f"echo ${{lastRelease.version}} > {LAST_RELEASE_FILE}",
                "verifyReleaseCmd": f"echo ${{nextRelease.version}} > {NEXT_RELEASE_FILE}",        
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

            self.releaserc.add_plugin("@semantic-release/release-notes-generator")
            self.releaserc.set_dry_run(self.dry_run)
            self.releaserc.set_debug(self.debug)
            self.releaserc.set_ci(self.ci)
        else:
            print("No CI provider detected, running in local mode")
            self.releaserc.set_dry_run(True)
            self.releaserc.set_debug(True)
            self.releaserc.set_ci(False)


    async def _prepare_semantic_release_container(self, source: Directory) -> Container:
        """Prepare the container for running semantic release.
        This functions specifies the container image and the working directory and
        copies the source directory to the container"""
        return await dag.container().from_(SEMANTIC_RELEASE_IMAGE).with_directory(
            APP_DIR, source
        ).with_workdir(APP_DIR)

    async def _github_actions_runner(self, container: Container) -> Container:
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
        # Required for Semantic Release
        ).with_secret_variable("GITHUB_TOKEN", self.github_token
        ).with_env_variable("GITHUB_USERNAME", self.username
        ).with_env_variable("GITHUB_ACTOR", self.username
        ).with_env_variable("GITHUB_REF", f"refs/heads/{self.branch}"
        ).with_env_variable("GITHUB_ACTIONS", "true"
        ).with_exec(["npx", "semantic-release"])

    # Run local (Requires GITHUB_TOKEN environment variable)
    async def _local_runner(self, container: Container) -> Container:
        """Run semantic release locally. minimal plugins enabled"""
        return await container.with_new_file(
            ".releaserc", contents=self.releaserc.to_string()
        ).with_exec(
            ["ls", "-la"]
        ).with_exec(
            ["cat", ".releaserc"]
        ).with_exec(["npx", "semantic-release"])