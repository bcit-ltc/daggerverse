import json
from typing import Annotated
from dagger import dag, function, object_type, Directory, DefaultPath, Doc, Container, QueryError


@object_type
class DetermineEnvironment:
    """Object type for determining the CI environment"""
        
    @function
    async def getenv(
        self,
        commitmessage: Annotated[str, Doc("Source directory containing the project files")],
        branch: Annotated[str, Doc("Branch name to check for the environment")],
        mapstring: Annotated[str, Doc("JSON string containing the environment map")],
    ) -> str:
        """Determine the environment of the project"""
        env_map = json.loads(mapstring)

        """Determine the environment based on the branch and commit message"""
        if branch in env_map["branches"]:
            branch_data = env_map["branches"][branch]
            for prefix in branch_data["prefixes"]:
                if commitmessage.startswith(prefix):
                    return branch_data[prefix]
            return branch_data["default"]
        return env_map["default"]
