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


@object_type
class SemanticRelease:
    # @function
    # def __init__(
    #     self,
    #     github_token: Optional[str] = None,
    #     source: Optional[str] = None,
    #     branch: Optional[str] = None,
    #     username: Optional[str] = None,
    #     ) -> None:
    #     self.mode = ReleaseMode.CI if github_token else ReleaseMode.LOCAL

    #     if self.mode == ReleaseMode.CI:
    #         if not all([source, branch, username]):
    #             raise ValueError("CI mode requires: source, branch, username")

    #     self.github_token = github_token
    #     self.source = source
    #     self.branch = branch
    #     self.username = username
    #     self.releaserc = ReleaseRC() # Initialize with an empty config
    #     self.container: Optional[Container] = None
    #     self.exec_output_file = "NEXT_VERSION"  # Store the exec output file variable

    #     self._set_required_plugins() # Set required plugins based on the mode CI or LOCAL
    #     self.releaserc.set("branches", [branch])
    #     self.releaserc.set("dryRun", False)
    #     self.releaserc.set("ci", True if self.mode == ReleaseMode.CI else False)
    #     self.releaserc.set("debug", True)
    #     self.releaserc.set("tagFormat", "${{version}}")

        # print(self.releaserc.to_dict())  # Debugging line
        # print(json.dumps(self.releaserc.to_dict(), indent=2))  # Debugging line

    @function
    async def test(self,
            source: Annotated[Directory, Doc("Source directory"), DefaultPath(".")],
            branch: Annotated[str, Doc("Branch name")],
            username: Annotated[str, Doc("Username")],
            github_token: Annotated[Secret, Doc("Github Token")],
             ) -> None:
        print("test")
        print(await source.name())
        print(branch)
        print(username)
        print(github_token)
        # release = SemanticRelease()
        await source.terminal(
            ["ls", "-la"],
        )
        


    # def _set_required_plugins(self):
    #     """Set required plugins based on the mode.
    #     This method modifies the releaserc object to include the necessary plugins
    #     for the specified mode (LOCAL or CI). It also ensures that the exec output
    #     file is always included in the plugins list.
    #     """
    #     # Always required plugins
    #     always_required_plugins = [
    #         "@semantic-release/exec",
    #         {
    #             "verifyReleaseCmd": f"echo ${{nextRelease.version}} > {self.exec_output_file}"
    #         }
    #     ]

    #     # Plugins for LOCAL mode
    #     if self.mode == ReleaseMode.LOCAL:
    #         required_plugins = [
    #             "@semantic-release/commit-analyzer",
    #             "@semantic-release/release-notes-generator"
    #         ]
    #         required_plugins.extend(always_required_plugins)
    #         for plugin in required_plugins:
    #             if plugin not in self.releaserc.get("plugins", []):
    #                 self.releaserc.add_plugin(plugin)

    #     # Plugins for CI mode
    #     elif self.mode == ReleaseMode.CI:
    #         required_plugins = [
    #             "@semantic-release/commit-analyzer",
    #             "@semantic-release/release-notes-generator",
    #             "@semantic-release/github"
    #         ]
    #         required_plugins.extend(always_required_plugins)
    #         for plugin in required_plugins:
    #             if plugin not in self.releaserc.get("plugins", []):
    #                 self.releaserc.add_plugin(plugin)      

    # def set_container(self, container: Container):
    #     self.container = container

    # def get_version(self) -> Optional[str]:
    #     """Reads the contents of the NEXT_VERSION file and returns the version.
    #     should be called after running the semantic-release command.
    #     Returns:
    #         str: The version read from the NEXT_VERSION file.
    #     Raises:
    #         FileNotFoundError: If the NEXT_VERSION file is not found.
    #         Exception: If there is an error reading the file."""

    #     try:
    #         with open(self.exec_output_file, "r") as file:
    #             version = file.read().strip()  # Read the file and remove any extra whitespace
    #         return version
    #     except FileNotFoundError:
    #         print(f"Error: {self.exec_output_file} not found.")
    #         return None
    #     except Exception as e:
    #         print(f"Error reading {self.exec_output_file}: {e}")
    #         return None


