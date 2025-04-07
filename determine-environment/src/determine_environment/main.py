from typing import Annotated
from dagger import dag, field, function, object_type, Directory, Secret, DefaultPath, Doc, Container, QueryError


def init() -> Container:
    """Initialize the container"""
    return (
        dag.container()
        .from_("alpine/git:2.47.2")
    )

@object_type
class DetermineEnvironment:
    """Object type for determining the CI environment"""
    git_container : Container = field(default=init)


    @function
    async def determine_environment(
        self,
    ) -> str:
        """Determine the environment of the project"""
        self.git_container = await (
            self.git_container
            .with_workdir("/usr/share/nginx/html")
            .with_exec(["git", "config", "--get", "remote.origin.url"])

        )
        git_url = (await self.git_container.stdout()).strip()
        return git_url