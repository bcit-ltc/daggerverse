import dagger
from dagger import dag, function, object_type, Container, DefaultPath, Directory, Secret, Doc, Enum, EnvVariable, enum_type
from typing import Annotated
# import asyncio
import json

@enum_type
class Environment(Enum):
    STABLE = "stable"
    REVIEW = "review"
    LATEST = "latest"
    LOCAL = "local"
    NONE = "none"
    
MAIN_BRANCH = "main"

@object_type
class PipelineManager:
    environment = Environment.NONE
    semantic_release_result = None

    @function
    async def run(self,
                source: Annotated[Directory, Doc("Source directory"), DefaultPath(".")], # source directory
                github_token: Annotated[Secret, Doc("Github Token")] | None,
                username: Annotated[str, Doc("Github Username")] | None,  # GitHub username
                branch: Annotated[str, Doc("Current Branch")] | None,  # Current branch
                commit_hash: Annotated[str, Doc("Current Commit Hash")] | None,  # Current commit hash
                  ) -> str:
        
        # Set function arguments as class variables
        self.source = source
        self.github_token = github_token
        self.username = username
        self.branch = branch
        self.commit_hash = commit_hash
        
        self.environment = await self._determine_environment()


            
        return self.environment
    
    @function
    async def _determine_environment(self) -> str:
        """
        Determine the environment based on the current branch and semantic release output.
        """

        # Check for GitHub token
        if self.github_token is None:
            self.environment = Environment.LOCAL
        else:
            if self.branch == MAIN_BRANCH:
                # semantic_release = await self.semantic_release()
                semantic_release_result = '{ "next_release": null, "last_release": "1.0.1"}'

                # Convert JSON String to Python
                semantic_release_result = json.loads(semantic_release_result)
                print(semantic_release_result['next_release'])

                if semantic_release_result['next_release']:
                    environment = Environment.STABLE
                else:
                    environment = Environment.LATEST
            else:
                environment = Environment.REVIEW

        print(self.branch)
        
        return self.environment
    
    
    # old code from `create-tag` module
    #
    # @function
    # async def createtag(
    #     self,
    #     source: Annotated[Directory, DefaultPath("./"), Doc("Source directory containing the project files")],
    #     env: Annotated[str, Doc("Environment to tag the image with")],
    #     version: Annotated[str, Doc("Version tag for the image")] = "",
    #     commithash: Annotated[str, Doc("Commit hash to use for the tag")] = "",
    #     tagmapstring: Annotated[str | None, Doc("JSON string containing the tag map")] = None,
    #     tagmapfile: Annotated[str | None, Doc("Name of the JSON file containing the tag map")] = "tag_map.json",
    # ) -> str:
    #     """Create a tag for the image based on the environment and customizable rules"""

    #     # Get the current date and time
    #     now = datetime.now()
    #     current_date = now.strftime("%Y-%m-%d")
    #     current_timestamp = now.strftime(current_date + "%s")
    
    
    #     # Load the tag map
    #     if tagmapstring:
    #         try:
    #             tag_map = json.loads(tagmapstring)
    #         except json.JSONDecodeError as e:
    #             raise QueryError(f"Failed to parse JSON: {e}")
    #         if not isinstance(tag_map, dict):
    #             raise QueryError("Tag map is not a valid JSON object")
    #     elif tagmapfile:
    #         file_content = await source.file(tagmapfile).contents()
    #         tag_map = json.loads(file_content)
    #     else:
    #         raise QueryError("No tag map provided")
    
    #     # Determine the tags based on the environment and tag map
    #     if env not in tag_map:
    #         raise QueryError(f"Environment '{env}' not found in tag map")
    
    #     env_data = tag_map[env]
    #     tags = []
    #     for rule in env_data.get("rules", []):
    #         tag_format = rule.get("format", "")
    #         tags.append(tag_format.format(
    #             env=env,
    #             version=version,
    #             date=current_date,
    #             timestamp=current_timestamp,
    #             commit_hash=commithash
    #         ))
    
    #     # Join tags with commas
    #     return ",".join(tags)    
    