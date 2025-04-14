import json
from typing import Annotated
from dagger import dag, function, object_type, Directory, DefaultPath, Doc, Container, QueryError


@object_type
class DetermineEnvironment:
    """Object type for determining the CI environment"""

    async def _get_current_branch(self, container: Container) -> str:
        """Retrieve the current branch name"""
        container = await container.with_exec(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        return (await container.stdout()).strip()

    async def _get_last_commit_message(self, container: Container) -> str:
        """Retrieve the last commit message"""
        container = await container.with_exec(["git", "log", "-1", "--pretty=%B"])
        return (await container.stdout()).strip()

    async def _load_json_file(self, container: Container, file_name: str) -> dict:
        """Load and parse the environment map JSON file"""
        container = await container.with_exec(["cat", "/usr/share/nginx/html/" + file_name])
        map_str = (await container.stdout()).strip()
        try:
            json_object = json.loads(map_str)
        except json.JSONDecodeError as e:
            raise QueryError(f"Failed to parse JSON: {e}")
        if not isinstance(json_object, dict):
            raise QueryError("Environment map is not a valid JSON object")
        return json_object

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
        mapstring: Annotated[str | None, Doc("JSON string containing the environment map")] = None,
    ) -> str:
        """Determine the environment of the project"""
        
        git_container = await (
            dag.container()
            .from_("alpine/git:2.47.2")
            .with_directory("/usr/share/nginx/html/.git", source.directory(".git"))
            .with_workdir("/usr/share/nginx/html")
        )
        
        current_branch = branch or await self._get_current_branch(git_container)
        last_commit_message = await self._get_last_commit_message(git_container)

        if mapstring:
            try:
                env_map = json.loads(mapstring)
            except json.JSONDecodeError as e:
                raise QueryError(f"Failed to parse JSON: {e}")
            if not isinstance(env_map, dict):
                raise QueryError("Environment map is not a valid JSON object")
        else:
            if mapfile:
                git_container = await git_container.with_file(mapfile, source.file(mapfile))
                env_map = await self._load_json_file(git_container, mapfile)
            else:
                # error if no mapfile is provided
                raise QueryError("No mapfile provided")
            

        return await self._determine_environment(env_map, current_branch, last_commit_message)