from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from faker import Faker


@dataclass(frozen=True, slots=True)
class BorrowerProfile:
    external_id: str
    first_name: str
    last_name: str
    email: str
    phone_number: str
    address_line_one: str
    city: str
    state: str
    postal_code: str

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "external_id": self.external_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone_number": self.phone_number,
            "address": {
                "line_one": self.address_line_one,
                "city": self.city,
                "state": self.state,
                "postal_code": self.postal_code,
            },
        }


class BorrowerFactory:
    """Builds synthetic borrowers for lower-environment testing."""

    def __init__(self, seed: int | None = None) -> None:
        self._faker = Faker()
        if seed is not None:
            self._faker.seed_instance(seed)

    def build(self, *, external_id: str | None = None) -> BorrowerProfile:
        first_name = self._faker.first_name()
        last_name = self._faker.last_name()
        identifier = external_id or f"cg-{uuid4().hex[:12]}"
        return BorrowerProfile(
            external_id=identifier,
            first_name=first_name,
            last_name=last_name,
            email=self._faker.email(),
            phone_number=self._faker.msisdn()[:12],
            address_line_one=self._faker.street_address(),
            city=self._faker.city(),
            state=self._faker.state_abbr(),
            postal_code=self._faker.postcode(),
        )
