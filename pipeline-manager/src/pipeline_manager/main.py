import dagger
from dagger import dag, function, object_type, Container, DefaultPath, Directory, Secret, Doc, Enum, EnvVariable, enum_type
from typing import Annotated
# import asyncio
import json
from datetime import datetime

# Constants
MAIN_BRANCH = "main"

@enum_type
class Environment(Enum):
    STABLE          = "stable"        # latest version ( main branch commit includes semver format)
    LATEST          = "latest"        # latest version ( main branch commit without semver format)
    REVIEW          = "review"        # review version ( not on main branch )
    LOCAL           = "local"         # local environment
    LATEST_STABLE   = "latest_stable" # could be either latest or stable (transition state)
    CI              = "ci"            # token found    (transition state)
    NONE            = "none"          # undefined      (transition state)


@object_type
class PipelineManager:
    environment = Environment.NONE
    semantic_release_result = None
    version = None
    tags = None

    @function
    async def run(self,
                source: Annotated[Directory, Doc("Source directory"), DefaultPath(".")], # source directory
                github_token: Annotated[Secret, Doc("Github Token")] | None,
                username: Annotated[str, Doc("Github Username")] | None,  # GitHub username
                branch: Annotated[str, Doc("Current Branch")] | None,  # Current branch
                commit_hash: Annotated[str, Doc("Current Commit Hash")] | None,  # Current commit hash
                  ) -> str:
        print(dir(dag))
        # Set function arguments as class variables
        self.source = source
        self.github_token = github_token
        self.username = username
        self.branch = branch
        self.commit_hash = commit_hash
        
        # Run unit tests
        await self.unit_tests()

        # Determine if ci environment by checking for GitHub token
        await self._check_if_ci()

        # Build the Docker image
        await self.build_docker_image()
        
        # Determine the environment
        await self._check_if_review()

        # Run semantic release
        await self.run_semantic_release()
    
        # Create tag
        await self._create_tag()


        return self.environment

    @function
    async def _check_if_ci(self) -> None:
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
            print("Running on Main branch")
            self.environment = Environment.LATEST_STABLE
        else:
            print("Running on Review branch")
            self.environment = Environment.REVIEW
    
    @function
    async def run_semantic_release(self) -> str:
        """
        Run semantic release if the environment is either latest or stable
        """
        if self.environment == Environment.LATEST_STABLE:
            print("Running semantic release...")
            print(dag.semantic_release())
            self.semantic_release_result = await dag.semantic_release().semanticrelease(
                source=self.source,
                github_token=self.github_token,
                username=self.username
            )
            print("Semantic Release Result: ", self.semantic_release_result)
            self.semantic_release_result = json.loads(self.semantic_release_result)
            print("Next Release: ", self.semantic_release_result['next_release'])
            if self.semantic_release_result['next_release']:
                self.environment = Environment.STABLE
                self.version = self.semantic_release_result['next_release']
            else:
                self.environment = Environment.LATEST
                self.version = self.semantic_release_result['last_release']
        else:
            print("Not running semantic release for this environment")
            self.semantic_release_result = None

    @function
    async def _create_tag(self) -> None:
        """
        Create a tag for the release
        """
        # Get the current date and time
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        current_timestamp = now.strftime(current_date + "%s")

        if self.environment == Environment.STABLE:
            self.tags = f"{self.version},{Environment.STABLE},{Environment.LATEST}"
            print("Tags created for STABLE: ", self.tags)
        elif self.environment == Environment.LATEST:
            self.tags = f"{self.version}-{self.commit_hash}.{current_timestamp},{Environment.LATEST}"
            print("Tags created for LATEST: ", self.tags)
        elif self.environment == Environment.REVIEW:
            self.tags = f"review-{self.branch}-{self.commit_hash}.{current_timestamp}"
            print("Tag created for REVIEW: ", self.tags)
        else:
            print("No tag created for this environment")
            

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