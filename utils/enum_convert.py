import inspect
import importlib
from enum import Enum

module = importlib.import_module("enums")


class _RawToEnum:
    _file_enums = (
        attribute for att_name, attribute in vars(module).items()
        if inspect.isclass(attribute) and issubclass(attribute, Enum)
    )
    """
        Creates a dict formatted as such:
            {
                SampleEnum1: {
                    'value_string': StringEnum,
                    ...
                },
                SampleEnum2: {
                    'other_value_string': OtherValueEnum,
                    ...
                },
                ...
            }
    """
    _enum_conversions = {
        enum_cls.__name__: {
            e.value: e for e in enum_cls
        }
        for enum_cls in _file_enums
    }

    def __call__(self, enum_class: Enum, enum_value: str):
        return self.raw_to_enum(enum_class=enum_class,
                                enum_value=enum_value)

    @classmethod
    def raw_to_enum(cls, enum_class: Enum, enum_value: str):
        return cls._enum_conversions[enum_class.__name__][enum_value]



RawToEnum = _RawToEnum()
