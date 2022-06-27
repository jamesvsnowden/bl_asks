
from bpy.props import StringProperty
from uuid import uuid4
from .system_struct import SystemStruct

class SystemObject(SystemStruct):

    SYSTEM_PATH = ""

    name: StringProperty(
        name="Name",
        description="System object identity (read-only)",
        get=lambda self: self.get("name", ""),
        set=lambda self, _: self.system.log.error(f'{type(self)}.name is read-only'),
        options={'HIDDEN'}
        )

    system_path: StringProperty(
        name="System Path",
        description="",
        get=lambda self: self.get("system_path", ""),
        options={'HIDDEN'}
        )

    def __init__(self) -> None:
        self["name"] = f'ASKS_{uuid4()}'
        self["system_path"] = f'{self.SYSTEM_PATH}["{self.name}"]'
