import os.path


# TODO: wire into the om test harness - for now this is hardcoded to the local server started by run-mysql.
DATABASES = [
    {
        'host': '127.0.0.1',
        'port': 3306,
        'user': 'root',
        'passwd': 'om',
        'database': 'test1',
        'use_unicode': True,
        'local_infile': True,
    },
    {
        'host': '127.0.0.1',
        'port': 3306,
        'user': 'root',
        'passwd': 'om',
        'database': 'test2',
    },
]

# The server's CA certificate, for the SSL tests. TODO: wire into the om harness.
CA_PEM = os.path.expanduser('~/ca.pem')
