"""Translation of Go's text/template/helper.go construction helpers."""

# Copyright 2011 The Go Authors.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
# following conditions are met:
#
#    * Redistributions of source code must retain the above copyright notice, this list of conditions and the following
#      disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the
#      following disclaimer in the documentation and/or other materials provided with the distribution.
#    * Neither the name of Google LLC nor the names of its contributors may be used to endorse or promote products
#      derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
import glob
import os.path
import typing as ta

from omcore import check

from . import tmpl
from .quoting import quote_go_string_or_raw


##


def must(template: tmpl.Template) -> tmpl.Template:
    # Python reports parse failures by raising directly, so a successfully supplied template is already Go's Must
    # result.
    return template


def parse_files(*filenames: str) -> tmpl.Template:
    return _parse_files(None, filenames)


def _parse_files(template: tmpl.Template | None, filenames: ta.Sequence[str]) -> tmpl.Template:
    if not filenames:
        raise ValueError('template: no files named in call to parse_files')
    root = template
    for filename in filenames:
        name = os.path.basename(filename)
        with open(filename, encoding='utf-8') as source:
            text = source.read()
        if root is None:
            root = tmpl.Template.new(name)
        parsed = root if name == root.name else root.new_associated(name)
        parsed.parse(text)
    return check.not_none(root)


def parse_glob(pattern: str) -> tmpl.Template:
    return _parse_glob(None, pattern)


def _parse_glob(template: tmpl.Template | None, pattern: str) -> tmpl.Template:
    filenames = glob.glob(pattern)
    if not filenames:
        raise ValueError(f'template: pattern matches no files: {quote_go_string_or_raw(pattern)}')
    return _parse_files(template, filenames)
