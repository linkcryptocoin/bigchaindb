import time
from unittest.mock import patch

import pytest

from bigchaindb.common import crypto
from multipipes import Pipe, Pipeline

from bigchaindb import Bigchain
from bigchaindb.pipelines import election


@pytest.mark.bdb
def test_check_for_quorum_invalid(b, user_pk):
    from bigchaindb.models import Transaction

    e = election.Election()

    # create blocks with transactions
    tx1 = Transaction.create([b.me], [([user_pk], 1)])
    tx1.sign([b.me_private])
    test_block = b.create_block([tx1])

    # simulate a federation with four voters
    key_pairs = [crypto.generate_key_pair() for _ in range(4)]
    test_federation = [Bigchain(public_key=key_pair[1], private_key=key_pair[0])
                       for key_pair in key_pairs]

    # add voters to block and write
    test_block.voters = [key_pair[1] for key_pair in key_pairs]
    test_block = test_block.sign(b.me_private)
    b.write_block(test_block)

    # split_vote (invalid)
    votes = [member.vote(test_block.id, 'a' * 64, True)
             for member in test_federation[:2]] + \
            [member.vote(test_block.id, 'b' * 64, False)
             for member in test_federation[2:]]

    # cast votes
    for vote in votes:
        b.write_vote(vote)

    # since this block is now invalid, should pass to the next process
    assert e.check_for_quorum(votes[-1]) == test_block


@pytest.mark.bdb
def test_check_for_quorum_invalid_prev_node(b, user_pk):
    from bigchaindb.models import Transaction
    e = election.Election()

    # create blocks with transactions
    tx1 = Transaction.create([b.me], [([user_pk], 1)])
    tx1.sign([b.me_private])
    test_block = b.create_block([tx1])

    # simulate a federation with four voters
    key_pairs = [crypto.generate_key_pair() for _ in range(4)]
    test_federation = [
        Bigchain(public_key=key_pair[1], private_key=key_pair[0])
        for key_pair in key_pairs
    ]

    # add voters to block and write
    test_block.voters = [key_pair[1] for key_pair in key_pairs]
    test_block = test_block.sign(b.me_private)
    b.write_block(test_block)

    # split vote over prev node
    votes = [member.vote(test_block.id, 'a' * 64, True)
             for member in test_federation[:2]] + \
            [member.vote(test_block.id, 'b' * 64, True)
             for member in test_federation[2:]]

    # cast votes
    for vote in votes:
        b.write_vote(vote)

    # since nodes cannot agree on prev block, the block is invalid
    assert e.check_for_quorum(votes[-1]) == test_block


@pytest.mark.bdb
def test_check_for_quorum_valid(b, user_pk):
    from bigchaindb.models import Transaction

    # simulate a federation with four voters
    key_pairs = [crypto.generate_key_pair() for _ in range(4)]
    test_federation = [
        Bigchain(public_key=key_pair[1], private_key=key_pair[0])
        for key_pair in key_pairs
    ]

    b.nodes_except_me = [key_pair[1] for key_pair in key_pairs]

    # create blocks with transactions
    tx1 = Transaction.create([b.me], [([user_pk], 1)])
    tx1.sign([b.me_private])
    test_block = b.create_block([tx1])

    # add voters to block and write
    test_block = test_block.sign(b.me_private)
    b.write_block(test_block)

    # votes for block one
    votes = [member.vote(test_block.id, 'a' * 64, True)
             for member in test_federation]
    # cast votes
    for vote in votes:
        b.write_vote(vote)

    e = election.Election()
    e.bigchain = b

    # since this block is valid, should go nowhere
    assert e.check_for_quorum(votes[-1]) is None


@patch('bigchaindb.core.Bigchain.get_block')
def test_invalid_vote(get_block, b):
    e = election.Election()
    assert e.check_for_quorum({}) is None
    get_block.assert_not_called()


@pytest.mark.bdb
def test_check_requeue_transaction(b, user_pk):
    from bigchaindb.models import Transaction

    e = election.Election()

    # create blocks with transactions
    tx1 = Transaction.create([b.me], [([user_pk], 1)])
    tx1.sign([b.me_private])
    test_block = b.create_block([tx1])

    e.requeue_transactions(test_block)

    time.sleep(1)
    backlog_tx, status = b.get_transaction(tx1.id, include_status=True)
    assert status == b.TX_IN_BACKLOG
    assert backlog_tx == tx1


@patch.object(Pipeline, 'start')
def test_start(mock_start):
    # TODO: `block.election` is just a wrapper around `block.create_pipeline`,
    #       that is tested by `test_full_pipeline`.
    #       If anyone has better ideas on how to test this, please do a PR :)
    election.start()
    mock_start.assert_called_with()


@pytest.mark.bdb
def test_full_pipeline(b, user_pk):
    import random
    from bigchaindb.backend import query
    from bigchaindb.models import Transaction

    outpipe = Pipe()

    # write two blocks
    txs = []
    for i in range(100):
        tx = Transaction.create([b.me], [([user_pk], 1)],
                                {'msg': random.random()})
        tx = tx.sign([b.me_private])
        txs.append(tx)

    valid_block = b.create_block(txs)
    b.write_block(valid_block)

    txs = []
    for i in range(100):
        tx = Transaction.create([b.me], [([user_pk], 1)],
                                {'msg': random.random()})
        tx = tx.sign([b.me_private])
        txs.append(tx)

    invalid_block = b.create_block(txs)
    b.write_block(invalid_block)

    pipeline = election.create_pipeline()
    pipeline.setup(indata=election.get_changefeed(), outdata=outpipe)
    pipeline.start()
    time.sleep(1)

    # vote one block valid, one invalid
    vote_valid = b.vote(valid_block.id, 'b' * 64, True)
    vote_invalid = b.vote(invalid_block.id, 'c' * 64, False)

    b.write_vote(vote_valid)
    b.write_vote(vote_invalid)

    outpipe.get()
    pipeline.terminate()

    # only transactions from the invalid block should be returned to
    # the backlog
    assert query.count_backlog(b.connection) == 100
    # NOTE: I'm still, I'm still tx from the block.
    tx_from_block = set([tx.id for tx in invalid_block.transactions])
    tx_from_backlog = set([tx['id'] for tx in list(query.get_stale_transactions(b.connection, 0))])
    assert tx_from_block == tx_from_backlog


def test_handle_block_events():
    from bigchaindb.events import Exchange, EventTypes

    exchange = Exchange()
    events_queue = exchange.get_publisher_queue()
    e = election.Election(events_queue=events_queue)
    block_id = 'a' * 64

    assert events_queue.qsize() == 0

    # no event should be emitted in case a block is undecided
    e.handle_block_events({'status': Bigchain.BLOCK_UNDECIDED}, block_id)
    assert events_queue.qsize() == 0

    # put an invalid block event in the queue
    e.handle_block_events({'status': Bigchain.BLOCK_INVALID}, block_id)
    event = events_queue.get()
    assert event.type == EventTypes.BLOCK_INVALID

    # put a valid block event in the queue
    e.handle_block_events({'status': Bigchain.BLOCK_VALID}, block_id)
    event = events_queue.get()
    assert event.type == EventTypes.BLOCK_VALID
