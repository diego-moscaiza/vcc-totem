from dataclasses import dataclass
from typing import Optional


@dataclass
class QueryResult:
    success: bool
    dni: str
    channel: str
    data: Optional[dict] = None
    error_message: Optional[str] = None
    has_offer: bool = False

    @property
    def found_client(self) -> bool:
        return self.success and self.data is not None
