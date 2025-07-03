import dagger
from dagger import dag, function, object_type, DefaultPath, Directory, Doc
from typing import Annotated

@object_type
class HelmOciRelease:


    @function
    async def run(self,
            source: Annotated[Directory, Doc("Source directory"), DefaultPath(".")], # source directory
            ) -> str:

        return "Helm OCI Release"