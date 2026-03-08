"""Primitive value generation: names, emails, dates, IDs, etc. (Faker + Mimesis + custom)."""

import random
import uuid
from datetime import date, datetime, timedelta
from typing import Any

from faker import Faker
from mimesis import Generic
from mimesis.locales import Locale

from data_forge.models.schema import ColumnDef, DataType


class PrimitiveGenerator:
    """Generate single field values by DataType and hints. Seeded for reproducibility."""

    def __init__(self, seed: int = 42, locale: str = "en_US"):
        self._seed = seed
        self._rng = random.Random(seed)
        self._faker = Faker(locale)
        self._faker.seed_instance(seed)
        try:
            loc = Locale.EN
            if locale.startswith("de"):
                loc = Locale.DE
            elif locale.startswith("es"):
                loc = Locale.ES
            elif locale.startswith("fr"):
                loc = Locale.FR
            self._mimesis = Generic(locale=loc)
            self._mimesis.random.seed(seed)
        except Exception:
            self._mimesis = Generic(locale=Locale.EN)
            self._mimesis.random.seed(seed)

    def generate_value(self, col: ColumnDef, row_index: int = 0) -> Any:
        """Generate one value for a column. row_index can be used for uniqueness."""
        hint = (col.generator_hint or "").lower()
        dtype = col.data_type

        # Hint overrides
        if hint in ("name", "full_name", "person"):
            return self._faker.name()
        if hint in ("email", "mail"):
            return self._faker.email()
        if hint in ("phone", "tel"):
            return self._faker.phone_number()
        if hint in ("company", "org", "organization"):
            return self._faker.company()
        if hint in ("address", "street"):
            return self._faker.address().replace("\n", ", ")
        if hint in ("city",):
            return self._faker.city()
        if hint in ("country",):
            return self._faker.country_code()
        if hint in ("uuid", "id", "guid"):
            return str(uuid.UUID(int=self._rng.getrandbits(128)))
        if hint in ("date", "created_at", "updated_at"):
            return self._date_in_range(col)

        # By type
        if dtype == DataType.STRING or dtype == DataType.TEXT:
            return self._string(col, row_index)
        if dtype == DataType.INTEGER or dtype == DataType.BIGINT:
            return self._integer(col)
        if dtype == DataType.FLOAT or dtype == DataType.DECIMAL:
            return self._float(col)
        if dtype == DataType.BOOLEAN:
            return self._rng.choice([True, False])
        if dtype == DataType.DATE:
            return self._date_in_range(col)
        if dtype == DataType.DATETIME or dtype == DataType.TIMESTAMP:
            return self._datetime_in_range(col)
        if dtype == DataType.UUID:
            return str(uuid.UUID(int=self._rng.getrandbits(128)))
        if dtype == DataType.EMAIL:
            return self._faker.email()
        if dtype == DataType.PHONE:
            return self._faker.phone_number()
        if dtype == DataType.URL:
            return self._faker.url()
        if dtype == DataType.ENUM and col.enum_values:
            return self._rng.choice(col.enum_values)
        if dtype == DataType.CURRENCY:
            return round(self._rng.uniform(col.min_value or 0, col.max_value or 10000), 2)
        if dtype == DataType.PERCENT:
            return round(self._rng.uniform(0, 1), 4)
        if dtype == DataType.JSON:
            return {"_placeholder": self._rng.randint(1, 99999)}
        return self._string(col, row_index)

    def _string(self, col: ColumnDef, row_index: int) -> str:
        min_l = col.min_length or 1
        max_l = col.max_length or 255
        length = self._rng.randint(min_l, min(max_l, 255))
        word = self._faker.word()
        if col.unique:
            return f"{word}_{row_index}_{self._rng.randint(0, 999999)}"[:max_l]
        # Faker text() needs at least 5 chars
        length = max(length, 5)
        return self._faker.text(max_nb_chars=min(length, 2000))[:max_l]

    def _integer(self, col: ColumnDef) -> int:
        lo = col.min_value if col.min_value is not None else 0
        hi = col.max_value if col.max_value is not None else 2**31 - 1
        return self._rng.randint(int(lo), int(hi))

    def _float(self, col: ColumnDef) -> float:
        lo = col.min_value if col.min_value is not None else 0.0
        hi = col.max_value if col.max_value is not None else 1.0
        return round(self._rng.uniform(lo, hi), 4)

    def _date_in_range(self, col: ColumnDef) -> str:
        # Return ISO date string
        base = date(2020, 1, 1)
        days = self._rng.randint(0, 1825)  # ~5 years
        d = base + timedelta(days=days)
        return d.isoformat()

    def _datetime_in_range(self, col: ColumnDef) -> str:
        base = datetime(2020, 1, 1)
        delta = timedelta(
            days=self._rng.randint(0, 1825),
            seconds=self._rng.randint(0, 86400),
        )
        dt = base + delta
        return dt.isoformat()
