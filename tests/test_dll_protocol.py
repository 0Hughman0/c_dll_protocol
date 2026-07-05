
from unittest.mock import Mock

from ctypes import Structure, c_int, c_bool
from C_dll_protocol import CStruct, DLLProtocolBase, CInt, CBool


def test_CStruct() -> None:
    class MyStruct(CStruct):
        a: CInt
        b: CBool
    
    s = MyStruct(a=1, b=True)

    assert isinstance(s, Structure)
    assert s.a == 1
    assert s.b == True

    assert s._fields_ == [
        ('a', c_int),
        ('b', c_bool)
    ]


def test_wrapping() -> None:
    class RealReturn(Structure):
        _fields_ = [
            ('a', c_int),
            ('b', c_bool)
        ]
    class MyStruct(CStruct):
        a: CInt
        b: CBool

    class MyDLLProtocol(DLLProtocolBase):

        def my_fun(self, a: CInt) -> MyStruct: ...
    
    dll = Mock()
    dll.my_fun = Mock(return_value=RealReturn(5, False))
    wraped_dll = MyDLLProtocol.wrap(dll)

    assert wraped_dll.my_fun.argtypes == [c_int]
    assert wraped_dll.my_fun.restype == MyStruct.__structure__

    response = wraped_dll.my_fun(10)

    assert response.a == 5
    assert response.b == False
