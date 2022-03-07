# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: sshe-cipher-param.proto

import sys
_b = sys.version_info[0] < 3 and (lambda x: x) or (lambda x: x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


DESCRIPTOR = _descriptor.FileDescriptor(
    name='sshe-cipher-param.proto',
    package='com.webank.ai.fate.core.mlmodel.buffer',
    syntax='proto3',
    serialized_options=_b('B\020CipherParamProto'),
    serialized_pb=_b('\n\x17sshe-cipher-param.proto\x12&com.webank.ai.fate.core.mlmodel.buffer\"\xa4\x01\n\x06\x43ipher\x12K\n\npublic_key\x18\x01 \x01(\x0b\x32\x37.com.webank.ai.fate.core.mlmodel.buffer.CipherPublicKey\x12M\n\x0bprivate_key\x18\x02 \x01(\x0b\x32\x38.com.webank.ai.fate.core.mlmodel.buffer.CipherPrivateKey\"\x1c\n\x0f\x43ipherPublicKey\x12\t\n\x01n\x18\x01 \x01(\t\"(\n\x10\x43ipherPrivateKey\x12\t\n\x01p\x18\x01 \x01(\t\x12\t\n\x01q\x18\x02 \x01(\t\"\x97\x01\n\nCipherText\x12K\n\npublic_key\x18\x01 \x01(\x0b\x32\x37.com.webank.ai.fate.core.mlmodel.buffer.CipherPublicKey\x12\x13\n\x0b\x63ipher_text\x18\x02 \x01(\t\x12\x10\n\x08\x65xponent\x18\x03 \x01(\t\x12\x15\n\ris_obfuscator\x18\x04 \x01(\x08\x42\x12\x42\x10\x43ipherParamProtob\x06proto3')
)


_CIPHER = _descriptor.Descriptor(
    name='Cipher',
    full_name='com.webank.ai.fate.core.mlmodel.buffer.Cipher',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name='public_key', full_name='com.webank.ai.fate.core.mlmodel.buffer.Cipher.public_key', index=0,
            number=1, type=11, cpp_type=10, label=1,
            has_default_value=False, default_value=None,
            message_type=None, enum_type=None, containing_type=None,
            is_extension=False, extension_scope=None,
            serialized_options=None, file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='private_key', full_name='com.webank.ai.fate.core.mlmodel.buffer.Cipher.private_key', index=1,
            number=2, type=11, cpp_type=10, label=1,
            has_default_value=False, default_value=None,
            message_type=None, enum_type=None, containing_type=None,
            is_extension=False, extension_scope=None,
            serialized_options=None, file=DESCRIPTOR),
    ],
    extensions=[
    ],
    nested_types=[],
    enum_types=[
    ],
    serialized_options=None,
    is_extendable=False,
    syntax='proto3',
    extension_ranges=[],
    oneofs=[
    ],
    serialized_start=68,
    serialized_end=232,
)


_CIPHERPUBLICKEY = _descriptor.Descriptor(
    name='CipherPublicKey',
    full_name='com.webank.ai.fate.core.mlmodel.buffer.CipherPublicKey',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name='n', full_name='com.webank.ai.fate.core.mlmodel.buffer.CipherPublicKey.n', index=0,
            number=1, type=9, cpp_type=9, label=1,
            has_default_value=False, default_value=_b("").decode('utf-8'),
            message_type=None, enum_type=None, containing_type=None,
            is_extension=False, extension_scope=None,
            serialized_options=None, file=DESCRIPTOR),
    ],
    extensions=[
    ],
    nested_types=[],
    enum_types=[
    ],
    serialized_options=None,
    is_extendable=False,
    syntax='proto3',
    extension_ranges=[],
    oneofs=[
    ],
    serialized_start=234,
    serialized_end=262,
)


_CIPHERPRIVATEKEY = _descriptor.Descriptor(
    name='CipherPrivateKey',
    full_name='com.webank.ai.fate.core.mlmodel.buffer.CipherPrivateKey',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name='p', full_name='com.webank.ai.fate.core.mlmodel.buffer.CipherPrivateKey.p', index=0,
            number=1, type=9, cpp_type=9, label=1,
            has_default_value=False, default_value=_b("").decode('utf-8'),
            message_type=None, enum_type=None, containing_type=None,
            is_extension=False, extension_scope=None,
            serialized_options=None, file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='q', full_name='com.webank.ai.fate.core.mlmodel.buffer.CipherPrivateKey.q', index=1,
            number=2, type=9, cpp_type=9, label=1,
            has_default_value=False, default_value=_b("").decode('utf-8'),
            message_type=None, enum_type=None, containing_type=None,
            is_extension=False, extension_scope=None,
            serialized_options=None, file=DESCRIPTOR),
    ],
    extensions=[
    ],
    nested_types=[],
    enum_types=[
    ],
    serialized_options=None,
    is_extendable=False,
    syntax='proto3',
    extension_ranges=[],
    oneofs=[
    ],
    serialized_start=264,
    serialized_end=304,
)


_CIPHERTEXT = _descriptor.Descriptor(
    name='CipherText',
    full_name='com.webank.ai.fate.core.mlmodel.buffer.CipherText',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name='public_key', full_name='com.webank.ai.fate.core.mlmodel.buffer.CipherText.public_key', index=0,
            number=1, type=11, cpp_type=10, label=1,
            has_default_value=False, default_value=None,
            message_type=None, enum_type=None, containing_type=None,
            is_extension=False, extension_scope=None,
            serialized_options=None, file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='cipher_text', full_name='com.webank.ai.fate.core.mlmodel.buffer.CipherText.cipher_text', index=1,
            number=2, type=9, cpp_type=9, label=1,
            has_default_value=False, default_value=_b("").decode('utf-8'),
            message_type=None, enum_type=None, containing_type=None,
            is_extension=False, extension_scope=None,
            serialized_options=None, file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='exponent', full_name='com.webank.ai.fate.core.mlmodel.buffer.CipherText.exponent', index=2,
            number=3, type=9, cpp_type=9, label=1,
            has_default_value=False, default_value=_b("").decode('utf-8'),
            message_type=None, enum_type=None, containing_type=None,
            is_extension=False, extension_scope=None,
            serialized_options=None, file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='is_obfuscator', full_name='com.webank.ai.fate.core.mlmodel.buffer.CipherText.is_obfuscator', index=3,
            number=4, type=8, cpp_type=7, label=1,
            has_default_value=False, default_value=False,
            message_type=None, enum_type=None, containing_type=None,
            is_extension=False, extension_scope=None,
            serialized_options=None, file=DESCRIPTOR),
    ],
    extensions=[
    ],
    nested_types=[],
    enum_types=[
    ],
    serialized_options=None,
    is_extendable=False,
    syntax='proto3',
    extension_ranges=[],
    oneofs=[
    ],
    serialized_start=307,
    serialized_end=458,
)

_CIPHER.fields_by_name['public_key'].message_type = _CIPHERPUBLICKEY
_CIPHER.fields_by_name['private_key'].message_type = _CIPHERPRIVATEKEY
_CIPHERTEXT.fields_by_name['public_key'].message_type = _CIPHERPUBLICKEY
DESCRIPTOR.message_types_by_name['Cipher'] = _CIPHER
DESCRIPTOR.message_types_by_name['CipherPublicKey'] = _CIPHERPUBLICKEY
DESCRIPTOR.message_types_by_name['CipherPrivateKey'] = _CIPHERPRIVATEKEY
DESCRIPTOR.message_types_by_name['CipherText'] = _CIPHERTEXT
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

Cipher = _reflection.GeneratedProtocolMessageType('Cipher', (_message.Message,), {
    'DESCRIPTOR': _CIPHER,
    '__module__': 'sshe_cipher_param_pb2'
    # @@protoc_insertion_point(class_scope:com.webank.ai.fate.core.mlmodel.buffer.Cipher)
})
_sym_db.RegisterMessage(Cipher)

CipherPublicKey = _reflection.GeneratedProtocolMessageType('CipherPublicKey', (_message.Message,), {
    'DESCRIPTOR': _CIPHERPUBLICKEY,
    '__module__': 'sshe_cipher_param_pb2'
    # @@protoc_insertion_point(class_scope:com.webank.ai.fate.core.mlmodel.buffer.CipherPublicKey)
})
_sym_db.RegisterMessage(CipherPublicKey)

CipherPrivateKey = _reflection.GeneratedProtocolMessageType('CipherPrivateKey', (_message.Message,), {
    'DESCRIPTOR': _CIPHERPRIVATEKEY,
    '__module__': 'sshe_cipher_param_pb2'
    # @@protoc_insertion_point(class_scope:com.webank.ai.fate.core.mlmodel.buffer.CipherPrivateKey)
})
_sym_db.RegisterMessage(CipherPrivateKey)

CipherText = _reflection.GeneratedProtocolMessageType('CipherText', (_message.Message,), {
    'DESCRIPTOR': _CIPHERTEXT,
    '__module__': 'sshe_cipher_param_pb2'
    # @@protoc_insertion_point(class_scope:com.webank.ai.fate.core.mlmodel.buffer.CipherText)
})
_sym_db.RegisterMessage(CipherText)


DESCRIPTOR._options = None
# @@protoc_insertion_point(module_scope)