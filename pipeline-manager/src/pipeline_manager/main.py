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

        # Determine if ci environment
        await self._check_ci()

        # Build the Docker image
        await self.build_docker_image()
        
        # Determine the environment
        await self._check_if_review()

        # Run semantic release
        await self.run_semantic_release()
    
        return self.environment

    @function
    async def _check_ci(self) -> None:
        """
        Check if the environment is CI or local
        """
        # Check if GitHub token is provided
        if self.github_token is not None:
            print("Running in CI environment")
            self.environment = Environment.CI
        else:
            print("Running locally")
            self.environment = Environment.LOCAL

    @function
    async def _check_if_review(self) -> str:
        """
        Determine if running on a review branch or main branch
        """
        if self.branch == MAIN_BRANCH:
            self.environment = Environment.LATEST_STABLE
        else:
            self.environment = Environment.REVIEW
    
    @function
    async def run_semantic_release(self) -> str:
        """
        Run semantic release if the environment is either latest or stable
        """
        if self.environment == Environment.LATEST_STABLE:
            # Run semantic release logic
            self.semantic_release_result = await self._semantic_release()
            print("Semantic Release Result: ", self.semantic_release_result)
        else:
            print("Not running semantic release for this environment")
            self.semantic_release_result = None

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
    
    async def build_docker_image(self) -> None:
        """
        Build the Docker image using the source directory.
        This function is a placeholder and should be replaced with actual build logic.
        """
        print("Building Docker image...")
        # Add your Docker build logic here
        # For example, you can use Docker CLI to build the image
        # await self.source.run("docker", args=["build", "-t", "my-image", "."])