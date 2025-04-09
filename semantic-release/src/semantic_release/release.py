from .releaserc import ReleaseRC
from enum import Enum
from typing import Optional
import json
from dagger import Container, dag, Directory, Doc, field, function, object_type, Secret, DefaultPath


class ReleaseMode(Enum):
    LOCAL = "local"
    CI = "ci"



# class Release:
#     # @function
#     def __init__(
#         self,
