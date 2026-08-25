CREATE_TEMP_TABLE_SQL = """ \
CREATE TEMPORARY TABLE `users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `email` varchar(255) COLLATE utf8_bin NOT NULL,
  `password` varchar(255) COLLATE utf8_bin NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_bin
  AUTO_INCREMENT=1; \
"""


def _main() -> None:
    from ... import omysql

    connection = omysql.Connection(
        host='127.0.0.1',
        port=35225,
        user='root',
        password='om',  # noqa
        database='om',
    )

    with connection:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_TEMP_TABLE_SQL)

        with connection.cursor() as cursor:
            # Create a new record
            sql = 'INSERT INTO `users` (`email`, `password`) VALUES (%s, %s)'
            cursor.execute(sql, ('webmaster@python.org', 'very-secret'))

        # connection is not autocommit by default. So you must commit to save
        # your changes.
        connection.commit()

        with connection.cursor() as cursor:
            # Read a single record
            sql = 'SELECT `id`, `password` FROM `users` WHERE `email`=%s'
            cursor.execute(sql, ('webmaster@python.org',))
            result = cursor.fetchone()
            print(result)


if __name__ == '__main__':
    _main()
