import json
from typing import Annotated
from datetime import datetime
from dagger import function, object_type, Directory, DefaultPath, Doc, QueryError


@object_type
class CreateTag:
    """Object type for determining the CI environment"""
    
    @function
    async def createtag(
        self,
        source: Annotated[Directory, DefaultPath("./"), Doc("Source directory containing the project files")],
        env: Annotated[str, Doc("Environment to tag the image with")],
        version: Annotated[str, Doc("Version tag for the image")] = "",
        commithash: Annotated[str, Doc("Commit hash to use for the tag")] = "",
        tagmapstring: Annotated[str | None, Doc("JSON string containing the tag map")] = None,
        tagmapfile: Annotated[str | None, Doc("Name of the JSON file containing the tag map")] = "tag_map.json",
    ) -> str:
        """Create a tag for the image based on the environment and customizable rules"""

        # Get the current date and time
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        current_timestamp = now.strftime(current_date + "%s")
    
    
        # Load the tag map
        if tagmapstring:
            try:
                tag_map = json.loads(tagmapstring)
            except json.JSONDecodeError as e:
                raise QueryError(f"Failed to parse JSON: {e}")
            if not isinstance(tag_map, dict):
                raise QueryError("Tag map is not a valid JSON object")
        elif tagmapfile:
            file_content = await source.file(tagmapfile).contents()
            tag_map = json.loads(file_content)
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
                env=env,
                version=version,
                date=current_date,
                timestamp=current_timestamp,
                commit_hash=commithash
            ))
    
        # Join tags with commas
        return ",".join(tags)