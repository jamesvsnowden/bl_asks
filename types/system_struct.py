
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .system import System

class SystemStruct:

    @property
    def system(self) -> 'System':
        return self.id_data.asks
