# Copyright (c) 2007-2009, Mathieu Fenniak
# Copyright (c) The Contributors
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
# following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this list of conditions and the following
#   disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
#   disclaimer in the documentation and/or other materials provided with the distribution.
# * The name of the author may not be used to endorse or promote products derived from this software without specific
#   prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Original Author: Mathieu Fenniak
"""The mapping of PostgreSQL encoding names to Python codec names."""


##


# PostgreSQL encodings:
# https://www.postgresql.org/docs/current/multibyte.html
#
# Python encodings:
# https://docs.python.org/3/library/codecs.html
#
# Commented out encodings don't require a name change between PostgreSQL and Python. If the py side is None, then the
# encoding isn't supported.
PG_PY_ENCODINGS: dict[str, str | None] = {
    # Not supported:
    'mule_internal': None,
    'euc_tw': None,
    # Name fine as-is:
    # "euc_jp",
    # "euc_jis_2004",
    # "euc_kr",
    # "gb18030",
    # "gbk",
    # "johab",
    # "sjis",
    # "shift_jis_2004",
    # "uhc",
    # "utf8",
    # Different name:
    'euc_cn': 'gb2312',
    'iso_8859_5': 'is8859_5',
    'iso_8859_6': 'is8859_6',
    'iso_8859_7': 'is8859_7',
    'iso_8859_8': 'is8859_8',
    'koi8': 'koi8_r',
    'latin1': 'iso8859-1',
    'latin2': 'iso8859_2',
    'latin3': 'iso8859_3',
    'latin4': 'iso8859_4',
    'latin5': 'iso8859_9',
    'latin6': 'iso8859_10',
    'latin7': 'iso8859_13',
    'latin8': 'iso8859_14',
    'latin9': 'iso8859_15',
    'sql_ascii': 'ascii',
    'win866': 'cp886',
    'win874': 'cp874',
    'win1250': 'cp1250',
    'win1251': 'cp1251',
    'win1252': 'cp1252',
    'win1253': 'cp1253',
    'win1254': 'cp1254',
    'win1255': 'cp1255',
    'win1256': 'cp1256',
    'win1257': 'cp1257',
    'win1258': 'cp1258',
    'unicode': 'utf-8',  # Needed for Amazon Redshift
}
