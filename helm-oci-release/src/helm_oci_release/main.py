import dagger
from dagger import dag, function, object_type, DefaultPath, Directory, Doc, Secret, Container
from typing import Annotated
from pathlib import Path

HELM_IMAGE = "alpine/helm:3.12.0"
OCI_REGISTRY_URL = "oci://ghcr.io"

@object_type
class HelmOciRelease:

    @function
    async def run(self,
            source: Annotated[Directory, Doc("Source directory"), DefaultPath(".")], # source directory
            github_token: Annotated[Secret, Doc("Github Token")],
            username: Annotated[str, Doc("Github Username")] = "local",  # GitHub username
            organization: Annotated[str, Doc("Organization Name")] = "bcit-ltc",  # Organization name
            app_name: Annotated[str, Doc("Application Name")] = "SomeApp",  # Application name
            helm_directory_path: Annotated[str, Doc("Helm Chart Directory Path")] = ".",  # Helm chart directory path
            chart_version: Annotated[str, Doc("Chart Version")] = "0.1.0",  # Chart version
            app_version: Annotated[str, Doc("Application Version")] = "0.1.0",  # Application version
            ) -> str:

        self.github_token = github_token
        self.username = username
        self.organization = organization
        self.app_name = app_name
        self.chart_version = chart_version
        self.app_version = app_version

        try:
            container = await self.prepare_base_container()
            container = await self.add_source_directory(container, source)
            # container = await self.set_workdir(container, app_name)
            container = await self.set_helm_workdir(container, helm_directory_path)
            container = await self.add_ghcr_password_secret(container, github_token)
            container = await self.helm_login(container, organization)
            container = await self.helm_list_contents(container)
            container = await self.helm_package(container)
            container = await self.helm_list_contents(container)
            container = await self.helm_push(container, f"{app_name}-{chart_version}", f"{OCI_REGISTRY_URL}/{organization}/oci")

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
        return await container.with_directory(self.app_name, source)

    # async def set_workdir(self, container: Container, path: str) -> Container:
    #     """
    #     Sets working directory.
    #     """
    #     return await container.with_workdir(path)
    
    async def set_helm_workdir(self, container: Container, helm_directory_path: str) -> Container:
        """ Sets the Helm chart working directory.
        """
        defaultpath = Path("/apps")
        workdir = Path(f"./{self.app_name}")
        helm_directory_path = Path(helm_directory_path)
        temp_path = defaultpath /workdir / helm_directory_path
        final_path = str(temp_path)
        print(f"[DEBUG] Setting Helm workdir to: {final_path}")
        return await container.with_workdir(final_path)

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

    async def helm_package(self, container: Container) -> Container:
        """
        Packages the Helm chart.
        """
        return await container.with_exec(["helm", "package", ".", "--version", self.chart_version, "--app-version", self.app_version])

    async def helm_list_contents(self, container: Container) -> Container:
        """
        Lists contents for debugging.
        """
        return await container.with_exec(["pwd"]).with_exec(["ls", "-la"])

    async def helm_push(self, container: Container, app_version: str, repo_url: str) -> Container:
        """
        Pushes the Helm chart to the registry.
        """
        return await container.with_exec([
            "helm", "push", f"{app_version}.tgz", repo_url
    ])

   