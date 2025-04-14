import json
from typing import Annotated
from datetime import datetime

from dagger import dag, function, object_type, Directory, DefaultPath, Doc, Container, QueryError


@object_type
class DetermineTag:
    """Object type for determining the CI environment"""

    async def _load_json_file(self, container: Container, file_name: str) -> dict:
        """Load and parse the environment map JSON file"""
        container = await container.with_exec(["cat", "/usr/share/nginx/html/" + file_name])
        map_str = (await container.stdout()).strip()
        try:
            json_object = json.loads(map_str)
        except json.JSONDecodeError as e:
            raise QueryError(f"Failed to parse JSON: {e}")
        if not isinstance(json_object, dict):
            raise QueryError("Environment map is not a valid JSON object")
        return json_object


    async def _get_commit_hash(self, container: Container, type: str = "short") -> str:
        """Retrieve the commit hash"""
        if type == "short":
            container = await container.with_exec(["git", "rev-parse", "--short", "HEAD"])
        elif type == "long":
            container = await container.with_exec(["git", "rev-parse", "HEAD"])
        
        return (await container.stdout()).strip()

    
    @function
    async def createtag(
        self,
        source: Annotated[Directory, DefaultPath("./"), Doc("Source directory containing the project files")],
        env: Annotated[str, Doc("Environment to tag the image with")],
        tag: Annotated[str, Doc("Version tag for the image")],
        hashtype: Annotated[str, Doc("Type of hash to use (short or long)")] = "short",
        tagmapfile: Annotated[str | None, Doc("Name of the JSON file containing the tag map")] = "tag_map.json",
        tagmapstring: Annotated[str | None, Doc("JSON string containing the tag map")] = None,
    ) -> str:
        """Create a tag for the image based on the environment and customizable rules"""
        # Get the current date and time
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        current_timestamp = now.strftime(current_date + "%s")
    
        # Get the commit hash
        git_container = await (
            dag.container()
            .from_("alpine/git:2.47.2")
            .with_directory("/usr/share/nginx/html/.git", source.directory(".git"))
            .with_workdir("/usr/share/nginx/html")
        )
        commit_hash = await self._get_commit_hash(git_container, hashtype)
    
        # Load the tag map
        if tagmapstring:
            try:
                tag_map = json.loads(tagmapstring)
            except json.JSONDecodeError as e:
                raise QueryError(f"Failed to parse JSON: {e}")
            if not isinstance(tag_map, dict):
                raise QueryError("Tag map is not a valid JSON object")
        elif tagmapfile:
            git_container = await git_container.with_file(tagmapfile, source.file(tagmapfile))
            tag_map = await self._load_json_file(git_container, tagmapfile)
        else:
            raise QueryError("No tag map provided")
    
        # Determine the tags based on the environment and tag map
        if env not in tag_map:
            raise QueryError(f"Environment '{env}' not found in tag map")
    
        env_data = tag_map[env]
        tags = []
        for rule in env_data.get("rules", []):
            tag_format = rule.get("format", "")
            tags.append(tag_format.format(
                tag=tag,
                date=current_date,
                timestamp=current_timestamp,
                commit_hash=commit_hash
            ))
    
        # Join tags with commas
        return ",".join(tags)