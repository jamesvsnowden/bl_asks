
from bpy.props import StringProperty
from uuid import uuid4
from .system_struct import SystemStruct

class SystemObject(SystemStruct):

    name: StringProperty(
        name="Name",
        description="System object identity (read-only)",
        get=lambda self: self.get("name", ""),
        set=lambda self, _: self.system.log.error(f'{type(self)}.name is read-only'),
        options={'HIDDEN'}
        )

    path: StringProperty(
        name="System Path",
        description="",
        get=lambda self: self.get("path", ""),
        options={'HIDDEN'}
        )
