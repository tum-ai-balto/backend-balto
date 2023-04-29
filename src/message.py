import dataclasses
from typing import Dict

import dataclasses_json
from enum import Enum

@dataclasses_json.dataclass_json
@dataclasses.dataclass
class EmployeeMessage:

    class Kind(Enum):
        TEXT = 'text'
        AUDIO = 'audio'
        IMAGE = 'image'

    kind: Kind
    content: str


@dataclasses_json.dataclass_json
@dataclasses.dataclass
class GenerateReportMessageRequest:
    employee: str
    employer: str
    employee_language: str
    employer_language: str
    chat_messages: list[EmployeeMessage]
