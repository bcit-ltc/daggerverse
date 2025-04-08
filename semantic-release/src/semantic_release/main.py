from typing import Annotated, Self
from dagger import Container, dag, Directory, Doc, field, function, object_type, Secret, DefaultPath

from .releaserc import ReleaseRC
from enum import Enum
from typing import Optional
import json

class ReleaseMode(Enum):
    LOCAL = "local"
    CI = "ci"


@object_type
class SemanticRelease:
    def __init__(
        self,
        github_token: Optional[str] = None,
        source: Optional[str] = None,
        branch: Optional[str] = None,
        username: Optional[str] = None,
        ) -> None:
        self.mode = ReleaseMode.CI if github_token else ReleaseMode.LOCAL

        if self.mode == ReleaseMode.CI:
            if not all([source, branch, username]):
                raise ValueError("CI mode requires: source, branch, username")

        self.github_token = github_token
        self.source = source
        self.branch = branch
        self.username = username
        self.releaserc = ReleaseRC() # Initialize with an empty config
        self.container: Optional[Container] = None
        self.exec_output_file = "NEXT_VERSION"  # Store the exec output file variable

        self._set_required_plugins() # Set required plugins based on the mode CI or LOCAL
        self.releaserc.set("branches", [branch])
        self.releaserc.set("dryRun", False)
        self.releaserc.set("ci", True if self.mode == ReleaseMode.CI else False)
        self.releaserc.set("debug", True)
        self.releaserc.set("tagFormat", "${{version}}")

        # print(self.releaserc.to_dict())  # Debugging line
        print(json.dumps(self.releaserc.to_dict(), indent=2))  # Debugging line

        