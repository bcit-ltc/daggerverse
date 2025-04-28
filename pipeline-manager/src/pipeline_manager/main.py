import dagger
from dagger import dag, function, object_type, Container, DefaultPath, Directory, Secret, Doc, Enum, EnvVariable, enum_type
from typing import Annotated
# import asyncio
import json

@enum_type
class Environment(Enum):
    STABLE = "stable"   # latest version ( main branch commit includes semver format)
    LATEST = "latest"   # latest version ( main branch commit without semver format)
    REVIEW = "review"   # review version ( not on main branch )
    LATEST_STABLE = "latest-stable" # could be either latest or stable (transition state)
    LOCAL = "local"     # local environment
    CI = "ci"           # token found
    NONE = "none"       # undefined
    
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
        
        # Run unit tests
        await self.unit_tests()

        # Build the Docker image
        await self.build_docker_image()
        
        # Determine the environment 
        await self._determine_environment()

        # Run semantic release
        await self.run_semantic_release()
    
        return self.environment
    
    @function
    async def _determine_environment(self) -> str:
        """
        Determine the environment
        """

        # Check if Local or on CI
        if self.github_token is None:
            self.environment = Environment.LOCAL
        else:
            self.environment = Environment.CI
        
        if self.branch == MAIN_BRANCH:
            self.environment = Environment.LATEST_STABLE

        # # Check for GitHub token
        # if self.github_token is None:
        #     self.environment = Environment.LOCAL
        # else:
        #     if self.branch == MAIN_BRANCH:
        #         # semantic_release = await self.semantic_release()
        #         semantic_release_result = '{ "next_release": null, "last_release": "1.0.1"}'

        #         # Convert JSON String to Python
        #         semantic_release_result = json.loads(semantic_release_result)
        #         print(semantic_release_result['next_release'])

        #         if semantic_release_result['next_release']:
        #             environment = Environment.STABLE
        #         else:
        #             environment = Environment.LATEST
        #     else:
        #         environment = Environment.REVIEW

        # print(self.branch)
        
        # return self.environment
    
    @function
    async def run_semantic_release(self) -> str:
        """
        Run semantic release
        """
        if self.environment == Environment.LATEST_STABLE:
            # Run semantic release logic
            self.semantic_release_result = await self._semantic_release()
            print("Semantic Release Result: ", self.semantic_release_result)
    

    @function
    async def unit_tests(self) -> None:
        """
        Run unit tests by calling the test function in the source directory.
        This function is a placeholder and should be replaced with actual test logic.
        """
        print("Running unit tests...")
        # Add your unit test logic here
        # For example, you can use pytest to run tests in the source directory
        # await self.source.run("pytest", args=["-v", "--tb=short"])