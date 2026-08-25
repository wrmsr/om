import struct


##


INT16 = struct.Struct('!h')
UINT16 = struct.Struct('!H')
INT32 = struct.Struct('!i')
INT32_PAIR = struct.Struct('!ii')

# Type code, then message length including the length itself but not the type code.
MESSAGE_HEADER = struct.Struct('!ci')
MESSAGE_HEADER_SIZE = MESSAGE_HEADER.size

# Overall format, then column count.
COPY_RESPONSE_HEADER = struct.Struct('!bh')

# Table oid, column attribute number, type oid, type size, type modifier, format code.
FIELD_DESCRIPTION_TAIL = struct.Struct('!ihihih')
