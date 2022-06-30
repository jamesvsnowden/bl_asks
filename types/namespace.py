
from typing import Callable, Type, TYPE_CHECKING
from contextlib import suppress
from uuid import uuid4
import bpy
if TYPE_CHECKING:
    from .component import Component
    from .system import System

_namespaces = {}

class namespace:

    def __new__(self, cls: Type['namespace'], name: str) -> None:
        if name in _namespaces:
            return _namespaces[name]
        

    def __init__(self, asks: Type['System'], name: str) -> None:
        self._asks = asks
        self._name = name
        self._type = None
        self._components = {}
        self._processors = set()
        self._draw_funcs = set()

    def define_component(self, key: str, cls: Type['Component']) -> None:
        try:
            bpy.utils.register_class(cls)
        except ValueError: pass
        self._components[key] = cls

    def define_processor(self, func: Callable) -> None:
        func.asks_ns = self._name
        func.asks_id = str(uuid4())
        self._processors.add(func)

    def define_draw_handler(self, func: Callable) -> None:
        func.asks_ns = self._name
        func.asks_id = str(uuid4())
        self._draw_funcs.add(func)

    def install(self) -> None:
        data = {}
        asks = self._asks
        name = self._name

        for key, cls in self._components.items():
            cls._users = getattr(cls, "_users", 0) + 1
            prop = f'{key}_components'
            asks.components__internal__[f'{name}.{key}'] = prop
            data[prop] = bpy.props.CollectionProperty(type=cls, options={'HIDDEN'})

        for func in self._processors:
            asks.processors__internal__[func.asks_id] = func

        for func in self._draw_funcs:
            asks.draw_funcs__internal__[func.asks_id] = func

        cls = self._type = type(name, (bpy.types.PropertyGroup,), {"__annotations__": data})
        bpy.utils.register_class(cls)
        setattr(bpy.types.Key, name, cls)

    def uninstall(self) -> None:
        asks = self._asks
        name = self._name

        for key, cls in self._components.items():
            prop = f'{key}_components'
            with suppress(KeyError): del asks.components__internal__[prop]
            count = cls._users = getattr(cls, "_users", 1) - 1
            if count <= 0:
                with suppress(ValueError): bpy.utils.unregister_class(cls)

        for func in self._processors:
            with suppress(KeyError): del asks.processors__internal__[func.asks_id]

        for func in self._draw_funcs:
            with suppress(KeyError): del asks.draw_funcs__internal__[func.asks_id]

        cls = self._type
        if cls:
            with suppress(ValueError): bpy.utils.unregister_class(cls)
            with suppress(AttributeError): delattr(bpy.types.Key, name)

        self._type = None
        self._components.clear()
        self._processors.clear()
        self._draw_funcs.clear()

ns = Namespace("inbetween")
ns.define_component("range", RangeComponent)

# later
c_range = system.components.create("inbetween.range", min=0.0, max=1.0)
entity.components.attach(c_range, name="range")