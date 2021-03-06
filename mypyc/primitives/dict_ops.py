"""Primitive dict ops."""

from typing import List

from mypyc.ir.ops import EmitterInterface, ERR_FALSE, ERR_MAGIC, ERR_NEVER, ERR_NEG_INT
from mypyc.ir.rtypes import (
    dict_rprimitive, object_rprimitive, bool_rprimitive, int_rprimitive,
    list_rprimitive, dict_next_rtuple_single, dict_next_rtuple_pair, c_pyssize_t_rprimitive,
    c_int_rprimitive
)

from mypyc.primitives.registry import (
    name_ref_op, method_op, func_op,
    simple_emit, name_emit, c_custom_op, c_method_op, c_function_op, c_binary_op
)


# Get the 'dict' type object.
name_ref_op('builtins.dict',
            result_type=object_rprimitive,
            error_kind=ERR_NEVER,
            emit=name_emit('&PyDict_Type', target_type="PyObject *"),
            is_borrowed=True)

# dict[key]
dict_get_item_op = c_method_op(
    name='__getitem__',
    arg_types=[dict_rprimitive, object_rprimitive],
    return_type=object_rprimitive,
    c_function_name='CPyDict_GetItem',
    error_kind=ERR_MAGIC)

# dict[key] = value
dict_set_item_op = c_method_op(
    name='__setitem__',
    arg_types=[dict_rprimitive, object_rprimitive, object_rprimitive],
    return_type=c_int_rprimitive,
    c_function_name='CPyDict_SetItem',
    error_kind=ERR_NEG_INT)

# key in dict
c_binary_op(
    name='in',
    arg_types=[object_rprimitive, dict_rprimitive],
    return_type=c_int_rprimitive,
    c_function_name='PyDict_Contains',
    error_kind=ERR_NEG_INT,
    truncated_type=bool_rprimitive,
    ordering=[1, 0])

# dict1.update(dict2)
dict_update_op = c_method_op(
    name='update',
    arg_types=[dict_rprimitive, dict_rprimitive],
    return_type=c_int_rprimitive,
    c_function_name='CPyDict_Update',
    error_kind=ERR_NEG_INT,
    priority=2)

# Operation used for **value in dict displays.
# This is mostly like dict.update(obj), but has customized error handling.
dict_update_in_display_op = c_custom_op(
    arg_types=[dict_rprimitive, dict_rprimitive],
    return_type=c_int_rprimitive,
    c_function_name='CPyDict_UpdateInDisplay',
    error_kind=ERR_NEG_INT)

# dict.update(obj)
c_method_op(
    name='update',
    arg_types=[dict_rprimitive, object_rprimitive],
    return_type=c_int_rprimitive,
    c_function_name='CPyDict_UpdateFromAny',
    error_kind=ERR_NEG_INT)

# dict.get(key, default)
c_method_op(
    name='get',
    arg_types=[dict_rprimitive, object_rprimitive, object_rprimitive],
    return_type=object_rprimitive,
    c_function_name='CPyDict_Get',
    error_kind=ERR_MAGIC)

# dict.get(key)
method_op(
    name='get',
    arg_types=[dict_rprimitive, object_rprimitive],
    result_type=object_rprimitive,
    error_kind=ERR_MAGIC,
    emit=simple_emit('{dest} = CPyDict_Get({args[0]}, {args[1]}, Py_None);'))

# Construct an empty dictionary.
dict_new_op = c_custom_op(
    arg_types=[],
    return_type=dict_rprimitive,
    c_function_name='PyDict_New',
    error_kind=ERR_MAGIC)

# Construct a dictionary from keys and values.
# Positional argument is the number of key-value pairs
# Variable arguments are (key1, value1, ..., keyN, valueN).
dict_build_op = c_custom_op(
    arg_types=[c_pyssize_t_rprimitive],
    return_type=dict_rprimitive,
    c_function_name='CPyDict_Build',
    error_kind=ERR_MAGIC,
    var_arg_type=object_rprimitive)

# Construct a dictionary from another dictionary.
c_function_op(
    name='builtins.dict',
    arg_types=[dict_rprimitive],
    return_type=dict_rprimitive,
    c_function_name='PyDict_Copy',
    error_kind=ERR_MAGIC,
    priority=2)

# Generic one-argument dict constructor: dict(obj)
c_function_op(
    name='builtins.dict',
    arg_types=[object_rprimitive],
    return_type=dict_rprimitive,
    c_function_name='CPyDict_FromAny',
    error_kind=ERR_MAGIC)

# dict.keys()
c_method_op(
    name='keys',
    arg_types=[dict_rprimitive],
    return_type=object_rprimitive,
    c_function_name='CPyDict_KeysView',
    error_kind=ERR_MAGIC)

# dict.values()
c_method_op(
    name='values',
    arg_types=[dict_rprimitive],
    return_type=object_rprimitive,
    c_function_name='CPyDict_ValuesView',
    error_kind=ERR_MAGIC)

# dict.items()
c_method_op(
    name='items',
    arg_types=[dict_rprimitive],
    return_type=object_rprimitive,
    c_function_name='CPyDict_ItemsView',
    error_kind=ERR_MAGIC)

# list(dict.keys())
dict_keys_op = c_custom_op(
    arg_types=[dict_rprimitive],
    return_type=list_rprimitive,
    c_function_name='CPyDict_Keys',
    error_kind=ERR_MAGIC)

# list(dict.values())
dict_values_op = c_custom_op(
    arg_types=[dict_rprimitive],
    return_type=list_rprimitive,
    c_function_name='CPyDict_Values',
    error_kind=ERR_MAGIC)

# list(dict.items())
dict_items_op = c_custom_op(
    arg_types=[dict_rprimitive],
    return_type=list_rprimitive,
    c_function_name='CPyDict_Items',
    error_kind=ERR_MAGIC)


def emit_len(emitter: EmitterInterface, args: List[str], dest: str) -> None:
    temp = emitter.temp_name()
    emitter.emit_declaration('Py_ssize_t %s;' % temp)
    emitter.emit_line('%s = PyDict_Size(%s);' % (temp, args[0]))
    emitter.emit_line('%s = CPyTagged_ShortFromSsize_t(%s);' % (dest, temp))


# len(dict)
func_op(name='builtins.len',
        arg_types=[dict_rprimitive],
        result_type=int_rprimitive,
        error_kind=ERR_NEVER,
        emit=emit_len)

# PyDict_Next() fast iteration
dict_key_iter_op = c_custom_op(
    arg_types=[dict_rprimitive],
    return_type=object_rprimitive,
    c_function_name='CPyDict_GetKeysIter',
    error_kind=ERR_MAGIC)

dict_value_iter_op = c_custom_op(
    arg_types=[dict_rprimitive],
    return_type=object_rprimitive,
    c_function_name='CPyDict_GetValuesIter',
    error_kind=ERR_MAGIC)

dict_item_iter_op = c_custom_op(
    arg_types=[dict_rprimitive],
    return_type=object_rprimitive,
    c_function_name='CPyDict_GetItemsIter',
    error_kind=ERR_MAGIC)

dict_next_key_op = c_custom_op(
    arg_types=[object_rprimitive, int_rprimitive],
    return_type=dict_next_rtuple_single,
    c_function_name='CPyDict_NextKey',
    error_kind=ERR_NEVER)

dict_next_value_op = c_custom_op(
    arg_types=[object_rprimitive, int_rprimitive],
    return_type=dict_next_rtuple_single,
    c_function_name='CPyDict_NextValue',
    error_kind=ERR_NEVER)

dict_next_item_op = c_custom_op(
    arg_types=[object_rprimitive, int_rprimitive],
    return_type=dict_next_rtuple_pair,
    c_function_name='CPyDict_NextItem',
    error_kind=ERR_NEVER)

# check that len(dict) == const during iteration
dict_check_size_op = c_custom_op(
    arg_types=[dict_rprimitive, int_rprimitive],
    return_type=bool_rprimitive,
    c_function_name='CPyDict_CheckSize',
    error_kind=ERR_FALSE)
