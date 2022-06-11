
from typing import TYPE_CHECKING, Generic, Iterator, List, Optional, Tuple, TypeVar, Union
from uuid import uuid4
import bpy
from bpy.types import PropertyGroup, ShapeKey
from bpy.props import StringProperty
from rna_prop_ui import rna_idprop_ui_create
import bpy
if TYPE_CHECKING:
    from bpy.types import Driver, DriverVariable, Key, UILayout

MESSAGE_BROKER = object()
COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'}
COMPAT_OBJECTS = {'MESH', 'LATTICE', 'CURVE', 'SURFACE'}
_namespace = ""


def split_layout(layout: 'UILayout',
                 label: Optional[str]="",
                 align: Optional[bool]=False,
                 padding: Optional[Union[float, bool]]=False):
    split = layout.split(factor=0.385)
        
    row = split.row()
    row.alignment = 'RIGHT'
    if label:
        row.label(text=label)
    else:
        row.label(icon='BLANK1')

    row = split.row()
    col = row.column(align=align)

    if padding:
        factor = padding if isinstance(padding, float) else 2.0
        row.separator(factor=factor)

    return col


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

    def __init__(self) -> None:
        key = self.id_data
        idprop_ensure(key, self.weight_property_name)
        idprop_ensure(key, self.influence_property_name)

T = TypeVar("T", bound=ASKSComponent)


class ASKSNamespace(Generic[T]):

    @property
    def collection__internal__(self):
        raise NotImplementedError(f'{self.__class__.__name__}.collection__internal__')

    def __contains__(self, key: Union[T, str, ShapeKey]) -> bool:
        if isinstance(key, ShapeKey):
            if not key.id_data != self.id_data:
                return False
            key = key.name
        if isinstance(key, str):
            return self.find(key) != -1
        for item in self:
            if item == key:
                return True
        return False

    def __len__(self) -> int:
        return len(self.collection__internal__)

    def __iter__(self) -> Iterator[T]:
        return iter(self.collection__internal__)

    def __getitem__(self, key: Union[str, int, slice, ShapeKey]) -> Union[T, List[T]]:
        if isinstance(key, ShapeKey) and key.id_data == self.id_data:
            key = key.name
        return self.collection__internal__[key]

    def find(self, key: str) -> int:
        if isinstance(key, ShapeKey):
            if key.id_data != self.id_data:
                return -1
            key = key.name
        return self.collection__internal__.find(key)

    def get(self, key: Union[str, ShapeKey], fallback: Optional[object]=None) -> Optional[T]:
        if isinstance(key, ShapeKey):
            if key.id_data != self.id_data:
                return fallback
            key = key.name
        return self.collection__internal__.get(key, fallback)

    def keys(self) -> Iterator[str]:
        return self.collection__internal__.keys()

    def items(self) -> Iterator[Tuple[str, T]]:
        return self.collection__internal__.items()

    def values(self) -> Iterator[T]:
        return self.collection__internal__.values()


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


@bpy.app.handlers.persistent
def load_post_handler(_=None) -> None:
    bpy.msgbus.clear_by_owner(MESSAGE_BROKER)
    bpy.msgbus.subscribe_rna(key=(bpy.types.ShapeKey, "name"),
                             owner=MESSAGE_BROKER,
                             args=tuple(),
                             notify=shape_key_name_update_handler)


def register(namespace: str):
    global _namespace
    _namespace = namespace
    bpy.app.handlers.load_post.append(load_post_handler)
    load_post_handler() # Ensure messages are subscribed to on first install


def unregister():
    bpy.msgbus.clear_by_owner(MESSAGE_BROKER)
    bpy.app.handlers.load_post.remove(load_post_handler)
