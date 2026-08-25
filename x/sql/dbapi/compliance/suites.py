# ruff: noqa: S101 S608
"""
A DB-API 2.0 (PEP 249) compliance suite, written against the spec and omcore's Dbapi* protocols rather than any one
driver. A driver binds it by subclassing DbapiComplianceSuite in a test module of its own:

    class TestDbapiCompliance(DbapiComplianceSuite):
        BINDING = DbapiComplianceBinding(module=mydriver, connect=lambda: mydriver.connect(...))

The mixins group the checks by area; none is collected on its own.
"""
import abc
import datetime
import decimal
import time
import typing as ta

import pytest

from omcore.sql.dbapi.abc import DbapiConnection
from omcore.sql.dbapi.abc import DbapiCursor
from omcore.sql.dbapi.abc import DbapiModule

from .bindings import DbapiComplianceBinding


##


class DbapiComplianceBase:
    @abc.abstractmethod
    def binding(self) -> DbapiComplianceBinding:
        raise NotImplementedError

    @property
    def b(self) -> DbapiComplianceBinding:
        return self.binding()

    @property
    def m(self) -> ta.Any:
        return self.binding().module

    def connect(self):
        return self.b.closing(self.b.connect())

    def insert_names(self, con, table, names, *, commit=False):
        cur = con.cursor()
        ph = self.b.placeholder(0, 'name')
        cur.executemany(f'insert into {table} values ({ph})', [self.b.params(['name'], [n]) for n in names])
        if commit:
            con.commit()
        return cur

    @staticmethod
    def select_names(con, table):
        cur = con.cursor()
        cur.execute(f'select name from {table} order by name')
        return [r[0] for r in cur.fetchall()]


##


class ModuleComplianceMixin(DbapiComplianceBase):
    def test_apilevel(self):
        assert self.m.apilevel == '2.0'

    def test_threadsafety(self):
        assert self.m.threadsafety in (0, 1, 2, 3)

    def test_paramstyle(self):
        assert self.m.paramstyle in ('qmark', 'numeric', 'named', 'format', 'pyformat')

    def test_connect(self):
        with self.connect() as con:
            assert con is not None

    def test_exception_hierarchy(self):
        m = self.m
        assert issubclass(m.Warning, Exception)
        assert issubclass(m.Error, Exception)
        assert not issubclass(m.Warning, m.Error)
        assert issubclass(m.InterfaceError, m.Error)
        assert issubclass(m.DatabaseError, m.Error)
        for name in ('DataError', 'OperationalError', 'IntegrityError', 'InternalError', 'ProgrammingError', 'NotSupportedError'):  # noqa: E501
            assert issubclass(getattr(m, name), m.DatabaseError), name

    def test_module_protocol_members(self):
        missing = [n for n in ta.get_protocol_members(DbapiModule) if not hasattr(self.m, n)]
        assert not missing

    def test_connection_protocol_members(self):
        with self.connect() as con:
            missing = [n for n in ta.get_protocol_members(DbapiConnection) if not hasattr(con, n)]
        assert not missing

    def test_cursor_protocol_members(self):
        with self.connect() as con:
            cur = con.cursor()
            missing = [n for n in ta.get_protocol_members(DbapiCursor) if not hasattr(cur, n)]
        assert not missing


##


class TypeComplianceMixin(DbapiComplianceBase):
    def test_type_constructors(self):
        m = self.m
        m.Date(2020, 1, 2)
        m.Time(3, 4, 5)
        m.Timestamp(2020, 1, 2, 3, 4, 5)
        ticks = time.mktime((2020, 1, 2, 3, 4, 5, 0, 0, -1))
        assert m.DateFromTicks(ticks) == m.Date(2020, 1, 2)
        assert m.TimeFromTicks(ticks) == m.Time(3, 4, 5)
        assert m.TimestampFromTicks(ticks) == m.Timestamp(2020, 1, 2, 3, 4, 5)
        m.Binary(b'')
        m.Binary(b'\x00\x01\xff')

    def test_type_objects_exist(self):
        for name in ('STRING', 'BINARY', 'NUMBER', 'DATETIME', 'ROWID'):
            assert hasattr(self.m, name), name

    @pytest.mark.parametrize(
        ('type_object', 'column_type_attr'),
        [
            ('STRING', 'varchar_type'),
            ('NUMBER', 'numeric_type'),
            ('DATETIME', 'timestamp_type'),
            ('BINARY', 'binary_type'),
        ],
    )
    def test_type_objects_match_description(self, type_object, column_type_attr):
        """Type objects must compare equal to the description type codes of columns of their kind."""

        with self.connect() as con, self.b.table(con, 'types', f'(v {getattr(self.b, column_type_attr)})') as t:
            cur = con.cursor()
            cur.execute(f'select v from {t}')
            type_code = cur.description[0][1]
            assert type_code == getattr(self.m, type_object)


##


class ConnectionComplianceMixin(DbapiComplianceBase):
    def test_commit_and_rollback_on_fresh_connection(self):
        with self.connect() as con:
            con.commit()
            con.rollback()

    def test_cursor(self):
        with self.connect() as con:
            cur = con.cursor()
            assert cur is not None
            cur.close()

    def test_close(self):
        con = self.b.connect()
        cur = con.cursor()
        con.close()

        with pytest.raises(self.m.Error):
            cur.execute('select 1')
        with pytest.raises(self.m.Error):
            con.commit()
        with pytest.raises(self.m.Error):
            con.close()

    def test_exceptions_as_connection_attributes(self):
        """An optional extension; if any one is present they all must be, and they must be the module's classes."""

        with self.connect() as con:
            if not hasattr(con, 'Error'):
                pytest.skip('connection exception attributes extension not implemented')

            for name in (
                    'Warning', 'Error', 'InterfaceError', 'DatabaseError', 'DataError', 'OperationalError',
                    'IntegrityError', 'InternalError', 'ProgrammingError', 'NotSupportedError',
            ):
                assert getattr(con, name) is getattr(self.m, name), name

    def test_cursors_on_one_connection_share_a_transaction(self):
        with self.connect() as con, self.b.table(con, 'booze', '(name varchar(20))') as t:
            cur1 = con.cursor()
            cur2 = con.cursor()
            cur1.execute(f"insert into {t} values ('Victoria Bitter')")
            cur2.execute(f'select name from {t}')
            assert [r[0] for r in cur2.fetchall()] == ['Victoria Bitter']

    def test_uncommitted_work_is_invisible_to_other_connections(self):
        with self.connect() as con1, self.b.table(con1, 'iso', '(name varchar(20))') as t, self.connect() as con2:
            self.insert_names(con1, t, ['a'])
            assert self.select_names(con2, t) == []
            con1.commit()
            con2.rollback()  # Leave any snapshot behind.
            assert self.select_names(con2, t) == ['a']

    def test_rollback_discards_work(self):
        with self.connect() as con, self.b.table(con, 'rb', '(name varchar(20))') as t:
            self.insert_names(con, t, ['a', 'b'])
            assert self.select_names(con, t) == ['a', 'b']
            con.rollback()
            assert self.select_names(con, t) == []

    def test_commit_persists_work(self):
        with self.connect() as con, self.b.table(con, 'cm', '(name varchar(20))') as t:
            self.insert_names(con, t, ['a', 'b'], commit=True)
            with self.connect() as con2:
                assert self.select_names(con2, t) == ['a', 'b']

    def test_closing_a_cursor_does_not_close_the_connection(self):
        with self.connect() as con:
            cur = con.cursor()
            cur.close()
            cur2 = con.cursor()
            cur2.execute('select 1')
            assert cur2.fetchone()[0] == 1


##


class CursorComplianceMixin(DbapiComplianceBase):
    def test_description(self):
        with self.connect() as con, self.b.table(con, 'desc', f'(name {self.b.varchar_type})') as t:
            cur = con.cursor()
            before = cur.description
            assert before is None

            cur.execute(f'select name from {t}')
            desc = cur.description
            assert len(desc) == 1
            assert len(desc[0]) == 7
            assert desc[0][0].lower() == 'name'
            assert desc[0][1] == self.m.STRING

            cur.execute(f'insert into {t} values (\'x\')')
            after = cur.description
            assert after is None

    def test_rowcount(self):
        with self.connect() as con, self.b.table(con, 'rc', '(name varchar(20))') as t:
            cur = con.cursor()
            assert cur.rowcount == -1

            cur.execute(f"insert into {t} values ('a')")
            assert cur.rowcount in (-1, 1)
            cur.execute(f"insert into {t} values ('b')")
            assert cur.rowcount in (-1, 1)
            cur.execute(f"update {t} set name = 'c'")
            assert cur.rowcount in (-1, 2)
            cur.execute(f'delete from {t}')
            assert cur.rowcount in (-1, 2)

            cur.execute(f'select name from {t}')
            assert cur.rowcount in (-1, 0)

    def test_closed_cursor(self):
        with self.connect() as con:
            cur = con.cursor()
            cur.close()
            with pytest.raises(self.m.Error):
                cur.execute('select 1')

    def test_execute_with_parameters(self):
        with self.connect() as con, self.b.table(con, 'params', '(name varchar(20))') as t:
            cur = con.cursor()
            cur.execute(f"insert into {t} values ('Victoria Bitter')")
            assert cur.rowcount in (-1, 1)

            ph = self.b.placeholder(0, 'beer')
            cur.execute(f'insert into {t} values ({ph})', self.b.params(['beer'], ["Cooper's"]))
            assert cur.rowcount in (-1, 1)

            assert self.select_names(con, t) == ["Cooper's", 'Victoria Bitter']

    def test_executemany(self):
        with self.connect() as con, self.b.table(con, 'many', '(name varchar(20))') as t:
            cur = con.cursor()
            ph = self.b.placeholder(0, 'beer')
            largs = [self.b.params(['beer'], [n]) for n in ("Cooper's", "Boag's")]
            cur.executemany(f'insert into {t} values ({ph})', largs)
            assert cur.rowcount in (-1, 2)
            assert self.select_names(con, t) == ["Boag's", "Cooper's"]

    def test_executemany_with_no_parameter_sets(self):
        with self.connect() as con, self.b.table(con, 'many0', '(name varchar(20))') as t:
            cur = con.cursor()
            ph = self.b.placeholder(0, 'beer')
            cur.executemany(f'insert into {t} values ({ph})', [])
            assert self.select_names(con, t) == []

    def test_fetchone(self):
        with self.connect() as con, self.b.table(con, 'f1', '(name varchar(20))') as t:
            cur = con.cursor()
            with pytest.raises(self.m.Error):
                cur.fetchone()

            cur.execute(f"insert into {t} values ('Victoria Bitter')")
            if self.b.strict_fetch_without_result:
                with pytest.raises(self.m.Error):
                    cur.fetchone()

            cur.execute(f"select name from {t} where name = 'nope'")
            assert cur.fetchone() is None
            assert cur.rowcount in (-1, 0)

            cur.execute(f'select name from {t}')
            row = cur.fetchone()
            assert len(row) == 1
            assert row[0] == 'Victoria Bitter'
            assert cur.fetchone() is None
            assert cur.rowcount in (-1, 1)

    def test_fetchmany(self):
        names = sorted(['Carlton Cold', 'Carlton Draft', 'Mountain Goat', 'Redback', 'Victoria Bitter', 'XXXX'])
        with self.connect() as con, self.b.table(con, 'fm', '(name varchar(20))') as t:
            cur = con.cursor()
            with pytest.raises(self.m.Error):
                cur.fetchmany(4)

            self.insert_names(con, t, names)

            cur.execute(f'select name from {t} order by name')
            r = cur.fetchmany()
            assert len(r) == 1
            assert r[0][0] == names[0]
            cur.arraysize = 10
            assert [x[0] for x in cur.fetchmany()] == names[1:]
            assert len(cur.fetchmany()) == 0
            assert cur.rowcount in (-1, 6)

            cur.arraysize = 4
            cur.execute(f'select name from {t} order by name')
            assert [x[0] for x in cur.fetchmany()] == names[:4]
            assert [x[0] for x in cur.fetchmany()] == names[4:]
            assert len(cur.fetchmany()) == 0
            assert cur.rowcount in (-1, 6)

            cur.arraysize = 6
            cur.execute(f'select name from {t} order by name')
            assert [x[0] for x in cur.fetchmany(2)] == names[:2]
            assert [x[0] for x in cur.fetchmany(100)] == names[2:]
            assert len(cur.fetchmany()) == 0

            cur.execute(f"select name from {t} where name = 'nope'")
            assert len(cur.fetchmany()) == 0
            assert len(cur.fetchmany()) == 0

    def test_fetchall(self):
        names = sorted(['Carlton Cold', 'Carlton Draft', 'Mountain Goat'])
        with self.connect() as con, self.b.table(con, 'fa', '(name varchar(20))') as t:
            cur = con.cursor()
            with pytest.raises(self.m.Error):
                cur.fetchall()

            self.insert_names(con, t, names)
            cur.execute(f"insert into {t} values ('z')")
            if self.b.strict_fetch_without_result:
                with pytest.raises(self.m.Error):
                    cur.fetchall()

            cur.execute(f"delete from {t} where name = 'z'")
            cur.execute(f'select name from {t} order by name')
            assert [x[0] for x in cur.fetchall()] == names
            assert len(cur.fetchall()) == 0
            assert cur.rowcount in (-1, 3)

            cur.execute(f"select name from {t} where name = 'nope'")
            assert len(cur.fetchall()) == 0
            assert cur.rowcount in (-1, 0)

    def test_mixed_fetching(self):
        names = sorted(['Carlton Cold', 'Carlton Draft', 'Mountain Goat', 'Redback', 'Victoria Bitter', 'XXXX'])
        with self.connect() as con, self.b.table(con, 'mf', '(name varchar(20))') as t:
            self.insert_names(con, t, names)
            cur = con.cursor()
            cur.execute(f'select name from {t} order by name')
            rows1 = [cur.fetchone()]
            rows2 = cur.fetchmany(2)
            rows3 = cur.fetchone()
            rows4 = cur.fetchall()
            assert [r[0] for r in [*rows1, *rows2, rows3, *rows4]] == names
            assert cur.rowcount in (-1, 6)

    def test_iteration_extension(self):
        with self.connect() as con, self.b.table(con, 'it', '(name varchar(20))') as t:
            self.insert_names(con, t, ['a', 'b'])
            cur = con.cursor()
            if not hasattr(cur, '__iter__'):
                pytest.skip('cursor iteration extension not implemented')
            cur.execute(f'select name from {t} order by name')
            assert [r[0] for r in cur] == ['a', 'b']

    def test_arraysize(self):
        with self.connect() as con:
            cur = con.cursor()
            assert cur.arraysize == 1
            cur.arraysize = 10
            assert cur.arraysize == 10

    def test_setinputsizes_and_setoutputsize(self):
        with self.connect() as con:
            cur = con.cursor()
            cur.setinputsizes([25])
            cur.setinputsizes([self.m.STRING])
            cur.setoutputsize(1000)
            cur.setoutputsize(1000, 0)
            ph = self.b.placeholder(0, 'v')
            cur.execute(f'select {ph}', self.b.params(['v'], ['x']))
            assert cur.fetchone()[0] == 'x'

    def test_nextset(self):
        with self.connect() as con:
            cur = con.cursor()
            if not hasattr(cur, 'nextset'):
                pytest.skip('nextset not implemented')
            cur.execute('select 1')
            cur.fetchall()
            try:
                assert cur.nextset() is None
            except self.m.NotSupportedError:
                pytest.skip('nextset not supported')

    def test_callproc(self):
        if (name := self.b.callproc_name) is None:
            pytest.skip('no callproc procedure configured')

        with self.connect() as con:
            cur = con.cursor()
            if not hasattr(cur, 'callproc'):
                pytest.skip('callproc not implemented')
            result = cur.callproc(name)
            assert result is None or isinstance(result, (list, tuple))


##


class OperationalComplianceMixin(DbapiComplianceBase):
    def round_trip(self, column_type, value, *, names=('v',)):
        with self.connect() as con, self.b.table(con, 'rt', f'(v {column_type})') as t:
            cur = con.cursor()
            ph = self.b.placeholder(0, 'v')
            cur.execute(f'insert into {t} values ({ph})', self.b.params(list(names), [value]))
            cur.execute(f'select v from {t}')
            return cur.fetchone()[0]

    def test_none_round_trip(self):
        assert self.round_trip(self.b.varchar_type, None) is None

    def test_unicode_round_trip(self):
        assert self.round_trip(self.b.varchar_type, 'hello ų wörld \U0001f37a') == 'hello ų wörld \U0001f37a'

    def test_empty_string_round_trip(self):
        assert self.round_trip(self.b.varchar_type, '') == ''

    @pytest.mark.parametrize(
        'value',
        [
            "it's",
            'back\\slash',
            '100%',
            'semi;colon',
            'new\nline',
            '"double" quotes',
            '%(pyformat)s and %s and ? and :named and :1',
        ],
    )
    def test_parameter_escaping(self, value):
        assert self.round_trip(self.b.varchar_type, value) == value

    def test_integer_round_trip(self):
        assert self.round_trip(self.b.integer_type, 42) == 42
        assert self.round_trip(self.b.integer_type, -7) == -7

    def test_numeric_round_trip(self):
        v = self.round_trip(self.b.numeric_type, decimal.Decimal('1234.567'))
        assert decimal.Decimal(str(v)) == decimal.Decimal('1234.567')

    def test_float_round_trip(self):
        assert self.round_trip(self.b.float_type, 1.5) == 1.5

    def test_binary_round_trip(self):
        data = b'\x00\x01\x02\xff\xfe'
        v = self.round_trip(self.b.binary_type, self.m.Binary(data))
        assert bytes(v) == data

    def test_date_round_trip(self):
        assert self.round_trip(self.b.date_type, self.m.Date(2020, 2, 29)) == datetime.date(2020, 2, 29)

    def test_time_round_trip(self):
        v = self.round_trip(self.b.time_type, self.m.Time(23, 59, 58))
        if self.b.time_is_timedelta:
            assert v == datetime.timedelta(hours=23, minutes=59, seconds=58)
        else:
            assert v == datetime.time(23, 59, 58)

    def test_timestamp_round_trip(self):
        ts = self.round_trip(self.b.timestamp_type, self.m.Timestamp(2020, 2, 29, 23, 59, 58))
        assert ts == datetime.datetime(2020, 2, 29, 23, 59, 58)  # noqa: DTZ001

    def test_literal_percent_in_sql_with_parameters(self):
        """A literal percent sign (here the modulo operator) must be expressible alongside parameters."""

        with self.connect() as con:
            cur = con.cursor()
            sql = self.b.escape_percent('select 7 % {ph}').format(ph=self.b.placeholder(0, 'v'))
            cur.execute(sql, self.b.params(['v'], [3]))
            assert cur.fetchone()[0] == 1

    def test_bulk_executemany_and_fetchmany(self):
        n = 1000
        with self.connect() as con, self.b.table(con, 'bulk', f'(i {self.b.integer_type}, name varchar(20))') as t:
            cur = con.cursor()
            ph = self.b.placeholders(['i', 'name'])
            cur.executemany(
                f'insert into {t} values ({ph[0]}, {ph[1]})',
                [self.b.params(['i', 'name'], [i, f'name{i}']) for i in range(n)],
            )
            assert cur.rowcount in (-1, n)

            cur.execute(f'select i, name from {t} order by i')
            seen = []
            cur.arraysize = 64
            while (rows := cur.fetchmany()):
                seen.extend(rows)
            assert [r[0] for r in seen] == list(range(n))
            assert seen[-1][1] == f'name{n - 1}'

    def test_database_error_leaves_connection_usable(self):
        with self.connect() as con:
            cur = con.cursor()
            with pytest.raises(self.m.DatabaseError):
                cur.execute('select * from this_table_does_not_exist_dbapi_compliance')
            con.rollback()
            cur.execute('select 1')
            assert cur.fetchone()[0] == 1

    def test_rollback_after_error_in_transaction(self):
        with self.connect() as con, self.b.table(con, 'txerr', '(name varchar(20))') as t:
            self.insert_names(con, t, ['a'], commit=True)
            cur = con.cursor()
            cur.execute(f"insert into {t} values ('b')")
            with pytest.raises(self.m.DatabaseError):
                cur.execute('select * from this_table_does_not_exist_dbapi_compliance')
            con.rollback()
            assert self.select_names(con, t) == ['a']

    def test_many_cursors(self):
        with self.connect() as con:
            cursors = [con.cursor() for _ in range(50)]
            for i, cur in enumerate(cursors):
                ph = self.b.placeholder(0, 'i')
                cur.execute(f'select {ph}', self.b.params(['i'], [str(i)]))
            assert [cur.fetchone()[0] for cur in cursors] == [str(i) for i in range(50)]

    def test_lower_func(self):
        with self.connect() as con:
            cur = con.cursor()
            ph = self.b.placeholder(0, 'v')
            cur.execute(f'select {self.b.lower_func}({ph})', self.b.params(['v'], ['FOO']))
            assert cur.fetchone()[0] == 'foo'


##


class DbapiComplianceSuite(
    ModuleComplianceMixin,
    TypeComplianceMixin,
    ConnectionComplianceMixin,
    CursorComplianceMixin,
    OperationalComplianceMixin,
):
    pass
