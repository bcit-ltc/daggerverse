import json
from typing import Annotated, Any
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
    git_container: Container = field(default=init)

    async def _get_current_branch(self, container: Container) -> str:
        """Retrieve the current branch name"""
        container = await container.with_exec(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        return (await container.stdout()).strip()

    async def _get_last_commit_message(self, container: Container) -> str:
        """Retrieve the last commit message"""
        container = await container.with_exec(["git", "log", "-1", "--pretty=%B"])
        return (await container.stdout()).strip()

    async def _load_env_map(self, container: Container, mapfile: str) -> dict:
        """Load and parse the environment map JSON file"""
        container = await container.with_exec(["cat", mapfile])
        map_str = (await container.stdout()).strip()
        try:
            env_map = json.loads(map_str)
        except json.JSONDecodeError as e:
            raise QueryError(f"Failed to parse JSON: {e}")
        if not isinstance(env_map, dict):
            raise QueryError("Environment map is not a valid JSON object")
        return env_map

    async def _determine_environment(
        self, env_map: dict, branch: str, last_commit_message: str
    ) -> str:
        """Determine the environment based on the branch and commit message"""
        if branch in env_map["branches"]:
            branch_data = env_map["branches"][branch]
            for prefix in branch_data["prefixes"]:
                if last_commit_message.startswith(prefix):
                    return branch_data[prefix]
            return branch_data["default"]
        return env_map["default"]

    @function
    async def getenv(
        self,
        source: Annotated[Directory, DefaultPath("./"), Doc("Source directory containing the project files")],
        branch: Annotated[str | None, Doc("Branch name to check for the environment")],
        mapfile: Annotated[str, Doc("Name of the JSON file containing the environment map")] = "env_map.json",
    ) -> str:
        """Determine the environment of the project"""
        temp_git_container = await (
            self.git_container
            .with_directory("/usr/share/nginx/html/.git", source.directory(".git"))
            .with_workdir("/usr/share/nginx/html")
            .with_file(mapfile, source.file(mapfile))
        )

        current_branch = branch or await self._get_current_branch(temp_git_container)
        last_commit_message = await self._get_last_commit_message(temp_git_container)
        env_map = await self._load_env_map(temp_git_container, mapfile)

        return await self._determine_environment(env_map, current_branch, last_commit_message)