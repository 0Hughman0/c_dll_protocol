# C DLL Protocol

Modern Python includes lots of nice quality of life improvements, such as type annotations, and clever tools like dataclasses.

However, the built-in `ctypes` API uses none of these features. Which makes it not nice to use, and feels like a blast to the past.

This short module (< 200 lines) allows for defining an equivalent to a `typing.Protocol`, but one that describes the API of a DLL.

Leveraging Pythons `typing.Annotated`, we take inspriration from the dataclasses implementation to provide hopefully a more familiar way to define `ctypes.Structure`s.

With a bit of slight of hand, I think this broadly fools type checkers into giving appropriate type hints on your dll object.

```python
# Old syntax ##########################################################################
from ctypes import Structure, c_int, c_bool, CDLL

class MyStruct(Structure):
    _fields_ = [
        ('a', c_int),
        ('b', c_bool)
    ]

dll = CDLL('my_dll.dll')

dll.my_func.argtypes = [c_int]
dll.my_func.restype = MyStruct

result = dll.my_func(5)  # no parameter hints
result.a  # no type hints for return type.


# With c_dll_protocol ################################################################
from ctypes import CDLL
from c_dll_protocol imoprt CInt, CBool, DLLProtocolBase

class MyStruct(CStruct):
    a: CInt
    b: CBool

class MyDLLProtocol(DLLProtocolBase):

    def my_func(self, a: CInt) -> MyStruct: ...

# Here type checkers are fooled into thinking this returns a MyDLLProtocol instance
# but in fact it is just the original DLL object 😈
wrapped_dll = MyDLLProtocol.wrap(CDLL('my_dll.dll'))

result = wrapped_dll.my_func(5)  # hints for paramters and return types are provided.
result.a  # type checkers know a is an int.

# c_dll_protocol takes care of settings these on your behalf.
wrapped_dll.my_func.restype  # returns CMyStuct
wrapped_dll.my_func.argtypes  # returns [c_int]
```
