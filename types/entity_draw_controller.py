
from typing import TYPE_CHECKING, Callable, Optional
from bpy.types import PropertyGroup
from bpy.props import StringProperty
from .system_struct import SystemStruct
if TYPE_CHECKING:
    from bpy.types import UILayout
    from .entity import Entity


DrawHandler = Callable[['Entity', 'UILayout'], None]


class EntityDrawController(SystemStruct, PropertyGroup):

    entity__internal__: StringProperty(options={'HIDDEN'})
    handle__internal__: StringProperty(options={'HIDDEN'})

    def __call__(self, layout: 'UILayout') -> None:
        entity = self.system.entities.collection__internal__[self.entity__internal__]
        handle = self.handle__internal__
        if handle:
            drawfunc = self.system.draw_funcs__internal__.get(handle)
            if drawfunc:
                drawfunc(layout, entity)
                return
        for component in entity.components:
            if not component.hide:
                component.draw(layout, entity)

    def __eq__(self, handler: DrawHandler) -> bool:
        handle = self.handle__internal__
        return bool(handle) and handle == getattr(handler, 'asks_id', "")

    @property
    def handler(self) -> Optional[DrawHandler]:
        return self.system.draw_funcs__internal__.get(self.handle__internal__)

    @handler.setter
    def handler(self, handler: DrawHandler) -> None:
        handle = getattr(handler, "asks_id", "")
        if not handle or handle not in self.system.draw_funcs__internal__:
            raise ValueError()
        self.handle__internal__ = handle

