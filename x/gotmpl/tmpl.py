"""
https://github.com/golang/go/blob/3d33437c450aa74014ea1d41cd986b6ee6266984/src/text/template/template.go
"""
# Copyright 2009 The Go Authors.
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
import dataclasses as dc
import enum
import typing as ta

from .parse import Tree
from .parse import parse
from .parse import is_empty_tree


class MissingKeyAction(enum.Enum):
    INVALID = enum.auto()     # Return an invalid reflect.Value.
    ZERO_VALUE = enum.auto()  # Return the zero value for the map element.
    ERROR = enum.auto()       # Error out


@dc.dataclass()
class Option:
    missing_key: MissingKeyAction = MissingKeyAction.INVALID


FuncMap: ta.TypeAlias = dict[str, ta.Callable]


# common holds the information shared by related templates.
@dc.dataclass(kw_only=True)
class Common:
    tmpl: dict[str, 'Template'] = dc.field(default_factory=dict)  # Map from name to defined templates.
    option: Option = Option()
    # We use two maps, one for parsing and one for execution. This separation makes the API cleaner since it doesn't
    # expose reflection to the client.
    parse_funcs: FuncMap = dc.field(default_factory=dict)
    exec_funcs: dict[str, ta.Callable] = dc.field(default_factory=dict)


# Template is the representation of a parsed template. The *parse.Tree field is exported only for use by [html/template]
# and should be treated as unexported by all other clients.
class Template:
    def __init__(
            self,
            name: str,
            *,
            common: Common | None = None,
            tree: Tree | None = None,
            left_delim: str = '',
            right_delim: str = '',
    ) -> None:
        super().__init__()

        self._name = name
        self._common = common
        self._tree = tree
        self._left_delim = left_delim
        self._right_delim = right_delim

    # New allocates a new, undefined template with the given name.
    @classmethod
    def new(cls, name: str) -> 'Template':
        t = cls(name)
        t._init()
        return t

    # Name returns the name of the template.
    @property
    def name(self) -> str:
        return self._name

    @property
    def tree(self) -> Tree | None:
        return self._tree

    # init guarantees that t has a valid common structure.
    def _init(self) -> None:
        if self._common is None:
            self._common = Common()

    # New allocates a new, undefined template associated with the given one and with the same delimiters. The
    # association, which is transitive, allows one template to invoke another with a {{template}} action.
    #
    # Because associated templates share underlying data, template construction cannot be done safely in parallel. Once
    # the templates are constructed, they can be executed in parallel.
    def _new(self, name: str) -> 'Template':
        self._init()
        nt = Template(
            name=name,
            common=self._common,
            left_delim=self._left_delim,
            right_delim=self._right_delim,
        )
        return nt

    # Clone returns a duplicate of the template, including all associated templates. The actual representation is not
    # copied, but the name space of associated templates is, so further calls to [Template.Parse] in the copy will add
    # templates to the copy but not to the original. Clone can be used to prepare common templates and use them with
    # variant definitions for other templates by adding the variants after the clone is made.
    def clone(self) -> 'Template':
        nt = self.copy(None)
        nt._init()
        if self._common is None:
            return nt
        for k, v in self._common.tmpl.items():
            if k == self.name:
                nt._common.tmpl[self._name] = nt
                continue
            # The associated templates share nt's common structure.
            tmpl = v.copy(nt._common)
            nt._common.tmpl[k] = tmpl
        for k, v in self._common.parse_funcs.items():
            nt._common.parse_funcs[k] = v
        for k, v in self._common.exec_funcs.items():
            nt._common.exec_funcs[k] = v
        return nt

    # copy returns a shallow copy of t, with common set to the argument.
    def copy(self, c: Common | None) -> 'Template':
        return Template(
            name=self._name,
            tree=self._tree,
            common=c,
            left_delim=self._left_delim,
            right_delim=self._right_delim,
        )

    # AddParseTree associates the argument parse tree with the template t, giving it the specified name. If the template
    # has not been defined, this tree becomes its definition. If it has been defined and already has that name, the
    # existing definition is replaced; otherwise a new template is created, defined, and returned.
    def add_parse_tree(self, name: str, tree: Tree) -> 'Template':
        self._init()
        nt = self
        if name != self._name:
            nt = self._new(name)
        # Even if nt == t, we need to install it in the common.tmpl map.
        if self.associate(nt, tree) or nt._tree is None:
            nt._tree = tree
        return nt

    # Templates returns a slice of defined templates associated with t.
    def templates(self) -> list['Template'] | None:
        if self._common is None:
            return None
        # Return a slice so we don't expose the map.
        return list(self._common.tmpl.values())

    # Delims sets the action delimiters to the specified strings, to be used in subsequent calls to [Template.Parse],
    # [Template.ParseFiles], or [Template.ParseGlob]. Nested template definitions will inherit the settings. An empty
    # delimiter stands for the corresponding default: {{ or }}.
    # The return value is the template, so calls can be chained.
    def delims(self, left: str, right: str) -> 'Template':
        self._init()
        self._left_delim = left
        self._right_delim = right
        return self

    # Funcs adds the elements of the argument map to the template's function map.
    # It must be called before the template is parsed.
    # It panics if a value in the map is not a function with appropriate return type or if the name cannot be used
    # syntactically as a function in a template.
    # It is legal to overwrite elements of the map. The return value is the template, so calls can be chained.
    def funcs(self, func_map: FuncMap) -> 'Template':
        self._init()
        add_value_funcs(self._common.exec_funcs, func_map)
        add_funcs(self._common.parse_funcs, func_map)
        return self

    # Lookup returns the template with the given name that is associated with t.
    # It returns nil if there is no such template or the template has no definition.
    def lookup(self, name: str) -> ta.Optional['Template']:
        if self._common is None:
            return None
        return self._common.tmpl.get(name)

    # Parse parses text as a template body for t.
    # Named template definitions ({{define ...}} or {{block ...}} statements) in text define additional templates
    # associated with t and are removed from the definition of t itself.
    #
    # Templates can be redefined in successive calls to Parse.
    # A template definition with a body containing only white space and comments is considered empty and will not
    # replace an existing template's body.
    # This allows using Parse to add new named template definitions without overwriting the main template body.
    def parse(self, text: str) -> 'Template':
        self._init()
        trees = parse(self._name, text, self._left_delim, self._right_delim, self._common.parse_funcs, builtins())
        # Add the newly parsed trees, including the one for t, into our common structure.
        for name, tree in trees.items():
            self.add_parse_tree(name, tree)
        return self

    # associate installs the new template into the group of templates associated with t. The two are already known to
    # share the common structure.
    # The boolean return value reports whether to store this tree as t.Tree.
    def associate(self, new: 'Template', tree: Tree) -> bool:
        if new._common is not self._common:
            raise RuntimeError("internal error: associate not common")
        if (old := self._common.tmpl.get(new.name)) is not None and is_empty_tree(tree.root) and old._tree is not None:
            # If a template by that name exists, don't replace it with an empty template.
            return False
        self._common.tmpl[new.name] = new
        return True
