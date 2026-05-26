from __future__ import annotations

from pydantic import BaseModel


class EKYCResponse(BaseModel):
    id_number: str = ""
    full_name: str = ""
    date_of_birth: str = ""
    gender: str = ""
    nationality: str = ""
    home_town: str = ""
    address: str = ""

    model_config = {
        "json_schema_extra": {
            "example": {
                "id_number": "001203012345",
                "full_name": "NGUYEN VAN A",
                "date_of_birth": "01/01/2000",
                "gender": "Nam",
                "nationality": "Viet Nam",
                "home_town": "Xa ABC, Huyen DEF, Tinh GHI",
                "address": "So 1 Duong XYZ, Phuong KLM, Quan NOP, TP HCM",
            }
        }
    }
