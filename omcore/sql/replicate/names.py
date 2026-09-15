"""
Everything replication owns in a database is named under `_orpl_`: a base table's shadow is `_orpl_<table>`, and
replication's own internal tables and trigger functions take the doubled-underscore `_orpl__` form.
"""
import typing as ta

from ..qualifiedname import QualifiedName


##


PREFIX: ta.Final[str] = '_orpl_'
INTERNAL_PREFIX: ta.Final[str] = PREFIX + '_'

NODE_TABLE_NAME: ta.Final[str] = INTERNAL_PREFIX + 'node'
CURSOR_TABLE_NAME: ta.Final[str] = INTERNAL_PREFIX + 'cursor'
LOG_TABLE_NAME: ta.Final[str] = INTERNAL_PREFIX + 'log'


def shadow_name(table: QualifiedName) -> QualifiedName:
    return table.sibling(PREFIX + table.last)


def node_table_name(qualifier: ta.Sequence[str]) -> QualifiedName:
    return QualifiedName((*qualifier, NODE_TABLE_NAME))


def cursor_table_name(qualifier: ta.Sequence[str]) -> QualifiedName:
    return QualifiedName((*qualifier, CURSOR_TABLE_NAME))


def log_table_name(qualifier: ta.Sequence[str]) -> QualifiedName:
    return QualifiedName((*qualifier, LOG_TABLE_NAME))


def capture_trigger_prefix(table: QualifiedName) -> str:
    return f'{PREFIX}{table.last}__capture__'


def capture_function_name(trigger_name: str) -> str:
    # For dialects whose triggers call a separate function object: a fixed rewrite of the trigger's own name, so a drop
    # that knows only the trigger name can find the function too.
    return trigger_name.replace('__capture__', '__capturefn__', 1)
