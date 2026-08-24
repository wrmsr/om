import os.path


# TODO: wire into the om test harness - for now this is hardcoded to the local server started by run-mysql. The
# databases themselves are created by the session bootstrap fixture, using these root credentials.
DATABASES = [
    {
        'host': '127.0.0.1',
        'port': 3306,
        'user': 'root',
        'passwd': 'om',
        'database': 'test_omysql_1',
        'use_unicode': True,
        'local_infile': True,
    },
    {
        'host': '127.0.0.1',
        'port': 3306,
        'user': 'root',
        'passwd': 'om',
        'database': 'test_omysql_2',
    },
]

# The server's CA certificate, for the SSL tests. TODO: wire into the om harness.
CA_PEM = os.path.expanduser('~/ca.pem')
