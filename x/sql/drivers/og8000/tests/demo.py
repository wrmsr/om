DATABASE = dict(
    host='127.0.0.1',
    port=35224,
    user='postgres',
    password='om',  # noqa
)


def run_native() -> None:
    from .. import native

    con = native.Connection(**DATABASE)

    con.run('CREATE TEMPORARY TABLE book (id SERIAL, title TEXT)')

    for title in ("Ender's Game", 'The Magus'):
        con.run('INSERT INTO book (title) VALUES (:title)', title=title)

    for row in con.run('SELECT * FROM book'):  # type: ignore
        print(row)

    con.close()


def run_dbapi() -> None:
    from .. import dbapi

    conn = dbapi.connect(**DATABASE)  # type: ignore
    cursor = conn.cursor()
    cursor.execute('CREATE TEMPORARY TABLE book (id SERIAL, title TEXT)')
    cursor.execute(
        'INSERT INTO book (title) VALUES (%s), (%s) RETURNING id, title',
        ("Ender's Game", 'Speaker for the Dead'),
    )
    results = cursor.fetchall()
    for row in results:
        id, title = row  # noqa
        print('id = %s, title = %s' % (id, title))  # noqa
    conn.commit()

    conn.close()


def _main() -> None:
    run_native()
    run_dbapi()


if __name__ == '__main__':
    _main()
