def _main() -> None:
    from .. import native

    con = native.Connection('postgres', '127.0.0.1', port=35224, password='om')

    con.run('CREATE TEMPORARY TABLE book (id SERIAL, title TEXT)')

    for title in ("Ender's Game", 'The Magus'):
        con.run('INSERT INTO book (title) VALUES (:title)', title=title)

    for row in con.run('SELECT * FROM book'):
        print(row)

    con.close()


if __name__ == '__main__':
    _main()
