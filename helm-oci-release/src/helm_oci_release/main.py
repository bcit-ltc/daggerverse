import dagger
from dagger import dag, function, object_type, DefaultPath, Directory, Doc, Secret, Container
from typing import Annotated

HELM_IMAGE = "alpine/helm:3.12.0"
WORKDIR = "/app"

@object_type
class HelmOciRelease:

    @function
    async def run(self,
            source: Annotated[Directory, Doc("Source directory"), DefaultPath(".")], # source directory
            github_token: Annotated[Secret, Doc("Github Token")],
            username: Annotated[str, Doc("Github Username")] = "local",  # GitHub username
            organization: Annotated[str, Doc("Organization Name")] = "bcit-ltc",  # Organization name
            appname: Annotated[str, Doc("Application Name")] = "SomeApp",  # Application name
            chart_version: Annotated[str, Doc("Chart Version")] = "0.1.0",  # Chart version
            app_version: Annotated[str, Doc("Application Version")] = "0.1.0",  # Application version
            ) -> str:

        self.github_token = github_token
        self.username = username
        self.organization = organization
        self.appname = appname
        self.chart_version = chart_version
        self.app_version = app_version

        try:
            container = await self.prepare_base_container()
            container = await self.add_source_directory(container, source)
            container = await self.set_workdir(container, f"{WORKDIR}/{appname}")
            container = await self.add_ghcr_password_secret(container, github_token)
            container = await self.helm_login(container, organization)
            container = await self.update_chart_name(container)
            container = await self.helm_package(container)
            container = await self.helm_list_contents(container)
            container = await self.helm_push(container, f"{appname}-{chart_version}", f"oci://ghcr.io/{organization}/oci")

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
            f'--username {username} --password-stdin'
        )
        return await container.with_exec(["sh", "-c", login_cmd])

    async def update_chart_name(self, container: Container) -> Container:
        """
        Updates the Chart.yaml file.
        """
        # Use built-in shell commands available in Alpine (sh, echo, cat, etc.)
        # Use 'sh' to update Chart.yaml without sed
        return await container.with_exec([
            "sh", "-c",
            f"echo 'name: {self.appname}' > Chart.yaml.tmp && grep -v '^name:' Chart.yaml >> Chart.yaml.tmp && mv Chart.yaml.tmp Chart.yaml && cat Chart.yaml"
        ])

    async def helm_package(self, container: Container) -> Container:
        """
        Packages the Helm chart.
        """
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

   