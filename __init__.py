
from typing import TYPE_CHECKING, Callable, Optional
from uuid import uuid4
import bpy
from bpy.types import PropertyGroup
from bpy.props import StringProperty
from rna_prop_ui import rna_idprop_ui_create
import bpy
if TYPE_CHECKING:
    from bpy.types import Driver, DriverVariable, Key, ShapeKey

MESSAGE_BROKER = object()
_namespace = ""
_setup_component = None


def idprop_ensure(key: 'Key', name: str) -> None:
    if key.get(name) is None:
        idprop_create(key, name)


def idprop_create(key: 'Key', name: str) -> None:
    rna_idprop_ui_create(key, name, default=1.0, min=0.0, max=1.0, soft_min=0.0, soft_max=1.0)


def identifier(identifiable: 'Identifiable') -> str:
    value = PropertyGroup.get(identifiable, "identifier")
    if not value:
        value = uuid4().hex
        PropertyGroup.__setitem__(identifiable, "identifier", value)
    return value


class Identifiable:

    identifier: StringProperty(
        name="Identifier",
        description="Unique data identifier (read-only)",
        get=identifier,
        options={'HIDDEN'}
        )


class ASKSComponent(Identifiable):

    @property
    def influence_property_name(self) -> str:
        return f'asks_infl_{self.identifier}'

    @property
    def influence_property_path(self) -> str:
        return f'["{self.influence_property_name}"]'

    @property
    def weight_property_name(self) -> str:
        return f'asks_wght_{self.identifier}'

    @property
    def weight_property_path(self) -> str:
        return f'["{self.weight_property_name}"]'


def add_proxy_variable(driver: 'Driver', component: ASKSComponent) -> None:
    var = driver.variables.new()
    var.type = 'SINGLE_PROP'
    var.name = f'{_namespace}_{component.identifier}'
    tgt = var.targets[0]
    tgt.id_type = 'KEY'
    tgt.id = component.id_data
    tgt.data_path = "reference_key.value"


def get_proxy_variable(driver: 'Driver') -> Optional['DriverVariable']:
    vars = driver.variables
    if len(vars) >= 1:
        var = vars[0]
        if var.name.startswith(_namespace) and var.type == 'SINGLE_PROP':
            tgt = var.targets[0]
            if tgt.id_type == 'KEY' and tgt.data_path == "reference_key.value":
                return var


def find_shape_key_value_driver(shape: 'ShapeKey') -> Optional['Driver']:
    animdata = shape.id_data
    if animdata is not None:
        return animdata.drivers.find(f'key_blocks["{shape.name}"].value')


def shape_key_name_update_handler():
    for key in bpy.data.shape_keys:
        if key.is_property_set(_namespace):
            ns = getattr(key, _namespace)
            for kb in key.key_blocks:
                fc = find_shape_key_value_driver(kb)
                if fc is not None:
                    var = get_proxy_variable(fc.driver)
                    if var is not None:
                        id = var.name[len(_namespace)+1:]
                        co = next((x for x in ns if x.get("identifier", "") == id), None)
                        if co is not None:
                            co["name"] = kb.name


def setup():
    keys = bpy.data.shape_keys
    if keys:
        for key in keys:
            if key.is_property_set(_namespace):
                for co in getattr(key, _namespace):
                    if isinstance(co, ASKSComponent):
                        idprop_ensure(key, co.weight_property_name)
                        idprop_ensure(key, co.influence_property_name)
                        if _setup_component:
                            _setup_component(co)


def try_setup():
    try:
        setup()
    except AttributeError: pass


@bpy.app.handlers.persistent
def load_post_handler(_=None) -> None:
    bpy.msgbus.clear_by_owner(MESSAGE_BROKER)
    bpy.msgbus.subscribe_rna(key=(bpy.types.ShapeKey, "name"),
                             owner=MESSAGE_BROKER,
                             args=tuple(),
                             notify=shape_key_name_update_handler)

    # On initial load accessing bpy.data.shape_keys will raise AttributeError.
    # Retry after 5 seconds.
    try:
        setup()
    except AttributeError:
        bpy.app.timers.register(try_setup, first_interval=5)


def register(namespace: str, setup_component: Optional[Callable[[ASKSComponent], None]]=None):
    global _namespace
    _namespace = namespace
    if setup_component:
        global _setup_component
        _setup_component = setup_component
    bpy.app.handlers.load_post.append(load_post_handler)
    load_post_handler() # Ensure messages are subscribed to on first install


def unregister():
    bpy.msgbus.clear_by_owner(MESSAGE_BROKER)
    bpy.app.handlers.load_post.remove(load_post_handler)
