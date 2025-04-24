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
                # semantic_release_result = '{ "next_release": null, "last_release": "1.0.1"}'

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