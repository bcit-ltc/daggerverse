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
            container = await self.prepare_base_container()
            container = await self.add_source_directory(container, source)
            container = await self.set_workdir(container, f"{WORKDIR}/{appname}")
            container = await self.add_ghcr_password_secret(container, github_token)
            container = await self.helm_login(container, username)
            container = await self.helm_package(container)
            container = await self.helm_list_contents(container)
            container = await self.helm_push(container, f"{appname}-{chart_version}", f"oci://ghcr.io/bcit-ltc/{appname}/oci")

            # await self._prepare_helm_container(source)
            # await self._setup_helm_directory(source)
        except Exception as e:
            print(f"[ERROR] Pipeline failed: {e}")

        return None

    async def prepare_base_container(self) -> Container:
        """
        Pulls the Helm base image.
        """
        return await dag.container().from_(HELM_IMAGE)

    async def add_source_directory(self, container: Container, source: Directory) -> Container:
        """
        Mounts the local source code.
        """
        return await container.with_directory(WORKDIR, source)

    async def set_workdir(self, container: Container, path: str) -> Container:
        """
        Sets working directory.
        """
        return await container.with_workdir(path)

    async def add_ghcr_password_secret(self, container: Container, github_token: Secret) -> Container:
        """
        Adds the GHCR secret.
        """
        return await container.with_secret_variable("GHCR_PASSWORD", github_token)

    async def helm_login(self, container: Container, username: str) -> Container:
        """
        Runs helm registry login command.
        """
        login_cmd = (
            f'echo "$GHCR_PASSWORD" | helm registry login ghcr.io '
            f'--username bcit-ltc --password-stdin'
        )
        return await container.with_exec(["sh", "-c", login_cmd])

    async def helm_package(self, container: Container) -> Container:
        """
        Packages the Helm chart.
        """
        # Use built-in shell commands available in Alpine (sh, echo, cat, etc.)
        # Use 'sh' to update Chart.yaml without sed
        await container.with_exec([
            "sh", "-c",
            f"echo 'name: {self.appname}' > Chart.yaml.tmp && grep -v '^name:' Chart.yaml >> Chart.yaml.tmp && mv Chart.yaml.tmp Chart.yaml && cat Chart.yaml"
        ])

        await container.with_exec(
            ["touch", "somefile.yaml"]
        )

        return await container.with_exec(["helm", "package", ".", "--version", self.chart_version, "--app-version", self.app_version])

    async def helm_list_contents(self, container: Container) -> Container:
        """
        Lists contents for debugging.
        """
        return await container.with_exec(["ls", "-la"])

    async def helm_push(self, container: Container, app_version: str, repo_url: str) -> Container:
        """
        Pushes the Helm chart to the registry.
        """
        return await container.with_exec([
            "helm", "push", f"{app_version}.tgz", repo_url
    ])

    # async def _setup_helm_directory(self, source: Directory) -> Directory:
    #     """
    #     Set up the Helm directory structure in the container.
    #     """
        
    #     result = await self.helm_container.with_directory(
    #         WORKDIR, source
    #     ).with_workdir(WORKDIR
    #     # ).with_env_variable("GHCR_USERNAME", self.username
    #     ).with_secret_variable("GHCR_PASSWORD", self.github_token
    #     ).with_exec([
    #         "sh", "-c", 'echo "$GHCR_PASSWORD" | helm registry login ghcr.io --username bcit-ltc --password-stdin'
    #     ]
    #     ).with_workdir(WORKDIR + "/" + self.appname
    #     ).with_exec(
    #         ["helm", "package", "."]
    #     ).with_exec(
    #         ["ls", "-la"]
    #     ).with_exec(
    #         ["helm", "push", f"oci-1.0.0.tgz", f"oci://ghcr.io/bcit-ltc/oci"]
    #     )

    #     return await result.stdout()

    # async def _prepare_helm_container(self, source: Directory) -> Container:
    #     self.helm_container =  await dag.container().from_(HELM_IMAGE)
    #     return self.helm_container
    
    # async def _run_helm_command(self, command: str, args: list[str]) -> str:
    #     """
    #     Run a Helm command with the given arguments.
    #     """
    #     container = await self._prepare_helm_container()
    #     result = await container.with_exec(["helm", command] + args).stdout()
    #     return result

    # async def _helm_login(self, source: Directory) -> Container:
    #     self.helm_container =  await dag.container().from_(HELM_IMAGE)
    #     return self.helm_container
