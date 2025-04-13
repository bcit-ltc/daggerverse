from typing import Any, Dict, List, Optional, Union
import json

class ReleaseRC:
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        # if not isinstance(config, dict):
        #     raise ValueError("ReleaseRC requires a dictionary as config.")
        # self.data: Dict[str, Any] = config

        # Ensure essential keys are initialized properly
        self.data = config if config else {}

        self.data.setdefault("branches", [])
        # self.data.setdefault("repositoryUrl", None)
        self.data.setdefault("dryRun", False)
        self.data.setdefault("ci", False)
        self.data.setdefault("debug", False)
        self.data.setdefault("plugins", [])
        # self.data.setdefault("tagFormat", "${version}")

    def add_branch(self, branch: str) -> None:
        if branch not in self.data["branches"]:
            self.data["branches"].append(branch)

    def add_plugin(self, plugin: Union[str, List[Any]]) -> None:
        if plugin not in self.data["plugins"]:
            self.data["plugins"].append(plugin)

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value

    def to_dict(self) -> Dict[str, Any]:
        return self.data
    
    def to_string(self) -> str:
        """Convert the ReleaseRC object to a string representation."""
        return (json.dumps(self.data, indent=2))

    def set_dry_run(self, value: bool):
        """Set the dryRun field."""
        self.set("dryRun", value)

    def set_ci(self, value: bool):
        """Set the ci field."""
        self.set("ci", value)

    def set_debug(self, value: bool):
        """Set the debug field."""
        self.set("debug", value)
    
    # def set_repository_url(self, url: str):
    #     """Set the repositoryUrl field."""
    #     self.set("repositoryUrl", url)

    def __repr__(self):
        return f"<ReleaseRC keys={list(self.data.keys())}>"
