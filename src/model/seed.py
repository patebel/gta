import json
from abc import abstractmethod

import numpy as np

from util.logging import log_error


class Seed:
    def __init__(self, ga_id, attributes, additional_data=None):
        self.ga_id = ga_id
        self.attributes = attributes
        self.additional_data = additional_data

    def get_attributes_string(self):
        return str(self.attributes)

    def to_dict(self):
        return {
            "ga_id": self.ga_id,
            "attributes": {
                key: np.asscalar(value) if isinstance(value, np.integer) else value
                for key, value in self.attributes.items()
            },
            "additional_data": self.additional_data
        }

    def to_json(self):
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, indent=4)

    @classmethod
    def from_json(cls, data):
        if isinstance(data, str):
            data = json.loads(data)
        return cls(
            ga_id=data.get("ga_id"),
            attributes=data.get("attributes"),
            additional_data=data.get("additional_data", None)
        )

    @abstractmethod
    def too_young(self):
        pass

    @abstractmethod
    def too_old(self):
        pass


class MiD2017Seed(Seed):
    def too_young(self):
        age = self._parse_age_as_number()
        return age is not None and age < 15

    def too_old(self):
        age = self._parse_age_as_number()
        return age is not None and age > 75

    def _parse_age_as_number(self):
        age_str = self.attributes.get("Alter (fehlende Angaben ergänzt aus HH-Interview)")
        try:
            age = int(age_str)
            return age
        except ValueError:
            log_error(f'{age_str} is not an integer')
            return None


class CensusSeed(Seed):
    def too_young(self):
        return self.attributes.get("Altersgruppe") == "unter 15"

    def too_old(self):
        return self.attributes.get("Altersgruppe") == "75 und älter"
