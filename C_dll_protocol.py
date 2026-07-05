from typing import Protocol, Annotated, get_args, get_type_hints, get_origin, dataclass_transform, TypeVar, Type
import inspect

import ctypes

__version__ = '0.0.0'


CBool = Annotated[bool, ctypes.c_bool]

CChar = Annotated[bytes, ctypes.c_char]
CWChar = Annotated[str, ctypes.c_wchar]

CByte = Annotated[int, ctypes.c_byte]
CUByte = Annotated[int, ctypes.c_ubyte]
CShort = Annotated[int, ctypes.c_short]
CUShort = Annotated[int, ctypes.c_ushort]
CInt = Annotated[int, ctypes.c_int]

CInt8 = Annotated[int, ctypes.c_int8]
CInt16 = Annotated[int, ctypes.c_int16]
CInt32 = Annotated[int, ctypes.c_int32]
CInt64 = Annotated[int, ctypes.c_int64]

CUInt = Annotated[int, ctypes.c_uint]
CUInt8 = Annotated[int, ctypes.c_uint8]
CUInt16 = Annotated[int, ctypes.c_uint16]
CUInt32 = Annotated[int, ctypes.c_uint32]
CUInt64 = Annotated[int, ctypes.c_uint64]

CLong = Annotated[int, ctypes.c_long]
CULong = Annotated[int, ctypes.c_ulong]
CLongLong = Annotated[int, ctypes.c_longlong]
CULongLong = Annotated[int, ctypes.c_ulonglong]

CSizeT = Annotated[int, ctypes.c_size_t]
CSSizeT = Annotated[int, ctypes.c_ssize_t]

CFloat = Annotated[float, ctypes.c_float]
CDouble = Annotated[float, ctypes.c_double]
CLongDouble = Annotated[float, ctypes.c_longdouble]

CCharP = Annotated[bytes, ctypes.c_char_p]
CWCharP = Annotated[str, ctypes.c_wchar_p]
CVoidP = Annotated[int, ctypes.c_void_p]

CPyObject = Annotated[object, ctypes.py_object]


class CStructMeta(type):
    
    def __new__(meta, name, bases, namespace, /, **kwds):
        Cls = super().__new__(meta, name, bases, namespace, **kwds)

        _fields_ = []
    
        for field_name, type_ in Cls.__annotations__.items():
            if field_name == '__structure__':
                continue

            if hasattr(type_, '__metadata__'):
                # Always the first annotated type
                type_ = type_.__metadata__[0]

            _fields_.append(
                (field_name, type_)
            )

        CStructure =  type(f'{name}C', (ctypes.Structure,), {'_fields_': _fields_})
        Cls.__structure__ = CStructure
        return Cls
    
    def __call__(Cls, *args, **kwargs):
        return Cls.__structure__(*args, **kwargs)


@dataclass_transform()
class CStruct(metaclass=CStructMeta):
    """
    Maybe a modern equivalent to `ctypes.Structure`.

    Write like a dataclass, but use C_dll_protocol's types e.g. `CInt`.

    Designed to fool type checkers! When CStruct is called to create an instance, through slight of hand 
    creates an appropriately constructed `ctypes.Structure`!

    The API remains the same and type hints should be appropriate.

    Can be used in conjunction with DLLProtocolBase as either arguments or return types

    Example
    -------
    ```
    class MyStruct:
        a: CInt
        b: CBool

    s = MyStruct(2, True)
    isinstance(s, ctypes.Structure)  # True!
    ```
    """
    __structure__: ctypes.Structure


T = TypeVar('T')

class DLLProtocolBase(Protocol):

    @classmethod
    def wrap(cls: Type[T], dll) -> T:
        """
        Wrapp dll with this protocol.

        Fools(?) typecheckers into thinking dll is an instance of this protocol... which it probably is.

        Additionally uses method type annotations to apply `argstype` and `restype` to the DLL automatically.


        Example
        -------
        ```
        from C_dll_protocol import CInt, CBool, CStruct, DLLProtocolBase

        class MyStruct(CStruct):
            a: CInt
            b: CBool
        
        class MyDLL(DLLProtocolBase):

            def my_func(self, arg: CInt) -> MyStruct:
                pass
            
        dll = MyDLL.wrap(WinDLL("my_dll.dll"))
        
        out = dll.my_func(arg=2)
        out.a  # int (decoded from ctypes.c_int)
        out.b  # bool (decoded from ctypes.c_bool)
        ```
        """
        for name, method in inspect.getmembers(
            cls,
            predicate=inspect.isfunction,
        ):
            # not this, or any special methods
            if name == "apply" or '__' in name:
                continue

            try:
                func = getattr(dll, name)
            except AttributeError:
                print(f"Warning: DLL does not export {name}")
                continue

            hints = get_type_hints(
                method,
                include_extras=True,
            )

            sig = inspect.signature(method)

            argtypes = []

            for param in sig.parameters.values():

                if param.name in ["self", "args", "kwargs"]:
                    continue

                annotation = hints[param.name]

                if hasattr(annotation, '__structure__'):
                    argtype = annotation.__structure__
                else:
                    if get_origin(annotation) is not Annotated:
                        raise TypeError(
                            f"{name}.{param.name} "
                            "must use Annotated[..., ctypes_type] or be a CStruct"
                        )

                    _, argtype = get_args(annotation)

                argtypes.append(argtype)

            return_annotation = hints.get("return")

            if hasattr(return_annotation, '__structure__'):
                return_type = return_annotation.__structure__
            else:
                if get_origin(return_annotation) is not Annotated:
                    raise TypeError(
                        f"{name}.return "
                        "must use Annotated[..., ctypes_type] or be a CStruct"
                    )

                _, return_type = get_args(return_annotation)

            func.argtypes = argtypes
            func.restype = return_type

        return dll
