import pytest


pytestmark = pytest.mark.bdb


def test_init_creates_db_tables_and_indexes():
    import bigchaindb
    from bigchaindb import backend
    from bigchaindb.backend.schema import init_database

    conn = backend.connect()
    dbname = bigchaindb.config['database']['name']

    # the db is set up by the fixture so we need to remove it
    conn.conn.drop_database(dbname)

    init_database()

    collection_names = conn.conn[dbname].collection_names()
    assert sorted(collection_names) == ['assets', 'backlog', 'bigchain',
                                        'metadata', 'votes']

    indexes = conn.conn[dbname]['bigchain'].index_information().keys()
    assert sorted(indexes) == ['_id_', 'asset_id', 'block_id', 'block_timestamp',
                               'inputs', 'outputs', 'transaction_id']

    indexes = conn.conn[dbname]['backlog'].index_information().keys()
    assert sorted(indexes) == ['_id_', 'assignee__transaction_timestamp',
                               'transaction_id']

    indexes = conn.conn[dbname]['votes'].index_information().keys()
    assert sorted(indexes) == ['_id_', 'block_and_voter']

    indexes = conn.conn[dbname]['assets'].index_information().keys()
    assert sorted(indexes) == ['_id_', 'asset_id', 'text']

    indexes = conn.conn[dbname]['metadata'].index_information().keys()
    assert sorted(indexes) == ['_id_', 'text', 'transaction_id']


def test_init_database_fails_if_db_exists():
    import bigchaindb
    from bigchaindb import backend
    from bigchaindb.backend.schema import init_database
    from bigchaindb.common import exceptions

    conn = backend.connect()
    dbname = bigchaindb.config['database']['name']

    # The db is set up by the fixtures
    assert dbname in conn.conn.database_names()

    with pytest.raises(exceptions.DatabaseAlreadyExists):
        init_database()


def test_create_tables():
    import bigchaindb
    from bigchaindb import backend
    from bigchaindb.backend import schema

    conn = backend.connect()
    dbname = bigchaindb.config['database']['name']

    # The db is set up by the fixtures so we need to remove it
    conn.conn.drop_database(dbname)
    schema.create_database(conn, dbname)
    schema.create_tables(conn, dbname)

    collection_names = conn.conn[dbname].collection_names()
    assert sorted(collection_names) == ['assets', 'backlog', 'bigchain',
                                        'metadata', 'votes']


def test_create_secondary_indexes():
    import bigchaindb
    from bigchaindb import backend
    from bigchaindb.backend import schema

    conn = backend.connect()
    dbname = bigchaindb.config['database']['name']

    # The db is set up by the fixtures so we need to remove it
    conn.conn.drop_database(dbname)
    schema.create_database(conn, dbname)
    schema.create_tables(conn, dbname)
    schema.create_indexes(conn, dbname)

    # Bigchain table
    indexes = conn.conn[dbname]['bigchain'].index_information().keys()
    assert sorted(indexes) == ['_id_', 'asset_id', 'block_id', 'block_timestamp',
                               'inputs', 'outputs', 'transaction_id']

    # Backlog table
    indexes = conn.conn[dbname]['backlog'].index_information().keys()
    assert sorted(indexes) == ['_id_', 'assignee__transaction_timestamp',
                               'transaction_id']

    # Votes table
    indexes = conn.conn[dbname]['votes'].index_information().keys()
    assert sorted(indexes) == ['_id_', 'block_and_voter']


def test_drop(dummy_db):
    from bigchaindb import backend
    from bigchaindb.backend import schema

    conn = backend.connect()
    assert dummy_db in conn.conn.database_names()
    schema.drop_database(conn, dummy_db)
    assert dummy_db not in conn.conn.database_names()
