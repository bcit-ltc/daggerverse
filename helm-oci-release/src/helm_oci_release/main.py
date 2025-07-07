import dagger
from dagger import dag, function, object_type, DefaultPath, Directory, Doc, Secret, Container
from typing import Annotated

HELM_IMAGE = "alpine/helm:3.12.0"
WORKDIR = "/app"

@object_type
class HelmOciRelease:
    helm_container: Container | None = None  # Container for Helm operations

    @function
    async def run(self,
            source: Annotated[Directory, Doc("Source directory"), DefaultPath(".")], # source directory
            github_token: Annotated[Secret | None, Doc("Github Token")],
            username: Annotated[str, Doc("Github Username")] = "local",  # GitHub username
            appname: Annotated[str, Doc("Application Name")] = "SomeApp",  # Application name
            chart_version: Annotated[str, Doc("Chart Version")] = "0.1.0",  # Chart version
            app_version: Annotated[str, Doc("Application Version")] = "0.1.0",  # Application version
            ) -> str:

        self.github_token = github_token
        self.username = username
        self.appname = appname
        self.chart_version = chart_version
        self.app_version = app_version

        try:
            await self._prepare_helm_container(source)
            await self._setup_helm_directory(source)
        except Exception as e:
            print(f"[ERROR] Pipeline failed: {e}")

        return None

    async def _setup_helm_directory(self, source: Directory) -> Directory:
        """
        Set up the Helm directory structure in the container.
        """
        
        result = await self.helm_container.with_directory(
            WORKDIR, source
        ).with_workdir(WORKDIR
        # ).with_env_variable("GHCR_USERNAME", self.username
        ).with_secret_variable("GHCR_PASSWORD", self.github_token
        ).with_exec([
            "sh", "-c", 'echo "$GHCR_PASSWORD" | helm registry login ghcr.io --username bcit-ltc --password-stdin'
        ]
        ).with_workdir(WORKDIR + "/" + self.appname
        ).with_exec(
            ["helm", "package", "."]
        ).with_exec(
            ["ls", "-la"]
        ).with_exec(
            ["helm", "push", f"oci-1.0.0.tgz", f"oci://ghcr.io/bcit-ltc/oci"]
        )

        return await result.stdout()

    async def _prepare_helm_container(self, source: Directory) -> Container:
        self.helm_container =  await dag.container().from_(HELM_IMAGE)
        return self.helm_container
    
    # async def _run_helm_command(self, command: str, args: list[str]) -> str:
    #     """
    #     Run a Helm command with the given arguments.
    #     """
    #     container = await self._prepare_helm_container()
    #     result = await container.with_exec(["helm", command] + args).stdout()
    #     return result

    async def _helm_login(self, source: Directory) -> Container:
        self.helm_container =  await dag.container().from_(HELM_IMAGE)
        return self.helm_container
