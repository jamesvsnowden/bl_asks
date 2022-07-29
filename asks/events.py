
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple, Union
from sys import modules
from logging import getLogger
from bpy.types import PropertyGroup
from bpy.props import CollectionProperty, StringProperty

log = getLogger("asks")

class EventProxy(PropertyGroup):

    @property
    def handler(self) -> Optional[Callable]:
        module = modules.get(self.module)
        if module:
            handler = getattr(module, self.name, None)
            if callable(handler):
                return handler

    module: StringProperty(
        name="Path",
        get=lambda self: self.get("module", ""),
        options=set()
        )

    name: StringProperty(
        name="Name",
        get=lambda self: self.get("name", ""),
        options=set()
        )

    type: StringProperty(
        name="Type",
        get=lambda self: self.get("type", ""),
        options=set()
        )

    def __init__(self, type_: str, handler: Callable) -> None:
        self["type"] = type_
        self["name"] = handler.__name__
        self["module"] = handler.__module__

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, EventProxy):
            return other.module == self.module and other.name == self.name
        elif callable(other):
            return other.__module__ == self.module and other.__name__ == self.name
        else:
            return False

    def __call__(self,
                 dispatcher: 'EventDispatcher',
                 *args: Tuple[Any],
                 **kwargs: Dict[str, Any]) -> None:
        handler = self.handler
        if handler:
            try:
                handler(dispatcher, *args, **kwargs)
            except Exception:
                log.exception(f'An error occurred during the handling of event "{self.type}"')
        else:
            log.error(f'Handler for event "{self.type}" not found at {self.module}.{self.name}')


class EventProxies(PropertyGroup):

    internal__: CollectionProperty(type=EventProxy)

    name: StringProperty(
        name="Name",
        get=lambda self: self.get("name", ""),
        set=lambda _,__: log.warning("EventProxies.name is read-only"),
        options=set()
        )

    type: StringProperty(
        name="Type",
        get=lambda self: self.get("name", ""),
        options=set()
        )

    def __init__(self, type_: str) -> None:
        self["name"] = type_

    def __contains__(self, item: Any) -> bool:
        return any(proxy == item for proxy in self)

    def __iter__(self) -> Iterator[EventProxy]:
        return iter(self.internal__)

    def __len__(self) -> int:
        return len(self.internal__)

    def __getitem__(self, key: Union[int, slice]) -> Union[EventProxy, List[EventProxy]]:
        return self.internal__[key]

    def __call__(self, dispatcher: 'EventDispatcher', *args: Tuple[Any], **kwargs: Dict[str, Any]) -> None:
        for proxy in self:
            proxy(dispatcher, *args, **kwargs)

    def add(self, handler: Callable) -> None:
        if handler not in self:
            self.internal__.add().__init__(self.name, handler)

    def remove(self, handler: Callable) -> None:
        index = next((i for i, x in enumerate(self) if x == handler), -1)
        if index != -1:
            self.internal__.remove(index)


class EventDispatcher:

    eventproxies__: CollectionProperty(type=EventProxies)

    def bind(self, key: str, handler: Callable) -> None:
        if not isinstance(key, str):
            raise TypeError()
        if not callable(handler):
            raise TypeError()
        proxies = self.eventproxies__.get(key)
        if proxies is None:
            proxies = self.eventproxies__.add()
            proxies.__init__(key)
        proxies.add(handler)

    def unbind(self, key: str, handler: Callable) -> None:
        if not isinstance(key, str):
            raise TypeError()
        if not callable(handler):
            raise TypeError()
        proxies = self.eventproxies__.get(key)
        if proxies is not None:
            proxies.remove(handler)

    def dispatch(self, key: str, *args: Tuple[Any], **kwargs: Dict[str, Any]) -> None:
        proxies = self.eventproxies__.get(key)
        if proxies is not None:
            proxies(self, *args, **kwargs)
