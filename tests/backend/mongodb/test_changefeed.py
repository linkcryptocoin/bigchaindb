from unittest import mock

import pytest

from multipipes import Pipe


@pytest.fixture
def mock_changefeed_data():
    return [
        {
            'op': 'i',
            'o': {'_id': '', 'msg': 'seems like we have an insert here'},
            'ts': 1,
        },
        {
            'op': 'd',
            'o': {'msg': 'seems like we have a delete here'},
            'ts': 2,
        },
        {
            'op': 'u',
            'o': {'msg': 'seems like we have an update here'},
            'o2': {'_id': 'some-id'},
            'ts': 3,
        },
    ]


@pytest.mark.bdb
@mock.patch('bigchaindb.backend.mongodb.changefeed._FEED_STOP', True)
@mock.patch('pymongo.cursor.Cursor.next')
def test_changefeed_insert(mock_cursor_next, mock_changefeed_data):
    from bigchaindb.backend import get_changefeed, connect
    from bigchaindb.backend.changefeed import ChangeFeed

    # setup connection and mocks
    conn = connect()
    # mock the `next` method of the cursor to return the mocked data
    mock_cursor_next.side_effect = [mock.DEFAULT] + mock_changefeed_data

    outpipe = Pipe()
    changefeed = get_changefeed(conn, 'backlog', ChangeFeed.INSERT)
    changefeed.outqueue = outpipe
    changefeed.run_forever()

    assert outpipe.get()['msg'] == 'seems like we have an insert here'
    assert outpipe.qsize() == 0


@pytest.mark.bdb
@mock.patch('bigchaindb.backend.mongodb.changefeed._FEED_STOP', True)
@mock.patch('pymongo.cursor.Cursor.next')
def test_changefeed_delete(mock_cursor_next, mock_changefeed_data):
    from bigchaindb.backend import get_changefeed, connect
    from bigchaindb.backend.changefeed import ChangeFeed

    conn = connect()
    mock_cursor_next.side_effect = [mock.DEFAULT] + mock_changefeed_data

    outpipe = Pipe()
    changefeed = get_changefeed(conn, 'backlog', ChangeFeed.DELETE)
    changefeed.outqueue = outpipe
    changefeed.run_forever()

    assert outpipe.get()['msg'] == 'seems like we have a delete here'
    assert outpipe.qsize() == 0


@pytest.mark.bdb
@mock.patch('bigchaindb.backend.mongodb.changefeed._FEED_STOP', True)
@mock.patch('pymongo.collection.Collection.find_one')
@mock.patch('pymongo.cursor.Cursor.next')
def test_changefeed_update(mock_cursor_next, mock_cursor_find_one,
                           mock_changefeed_data):
    from bigchaindb.backend import get_changefeed, connect
    from bigchaindb.backend.changefeed import ChangeFeed

    conn = connect()
    mock_cursor_next.side_effect = [mock.DEFAULT] + mock_changefeed_data
    mock_cursor_find_one.return_value = mock_changefeed_data[2]['o']

    outpipe = Pipe()
    changefeed = get_changefeed(conn, 'backlog', ChangeFeed.UPDATE)
    changefeed.outqueue = outpipe
    changefeed.run_forever()

    assert outpipe.get()['msg'] == 'seems like we have an update here'
    assert outpipe.qsize() == 0
    assert mock_cursor_find_one.called_once_with(
        {'_id': mock_changefeed_data[2]['o']},
        {'_id': False}
    )


@pytest.mark.bdb
@mock.patch('bigchaindb.backend.mongodb.changefeed._FEED_STOP', True)
@mock.patch('pymongo.collection.Collection.find_one')
@mock.patch('pymongo.cursor.Cursor.next')
def test_changefeed_multiple_operations(mock_cursor_next, mock_cursor_find_one,
                                        mock_changefeed_data):
    from bigchaindb.backend import get_changefeed, connect
    from bigchaindb.backend.changefeed import ChangeFeed

    conn = connect()
    mock_cursor_next.side_effect = [mock.DEFAULT] + mock_changefeed_data
    mock_cursor_find_one.return_value = mock_changefeed_data[2]['o']

    outpipe = Pipe()
    changefeed = get_changefeed(conn, 'backlog',
                                ChangeFeed.INSERT | ChangeFeed.UPDATE)
    changefeed.outqueue = outpipe
    changefeed.run_forever()

    assert outpipe.get()['msg'] == 'seems like we have an insert here'
    assert outpipe.get()['msg'] == 'seems like we have an update here'
    assert outpipe.qsize() == 0


@pytest.mark.bdb
@mock.patch('bigchaindb.backend.mongodb.changefeed._FEED_STOP', True)
@mock.patch('pymongo.cursor.Cursor.next')
def test_changefeed_prefeed(mock_cursor_next, mock_changefeed_data):
    from bigchaindb.backend import get_changefeed, connect
    from bigchaindb.backend.changefeed import ChangeFeed

    conn = connect()
    mock_cursor_next.side_effect = [mock.DEFAULT] + mock_changefeed_data

    outpipe = Pipe()
    changefeed = get_changefeed(conn, 'backlog', ChangeFeed.INSERT,
                                prefeed=[1, 2, 3])
    changefeed.outqueue = outpipe
    changefeed.run_forever()

    assert outpipe.qsize() == 4


@pytest.mark.bdb
def test_connection_failure():
    from bigchaindb.backend.exceptions import ConnectionError
    from bigchaindb.backend.mongodb.changefeed import run_changefeed

    conn = mock.MagicMock()
    conn.run.side_effect = [ConnectionError(), RuntimeError()]
    changefeed = run_changefeed(conn, 'backlog', -1)
    with pytest.raises(RuntimeError):
        for record in changefeed:
            assert False, 'Shouldn\'t get here'
