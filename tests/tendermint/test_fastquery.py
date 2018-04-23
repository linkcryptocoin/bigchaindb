import pytest

from bigchaindb.common.transaction import TransactionLink
from bigchaindb.models import Transaction

pytestmark = [pytest.mark.bdb, pytest.mark.tendermint]


@pytest.fixture
def txns(b, user_pk, user_sk, user2_pk, user2_sk):
    txs = [Transaction.create([user_pk], [([user2_pk], 1)]).sign([user_sk]),
           Transaction.create([user2_pk], [([user_pk], 1)]).sign([user2_sk]),
           Transaction.create([user_pk], [([user_pk], 1), ([user2_pk], 1)])
           .sign([user_sk])]
    b.store_bulk_transactions(txs)
    return txs


def test_get_outputs_by_public_key(b, user_pk, user2_pk, txns):
    assert b.fastquery.get_outputs_by_public_key(user_pk) == [
        TransactionLink(txns[1].id, 0),
        TransactionLink(txns[2].id, 0)
    ]
    assert b.fastquery.get_outputs_by_public_key(user2_pk) == [
        TransactionLink(txns[0].id, 0),
        TransactionLink(txns[2].id, 1),
    ]
