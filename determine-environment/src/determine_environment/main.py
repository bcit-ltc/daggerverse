import json
from typing import Annotated
from dagger import dag, function, object_type, Directory, DefaultPath, Doc, Container, QueryError


@object_type
class DetermineEnvironment:
    """Object type for determining the CI environment"""

    git_container = (
        dag.container()
        .from_("alpine/git:2.47.2")
        .with_workdir("/usr/share/nginx/html")
    )

    async def _get_current_branch(self, container: Container) -> str:
        """Retrieve the current branch name"""
        container = await container.with_exec(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        return (await container.stdout()).strip()

    async def _get_last_commit_message(self, container: Container) -> str:
        """Retrieve the last commit message"""
        container = await container.with_exec(["git", "log", "-1", "--pretty=%B"])
        return (await container.stdout()).strip()


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

    async def _get_commit_hash(self, container: Container, type: str = "short") -> str:
        """Retrieve the commit hash"""
        if type == "short":
            container = await container.with_exec(["git", "rev-parse", "--short", "HEAD"])
        elif type == "long":
            container = await container.with_exec(["git", "rev-parse", "HEAD"])
        
        return (await container.stdout()).strip()

    @function
    async def determineenvironment(
        self,
        source: Annotated[Directory, DefaultPath("./"), Doc("Source directory containing the project files")],
        branch: Annotated[str | None, Doc("Branch name to check for the environment")],
        mapfile: Annotated[str, Doc("Name of the JSON file containing the environment map")] = "env_map.json",
        mapstring: Annotated[str | None, Doc("JSON string containing the environment map")] = None,
        islocal: Annotated[bool, Doc("Whether to run the command locally or in a container")] = False,
    ) -> str:
        """Determine the environment of the project"""
        
        if islocal:
            return "local"
        
        git_container = await (
            self.git_container
            .with_directory("/usr/share/nginx/html/.git", source.directory(".git"))
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
                file_content = await source.file(mapfile).contents()
                env_map = json.loads(file_content)
            else:
                # error if no mapfile is provided
                raise QueryError("No mapfile provided")
            

        return await self._determine_environment(env_map, current_branch, last_commit_message)
    
