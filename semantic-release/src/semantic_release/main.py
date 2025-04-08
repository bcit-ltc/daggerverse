from typing import Annotated, Self
from dagger import Container, dag, Directory, Doc, field, function, object_type, Secret, DefaultPath

@object_type
class SemanticRelease:
    # github_token: Annotated[Secret, Doc("GitHub Token")]
    # source: Annotated[Directory, DefaultPath("./")]
    # branch: Annotated[str, Doc("GitHub branch name")]
    # username: Annotated[str, Doc("GitHub username")]
    # releaserc: Annotated[str, Doc("Release configuration json")]
    # container: Annotated[
    #     Container,
    #     Doc("Container to run commands in"),
    # ] = field()
    # @classmethod
    # async def init(
    #     cls,
    #     token: Annotated[Secret, Doc("The Github Token to use")],
    #     source: Annotated[Directory, DefaultPath("./"), Doc("The source directory")],
    #     branch: Annotated[str, Doc("The GitHub branch name")],
    #     username: Annotated[str, Doc("The GitHub username")]
    #     ) -> Self:
    #     self = cls(github_token = token, \
    #                source = source, \
    #                branch = branch, \
    #                 username = username)
    #     return cls(
    #         container=(
    #             dag.container()
    #             .from_("ghcr.io/bcit-ltc/semantic-release:latest")
    #         )
    #     )

    @function
    async def version(self) -> str:
        """Returns the string argument provided"""
        return await(
            dag.container()
            .from_("ghcr.io/bcit-ltc/semantic-release:latest")
            .with_workdir("/app") 
            .with_new_file(
            "/app/hello.txt",
            contents=f"""Helloo World""",
            ).with_exec(["cat", "/app/hello.txt"])
            .stdout()
        )
        
    @function
    def env(self) -> Container:
        """Returns a container with the necessary environment for git and gh"""
        return (
            dag.container() \
            .from_("ghcr.io/bcit-ltc/semantic-release:latest") \
            .with_workdir("/app") \
            .with_directory("/app", self.source) \
            .with_secret_variable("GITHUB_TOKEN", self.github_token) \
            .with_exec(["cp", "/usr/src/app/.releaserc", "/app/.releaserc"]) \
            .with_exec(["cat", "/app/.releaserc"]) \
            .with_exec(["npx", "semantic-release", "--branches", self.branch]) \
            .with_exec(["ls", "-la"]) \
            .with_exec(["cat", "NEXT_VERSION"]) \
            .stdout()
        )