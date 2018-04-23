import pytest


# CREATE divisible asset
# Single input
# Single owners_before
# Single output
# Single owners_after
def test_single_in_single_own_single_out_single_own_create(b, user_pk):
    from bigchaindb.models import Transaction

    tx = Transaction.create([b.me], [([user_pk], 100)])
    tx_signed = tx.sign([b.me_private])

    assert tx_signed.validate(b) == tx_signed
    assert len(tx_signed.outputs) == 1
    assert tx_signed.outputs[0].amount == 100
    assert len(tx_signed.inputs) == 1


# CREATE divisible asset
# Single input
# Single owners_before
# Multiple outputs
# Single owners_after per output
def test_single_in_single_own_multiple_out_single_own_create(b, user_pk):
    from bigchaindb.models import Transaction

    tx = Transaction.create([b.me], [([user_pk], 50), ([user_pk], 50)])
    tx_signed = tx.sign([b.me_private])

    assert tx_signed.validate(b) == tx_signed
    assert len(tx_signed.outputs) == 2
    assert tx_signed.outputs[0].amount == 50
    assert tx_signed.outputs[1].amount == 50
    assert len(tx_signed.inputs) == 1


# CREATE divisible asset
# Single input
# Single owners_before
# Single output
# Multiple owners_after
def test_single_in_single_own_single_out_multiple_own_create(b, user_pk):
    from bigchaindb.models import Transaction

    tx = Transaction.create([b.me], [([user_pk, user_pk], 100)])
    tx_signed = tx.sign([b.me_private])

    assert tx_signed.validate(b) == tx_signed
    assert len(tx_signed.outputs) == 1
    assert tx_signed.outputs[0].amount == 100

    output = tx_signed.outputs[0].to_dict()
    assert 'subconditions' in output['condition']['details']
    assert len(output['condition']['details']['subconditions']) == 2

    assert len(tx_signed.inputs) == 1


# CREATE divisible asset
# Single input
# Single owners_before
# Multiple outputs
# Mix: one output with a single owners_after, one output with multiple
#      owners_after
def test_single_in_single_own_multiple_out_mix_own_create(b, user_pk):
    from bigchaindb.models import Transaction

    tx = Transaction.create([b.me], [([user_pk], 50), ([user_pk, user_pk], 50)])
    tx_signed = tx.sign([b.me_private])

    assert tx_signed.validate(b) == tx_signed
    assert len(tx_signed.outputs) == 2
    assert tx_signed.outputs[0].amount == 50
    assert tx_signed.outputs[1].amount == 50

    output_cid1 = tx_signed.outputs[1].to_dict()
    assert 'subconditions' in output_cid1['condition']['details']
    assert len(output_cid1['condition']['details']['subconditions']) == 2

    assert len(tx_signed.inputs) == 1


# CREATE divisible asset
# Single input
# Multiple owners_before
# Output combinations already tested above
def test_single_in_multiple_own_single_out_single_own_create(b, user_pk,
                                                             user_sk):
    from bigchaindb.models import Transaction
    from bigchaindb.common.transaction import _fulfillment_to_details

    tx = Transaction.create([b.me, user_pk], [([user_pk], 100)])
    tx_signed = tx.sign([b.me_private, user_sk])
    assert tx_signed.validate(b) == tx_signed
    assert len(tx_signed.outputs) == 1
    assert tx_signed.outputs[0].amount == 100
    assert len(tx_signed.inputs) == 1

    ffill = _fulfillment_to_details(tx_signed.inputs[0].fulfillment)
    assert 'subconditions' in ffill
    assert len(ffill['subconditions']) == 2


# TRANSFER divisible asset
# Single input
# Single owners_before
# Single output
# Single owners_after
# TODO: I don't really need inputs. But I need the database to be setup or
#       else there will be no genesis block and b.get_last_voted_block will
#       fail.
#       Is there a better way of doing this?
@pytest.mark.bdb
@pytest.mark.usefixtures('inputs')
def test_single_in_single_own_single_out_single_own_transfer(b, user_pk,
                                                             user_sk):
    from bigchaindb.models import Transaction

    # CREATE divisible asset
    tx_create = Transaction.create([b.me], [([user_pk], 100)])
    tx_create_signed = tx_create.sign([b.me_private])
    # create block
    block = b.create_block([tx_create_signed])
    assert block.validate(b) == block
    b.write_block(block)
    # vote
    vote = b.vote(block.id, b.get_last_voted_block().id, True)
    b.write_vote(vote)

    # TRANSFER
    tx_transfer = Transaction.transfer(tx_create.to_inputs(), [([b.me], 100)],
                                       asset_id=tx_create.id)
    tx_transfer_signed = tx_transfer.sign([user_sk])

    assert tx_transfer_signed.validate(b)
    assert len(tx_transfer_signed.outputs) == 1
    assert tx_transfer_signed.outputs[0].amount == 100
    assert len(tx_transfer_signed.inputs) == 1


# TRANSFER divisible asset
# Single input
# Single owners_before
# Multiple output
# Single owners_after
@pytest.mark.bdb
@pytest.mark.usefixtures('inputs')
def test_single_in_single_own_multiple_out_single_own_transfer(b, user_pk,
                                                               user_sk):
    from bigchaindb.models import Transaction

    # CREATE divisible asset
    tx_create = Transaction.create([b.me], [([user_pk], 100)])
    tx_create_signed = tx_create.sign([b.me_private])
    # create block
    block = b.create_block([tx_create_signed])
    assert block.validate(b) == block
    b.write_block(block)
    # vote
    vote = b.vote(block.id, b.get_last_voted_block().id, True)
    b.write_vote(vote)

    # TRANSFER
    tx_transfer = Transaction.transfer(tx_create.to_inputs(),
                                       [([b.me], 50), ([b.me], 50)],
                                       asset_id=tx_create.id)
    tx_transfer_signed = tx_transfer.sign([user_sk])

    assert tx_transfer_signed.validate(b) == tx_transfer_signed
    assert len(tx_transfer_signed.outputs) == 2
    assert tx_transfer_signed.outputs[0].amount == 50
    assert tx_transfer_signed.outputs[1].amount == 50
    assert len(tx_transfer_signed.inputs) == 1


# TRANSFER divisible asset
# Single input
# Single owners_before
# Single output
# Multiple owners_after
@pytest.mark.bdb
@pytest.mark.usefixtures('inputs')
def test_single_in_single_own_single_out_multiple_own_transfer(b, user_pk,
                                                               user_sk):
    from bigchaindb.models import Transaction

    # CREATE divisible asset
    tx_create = Transaction.create([b.me], [([user_pk], 100)])
    tx_create_signed = tx_create.sign([b.me_private])
    # create block
    block = b.create_block([tx_create_signed])
    assert block.validate(b) == block
    b.write_block(block)
    # vote
    vote = b.vote(block.id, b.get_last_voted_block().id, True)
    b.write_vote(vote)

    # TRANSFER
    tx_transfer = Transaction.transfer(tx_create.to_inputs(),
                                       [([b.me, b.me], 100)],
                                       asset_id=tx_create.id)
    tx_transfer_signed = tx_transfer.sign([user_sk])

    assert tx_transfer_signed.validate(b) == tx_transfer_signed
    assert len(tx_transfer_signed.outputs) == 1
    assert tx_transfer_signed.outputs[0].amount == 100

    condition = tx_transfer_signed.outputs[0].to_dict()
    assert 'subconditions' in condition['condition']['details']
    assert len(condition['condition']['details']['subconditions']) == 2

    assert len(tx_transfer_signed.inputs) == 1


# TRANSFER divisible asset
# Single input
# Single owners_before
# Multiple outputs
# Mix: one output with a single owners_after, one output with multiple
#      owners_after
@pytest.mark.bdb
@pytest.mark.usefixtures('inputs')
def test_single_in_single_own_multiple_out_mix_own_transfer(b, user_pk,
                                                            user_sk):
    from bigchaindb.models import Transaction

    # CREATE divisible asset
    tx_create = Transaction.create([b.me], [([user_pk], 100)])
    tx_create_signed = tx_create.sign([b.me_private])
    # create block
    block = b.create_block([tx_create_signed])
    assert block.validate(b) == block
    b.write_block(block)
    # vote
    vote = b.vote(block.id, b.get_last_voted_block().id, True)
    b.write_vote(vote)

    # TRANSFER
    tx_transfer = Transaction.transfer(tx_create.to_inputs(),
                                       [([b.me], 50), ([b.me, b.me], 50)],
                                       asset_id=tx_create.id)
    tx_transfer_signed = tx_transfer.sign([user_sk])

    assert tx_transfer_signed.validate(b) == tx_transfer_signed
    assert len(tx_transfer_signed.outputs) == 2
    assert tx_transfer_signed.outputs[0].amount == 50
    assert tx_transfer_signed.outputs[1].amount == 50

    output_cid1 = tx_transfer_signed.outputs[1].to_dict()
    assert 'subconditions' in output_cid1['condition']['details']
    assert len(output_cid1['condition']['details']['subconditions']) == 2

    assert len(tx_transfer_signed.inputs) == 1


# TRANSFER divisible asset
# Single input
# Multiple owners_before
# Single output
# Single owners_after
@pytest.mark.bdb
@pytest.mark.usefixtures('inputs')
def test_single_in_multiple_own_single_out_single_own_transfer(b, user_pk,
                                                               user_sk):
    from bigchaindb.models import Transaction
    from bigchaindb.common.transaction import _fulfillment_to_details

    # CREATE divisible asset
    tx_create = Transaction.create([b.me], [([b.me, user_pk], 100)])
    tx_create_signed = tx_create.sign([b.me_private])
    # create block
    block = b.create_block([tx_create_signed])
    assert block.validate(b) == block
    b.write_block(block)
    # vote
    vote = b.vote(block.id, b.get_last_voted_block().id, True)
    b.write_vote(vote)

    # TRANSFER
    tx_transfer = Transaction.transfer(tx_create.to_inputs(), [([b.me], 100)],
                                       asset_id=tx_create.id)
    tx_transfer_signed = tx_transfer.sign([b.me_private, user_sk])

    assert tx_transfer_signed.validate(b) == tx_transfer_signed
    assert len(tx_transfer_signed.outputs) == 1
    assert tx_transfer_signed.outputs[0].amount == 100
    assert len(tx_transfer_signed.inputs) == 1

    ffill = _fulfillment_to_details(tx_transfer_signed.inputs[0].fulfillment)
    assert 'subconditions' in ffill
    assert len(ffill['subconditions']) == 2


# TRANSFER divisible asset
# Multiple inputs
# Single owners_before per input
# Single output
# Single owners_after
@pytest.mark.bdb
@pytest.mark.usefixtures('inputs')
def test_multiple_in_single_own_single_out_single_own_transfer(b, user_pk,
                                                               user_sk):
    from bigchaindb.models import Transaction

    # CREATE divisible asset
    tx_create = Transaction.create([b.me], [([user_pk], 50), ([user_pk], 50)])
    tx_create_signed = tx_create.sign([b.me_private])
    # create block
    block = b.create_block([tx_create_signed])
    assert block.validate(b) == block
    b.write_block(block)
    # vote
    vote = b.vote(block.id, b.get_last_voted_block().id, True)
    b.write_vote(vote)

    # TRANSFER
    tx_transfer = Transaction.transfer(tx_create.to_inputs(), [([b.me], 100)],
                                       asset_id=tx_create.id)
    tx_transfer_signed = tx_transfer.sign([user_sk])

    assert tx_transfer_signed.validate(b)
    assert len(tx_transfer_signed.outputs) == 1
    assert tx_transfer_signed.outputs[0].amount == 100
    assert len(tx_transfer_signed.inputs) == 2


# TRANSFER divisible asset
# Multiple inputs
# Multiple owners_before per input
# Single output
# Single owners_after
@pytest.mark.bdb
@pytest.mark.usefixtures('inputs')
def test_multiple_in_multiple_own_single_out_single_own_transfer(b, user_pk,
                                                                 user_sk):
    from bigchaindb.models import Transaction
    from bigchaindb.common.transaction import _fulfillment_to_details

    # CREATE divisible asset
    tx_create = Transaction.create([b.me], [([user_pk, b.me], 50), ([user_pk, b.me], 50)])
    tx_create_signed = tx_create.sign([b.me_private])
    # create block
    block = b.create_block([tx_create_signed])
    assert block.validate(b) == block
    b.write_block(block)
    # vote
    vote = b.vote(block.id, b.get_last_voted_block().id, True)
    b.write_vote(vote)

    # TRANSFER
    tx_transfer = Transaction.transfer(tx_create.to_inputs(), [([b.me], 100)],
                                       asset_id=tx_create.id)
    tx_transfer_signed = tx_transfer.sign([b.me_private, user_sk])

    assert tx_transfer_signed.validate(b)
    assert len(tx_transfer_signed.outputs) == 1
    assert tx_transfer_signed.outputs[0].amount == 100
    assert len(tx_transfer_signed.inputs) == 2

    ffill_fid0 = _fulfillment_to_details(tx_transfer_signed.inputs[0].fulfillment)
    ffill_fid1 = _fulfillment_to_details(tx_transfer_signed.inputs[1].fulfillment)
    assert 'subconditions' in ffill_fid0
    assert 'subconditions' in ffill_fid1
    assert len(ffill_fid0['subconditions']) == 2
    assert len(ffill_fid1['subconditions']) == 2


# TRANSFER divisible asset
# Multiple inputs
# Mix: one input with a single owners_before, one input with multiple
#      owners_before
# Single output
# Single owners_after
@pytest.mark.bdb
@pytest.mark.usefixtures('inputs')
def test_muiltiple_in_mix_own_multiple_out_single_own_transfer(b, user_pk,
                                                               user_sk):
    from bigchaindb.models import Transaction
    from bigchaindb.common.transaction import _fulfillment_to_details

    # CREATE divisible asset
    tx_create = Transaction.create([b.me], [([user_pk], 50), ([user_pk, b.me], 50)])
    tx_create_signed = tx_create.sign([b.me_private])
    # create block
    block = b.create_block([tx_create_signed])
    assert block.validate(b) == block
    b.write_block(block)
    # vote
    vote = b.vote(block.id, b.get_last_voted_block().id, True)
    b.write_vote(vote)

    # TRANSFER
    tx_transfer = Transaction.transfer(tx_create.to_inputs(), [([b.me], 100)],
                                       asset_id=tx_create.id)
    tx_transfer_signed = tx_transfer.sign([b.me_private, user_sk])

    assert tx_transfer_signed.validate(b) == tx_transfer_signed
    assert len(tx_transfer_signed.outputs) == 1
    assert tx_transfer_signed.outputs[0].amount == 100
    assert len(tx_transfer_signed.inputs) == 2

    ffill_fid0 = _fulfillment_to_details(tx_transfer_signed.inputs[0].fulfillment)
    ffill_fid1 = _fulfillment_to_details(tx_transfer_signed.inputs[1].fulfillment)
    assert 'subconditions' not in ffill_fid0
    assert 'subconditions' in ffill_fid1
    assert len(ffill_fid1['subconditions']) == 2


# TRANSFER divisible asset
# Multiple inputs
# Mix: one input with a single owners_before, one input with multiple
#      owners_before
# Multiple outputs
# Mix: one output with a single owners_after, one output with multiple
#      owners_after
@pytest.mark.bdb
@pytest.mark.usefixtures('inputs')
def test_muiltiple_in_mix_own_multiple_out_mix_own_transfer(b, user_pk,
                                                            user_sk):
    from bigchaindb.models import Transaction
    from bigchaindb.common.transaction import _fulfillment_to_details

    # CREATE divisible asset
    tx_create = Transaction.create([b.me], [([user_pk], 50), ([user_pk, b.me], 50)])
    tx_create_signed = tx_create.sign([b.me_private])
    # create block
    block = b.create_block([tx_create_signed])
    assert block.validate(b) == block
    b.write_block(block)
    # vote
    vote = b.vote(block.id, b.get_last_voted_block().id, True)
    b.write_vote(vote)

    # TRANSFER
    tx_transfer = Transaction.transfer(tx_create.to_inputs(),
                                       [([b.me], 50), ([b.me, user_pk], 50)],
                                       asset_id=tx_create.id)
    tx_transfer_signed = tx_transfer.sign([b.me_private, user_sk])

    assert tx_transfer_signed.validate(b) == tx_transfer_signed
    assert len(tx_transfer_signed.outputs) == 2
    assert tx_transfer_signed.outputs[0].amount == 50
    assert tx_transfer_signed.outputs[1].amount == 50
    assert len(tx_transfer_signed.inputs) == 2

    cond_cid0 = tx_transfer_signed.outputs[0].to_dict()
    cond_cid1 = tx_transfer_signed.outputs[1].to_dict()
    assert 'subconditions' not in cond_cid0['condition']['details']
    assert 'subconditions' in cond_cid1['condition']['details']
    assert len(cond_cid1['condition']['details']['subconditions']) == 2

    ffill_fid0 = _fulfillment_to_details(tx_transfer_signed.inputs[0].fulfillment)
    ffill_fid1 = _fulfillment_to_details(tx_transfer_signed.inputs[1].fulfillment)
    assert 'subconditions' not in ffill_fid0
    assert 'subconditions' in ffill_fid1
    assert len(ffill_fid1['subconditions']) == 2


# TRANSFER divisible asset
# Multiple inputs from different transactions
# Single owners_before
# Single output
# Single owners_after
@pytest.mark.bdb
@pytest.mark.usefixtures('inputs')
def test_multiple_in_different_transactions(b, user_pk, user_sk):
    from bigchaindb.models import Transaction

    # CREATE divisible asset
    # `b` creates a divisible asset and assigns 50 shares to `b` and
    # 50 shares to `user_pk`
    tx_create = Transaction.create([b.me], [([user_pk], 50), ([b.me], 50)])
    tx_create_signed = tx_create.sign([b.me_private])
    # create block
    block = b.create_block([tx_create_signed])
    assert block.validate(b) == block
    b.write_block(block)
    # vote
    vote = b.vote(block.id, b.get_last_voted_block().id, True)
    b.write_vote(vote)

    # TRANSFER divisible asset
    # `b` transfers its 50 shares to `user_pk`
    # after this transaction `user_pk` will have a total of 100 shares
    # split across two different transactions
    tx_transfer1 = Transaction.transfer(tx_create.to_inputs([1]),
                                        [([user_pk], 50)],
                                        asset_id=tx_create.id)
    tx_transfer1_signed = tx_transfer1.sign([b.me_private])
    # create block
    block = b.create_block([tx_transfer1_signed])
    assert block.validate(b) == block
    b.write_block(block)
    # vote
    vote = b.vote(block.id, b.get_last_voted_block().id, True)
    b.write_vote(vote)

    # TRANSFER
    # `user_pk` combines two different transaction with 50 shares each and
    # transfers a total of 100 shares back to `b`
    tx_transfer2 = Transaction.transfer(tx_create.to_inputs([0]) +
                                        tx_transfer1.to_inputs([0]),
                                        [([b.me], 100)],
                                        asset_id=tx_create.id)
    tx_transfer2_signed = tx_transfer2.sign([user_sk])

    assert tx_transfer2_signed.validate(b) == tx_transfer2_signed
    assert len(tx_transfer2_signed.outputs) == 1
    assert tx_transfer2_signed.outputs[0].amount == 100
    assert len(tx_transfer2_signed.inputs) == 2

    fid0_input = tx_transfer2_signed.inputs[0].fulfills.txid
    fid1_input = tx_transfer2_signed.inputs[1].fulfills.txid
    assert fid0_input == tx_create.id
    assert fid1_input == tx_transfer1.id


# In a TRANSFER transaction of a divisible asset the amount being spent in the
# inputs needs to match the amount being sent in the outputs.
# In other words `amount_in_inputs - amount_in_outputs == 0`
@pytest.mark.bdb
@pytest.mark.usefixtures('inputs')
def test_amount_error_transfer(b, user_pk, user_sk):
    from bigchaindb.models import Transaction
    from bigchaindb.common.exceptions import AmountError

    # CREATE divisible asset
    tx_create = Transaction.create([b.me], [([user_pk], 100)])
    tx_create_signed = tx_create.sign([b.me_private])
    # create block
    block = b.create_block([tx_create_signed])
    assert block.validate(b) == block
    b.write_block(block)
    # vote
    vote = b.vote(block.id, b.get_last_voted_block().id, True)
    b.write_vote(vote)

    # TRANSFER
    # output amount less than input amount
    tx_transfer = Transaction.transfer(tx_create.to_inputs(), [([b.me], 50)],
                                       asset_id=tx_create.id)
    tx_transfer_signed = tx_transfer.sign([user_sk])
    with pytest.raises(AmountError):
        tx_transfer_signed.validate(b)

    # TRANSFER
    # output amount greater than input amount
    tx_transfer = Transaction.transfer(tx_create.to_inputs(), [([b.me], 101)],
                                       asset_id=tx_create.id)
    tx_transfer_signed = tx_transfer.sign([user_sk])
    with pytest.raises(AmountError):
        tx_transfer_signed.validate(b)


@pytest.mark.skip(reason='Figure out how to handle this case')
@pytest.mark.bdb
@pytest.mark.usefixtures('inputs')
def test_threshold_same_public_key(b, user_pk, user_sk):
    # If we try to fulfill a threshold condition where each subcondition has
    # the same key get_subcondition_from_vk will always return the first
    # subcondition. This means that only the 1st subfulfillment will be
    # generated
    # Creating threshold conditions with the same key does not make sense but
    # that does not mean that the code shouldn't work.

    from bigchaindb.models import Transaction

    # CREATE divisible asset
    tx_create = Transaction.create([b.me], [([user_pk, user_pk], 100)])
    tx_create_signed = tx_create.sign([b.me_private])
    # create block
    block = b.create_block([tx_create_signed])
    assert block.validate(b) == block
    b.write_block(block)
    # vote
    vote = b.vote(block.id, b.get_last_voted_block().id, True)
    b.write_vote(vote)

    # TRANSFER
    tx_transfer = Transaction.transfer(tx_create.to_inputs(), [([b.me], 100)],
                                       asset_id=tx_create.id)
    tx_transfer_signed = tx_transfer.sign([user_sk, user_sk])

    assert tx_transfer_signed.validate(b) == tx_transfer_signed


@pytest.mark.bdb
@pytest.mark.usefixtures('inputs')
def test_sum_amount(b, user_pk, user_sk):
    from bigchaindb.models import Transaction

    # CREATE divisible asset with 3 outputs with amount 1
    tx_create = Transaction.create([b.me], [([user_pk], 1), ([user_pk], 1), ([user_pk], 1)])
    tx_create_signed = tx_create.sign([b.me_private])
    # create block
    block = b.create_block([tx_create_signed])
    assert block.validate(b) == block
    b.write_block(block)
    # vote
    vote = b.vote(block.id, b.get_last_voted_block().id, True)
    b.write_vote(vote)

    # create a transfer transaction with one output and check if the amount
    # is 3
    tx_transfer = Transaction.transfer(tx_create.to_inputs(), [([b.me], 3)],
                                       asset_id=tx_create.id)
    tx_transfer_signed = tx_transfer.sign([user_sk])

    assert tx_transfer_signed.validate(b) == tx_transfer_signed
    assert len(tx_transfer_signed.outputs) == 1
    assert tx_transfer_signed.outputs[0].amount == 3


@pytest.mark.bdb
@pytest.mark.usefixtures('inputs')
def test_divide(b, user_pk, user_sk):
    from bigchaindb.models import Transaction

    # CREATE divisible asset with 1 output with amount 3
    tx_create = Transaction.create([b.me], [([user_pk], 3)])
    tx_create_signed = tx_create.sign([b.me_private])
    # create block
    block = b.create_block([tx_create_signed])
    assert block.validate(b) == block
    b.write_block(block)
    # vote
    vote = b.vote(block.id, b.get_last_voted_block().id, True)
    b.write_vote(vote)

    # create a transfer transaction with 3 outputs and check if the amount
    # of each output is 1
    tx_transfer = Transaction.transfer(tx_create.to_inputs(),
                                       [([b.me], 1), ([b.me], 1), ([b.me], 1)],
                                       asset_id=tx_create.id)
    tx_transfer_signed = tx_transfer.sign([user_sk])

    assert tx_transfer_signed.validate(b) == tx_transfer_signed
    assert len(tx_transfer_signed.outputs) == 3
    for output in tx_transfer_signed.outputs:
        assert output.amount == 1
