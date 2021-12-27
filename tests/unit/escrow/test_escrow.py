from scripts.escrow_scripts.deploy_escrow import deploy_escrow, DISPUTE_FEE, MIN_ORDER
from scripts.helpful_scripts import get_account, LOCAL_BLOCKCHAIN_ENVIRONMENTS
from brownie import network, exceptions
import pytest
from web3 import Web3

zero_address = "0x0000000000000000000000000000000000000000"


def test_deploy_escrow():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    escrow = deploy_escrow()
    dispute_fee = Web3.toWei(DISPUTE_FEE, "ether")
    min_order = Web3.toWei(MIN_ORDER, "ether")
    assert escrow.owner() == account
    assert escrow.numBlocksToExpire() == 1
    assert escrow.disputeFee() == dispute_fee
    assert escrow.minOrderAmount() == min_order
    assert escrow.orderCount() == 0
    print("Test Deploy OK!")


def test_can_create_order():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    escrow = deploy_escrow()
    amount = Web3.toWei(2 * MIN_ORDER, "ether")
    deposit = Web3.toWei(DISPUTE_FEE, "ether")
    tx = escrow.createOrder(amount, deposit, {"from": account})
    tx.wait(1)
    assert escrow.orderCount() == 1
    assert escrow.orders(0) == (0, zero_address, account, amount, deposit, 0, 0)


def test_can_initiate_order():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    escrow = deploy_escrow()
    amount = Web3.toWei(2 * MIN_ORDER, "ether")
    deposit = Web3.toWei(DISPUTE_FEE, "ether")
    tx_create = escrow.createOrder(amount, deposit, {"from": account})
    tx_create.wait(1)
    tx_initiate = escrow.initiateOrder(
        0, {"from": account_1, "value": amount + deposit}
    )
    tx_initiate.wait(1)
    assert escrow.orders(0) == (1, account_1, account, amount, deposit, 0, 0)


def test_can_send_order():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    escrow = deploy_escrow()
    amount = Web3.toWei(2 * MIN_ORDER, "ether")
    deposit = Web3.toWei(DISPUTE_FEE, "ether")
    tx_create = escrow.createOrder(amount, deposit, {"from": account})
    tx_create.wait(1)
    tx_initiate = escrow.initiateOrder(
        0, {"from": account_1, "value": amount + deposit}
    )
    tx_initiate.wait(1)
    tx_send = escrow.sendOrder(0, {"from": account})
    tx_send.wait(1)
    send_block = tx_send.block_number
    assert escrow.orders(0) == (2, account_1, account, amount, deposit, 0, send_block)


def test_only_seller_can_send_order():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    account_2 = get_account(index=2)
    escrow = deploy_escrow()
    amount = Web3.toWei(2 * MIN_ORDER, "ether")
    deposit = Web3.toWei(DISPUTE_FEE, "ether")
    tx_create = escrow.createOrder(amount, deposit, {"from": account})
    tx_create.wait(1)
    tx_initiate = escrow.initiateOrder(
        0, {"from": account_1, "value": amount + deposit}
    )
    tx_initiate.wait(1)
    with pytest.raises(exceptions.VirtualMachineError):
        tx_send = escrow.sendOrder(0, {"from": account_2})


def test_can_receive_order():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    escrow = deploy_escrow()
    amount = Web3.toWei(2 * MIN_ORDER, "ether")
    deposit = Web3.toWei(DISPUTE_FEE, "ether")
    tx_create = escrow.createOrder(amount, deposit, {"from": account})
    tx_create.wait(1)
    tx_initiate = escrow.initiateOrder(
        0, {"from": account_1, "value": amount + deposit}
    )
    tx_initiate.wait(1)
    tx_send = escrow.sendOrder(0, {"from": account})
    tx_send.wait(1)
    send_block = tx_send.block_number
    seller_old_balance = account.balance()
    buyer_old_balance = account_1.balance()
    tx_receive = escrow.receiveOrder(0, {"from": account_1})
    tx_receive.wait(1)
    assert account.balance() == seller_old_balance + amount
    assert account_1.balance() == buyer_old_balance + deposit
    assert escrow.orders(0) == (3, account_1, account, amount, deposit, 0, send_block)


def test_can_expire_order():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    escrow = deploy_escrow(expiry_blocks=0)
    amount = Web3.toWei(2 * MIN_ORDER, "ether")
    deposit = Web3.toWei(DISPUTE_FEE, "ether")
    tx_create = escrow.createOrder(amount, deposit, {"from": account})
    tx_create.wait(1)
    tx_initiate = escrow.initiateOrder(
        0, {"from": account_1, "value": amount + deposit}
    )
    tx_initiate.wait(1)
    tx_send = escrow.sendOrder(0, {"from": account})
    tx_send.wait(1)
    block_send = tx_send.block_number
    seller_old_balance = account.balance()
    tx_expire = escrow.expireOrder(0, {"from": account})
    tx_expire.wait(1)
    assert account.balance() == seller_old_balance + amount + deposit
    assert escrow.orders(0) == (7, account_1, account, amount, deposit, 0, block_send)


def test_cant_expire_order():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    escrow = deploy_escrow()
    amount = Web3.toWei(2 * MIN_ORDER, "ether")
    deposit = Web3.toWei(DISPUTE_FEE, "ether")
    tx_create = escrow.createOrder(amount, deposit, {"from": account})
    tx_create.wait(1)
    tx_initiate = escrow.initiateOrder(
        0, {"from": account_1, "value": amount + deposit}
    )
    tx_initiate.wait(1)
    tx_send = escrow.sendOrder(0, {"from": account})
    tx_send.wait(1)
    with pytest.raises(exceptions.VirtualMachineError):
        escrow.expireOrder(0, {"from": account})


def test_buyer_can_cancel_order_before_send():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    escrow = deploy_escrow()
    amount = Web3.toWei(2 * MIN_ORDER, "ether")
    deposit = Web3.toWei(DISPUTE_FEE, "ether")
    tx_create = escrow.createOrder(amount, deposit, {"from": account})
    tx_create.wait(1)
    buyer_old_balance = account_1.balance()
    tx_initiate = escrow.initiateOrder(
        0, {"from": account_1, "value": amount + deposit}
    )
    tx_initiate.wait(1)
    assert account_1.balance() == buyer_old_balance - amount - deposit
    tx_cancel = escrow.cancelBuyOrder(0, {"from": account_1})
    tx_cancel.wait(1)
    assert buyer_old_balance == account_1.balance()
    assert escrow.orders(0) == (0, zero_address, account, amount, deposit, 0, 0)


def test_seller_can_cancel_order_after_create():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    escrow = deploy_escrow()
    amount = Web3.toWei(2 * MIN_ORDER, "ether")
    deposit = Web3.toWei(DISPUTE_FEE, "ether")
    tx_create = escrow.createOrder(amount, deposit, {"from": account})
    tx_create.wait(1)
    tx_cancel = escrow.cancelSellOrder(0, {"from": account})
    tx_cancel.wait(1)
    assert escrow.orders(0) == (4, zero_address, account, amount, deposit, 0, 0)


def test_seller_can_cancel_order_after_initiate():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    escrow = deploy_escrow()
    amount = Web3.toWei(2 * MIN_ORDER, "ether")
    deposit = Web3.toWei(DISPUTE_FEE, "ether")
    tx_create = escrow.createOrder(amount, deposit, {"from": account})
    tx_create.wait(1)
    buyer_old_balance = account_1.balance()
    tx_initiate = escrow.initiateOrder(
        0, {"from": account_1, "value": amount + deposit}
    )
    tx_initiate.wait(1)
    tx_cancel = escrow.cancelSellOrder(0, {"from": account})
    tx_cancel.wait(1)
    assert buyer_old_balance == account_1.balance()
    assert escrow.orders(0) == (4, account_1, account, amount, deposit, 0, 0)


def test_seller_can_cancel_order_after_send():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    escrow = deploy_escrow()
    amount = Web3.toWei(2 * MIN_ORDER, "ether")
    deposit = Web3.toWei(DISPUTE_FEE, "ether")
    tx_create = escrow.createOrder(amount, deposit, {"from": account})
    tx_create.wait(1)
    buyer_old_balance = account_1.balance()
    tx_initiate = escrow.initiateOrder(
        0, {"from": account_1, "value": amount + deposit}
    )
    tx_initiate.wait(1)
    tx_send = escrow.sendOrder(0, {"from": account})
    tx_send.wait(1)
    block_send = tx_send.block_number
    tx_cancel = escrow.cancelSellOrder(0, {"from": account})
    tx_cancel.wait(1)
    assert account_1.balance() == buyer_old_balance
    assert escrow.orders(0) == (4, account_1, account, amount, deposit, 0, block_send)


def test_buyer_can_dispute_order_after_send():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    escrow = deploy_escrow()
    amount = Web3.toWei(2 * MIN_ORDER, "ether")
    deposit = Web3.toWei(DISPUTE_FEE, "ether")
    tx_create = escrow.createOrder(amount, deposit, {"from": account})
    tx_create.wait(1)
    tx_initiate = escrow.initiateOrder(
        0, {"from": account_1, "value": amount + deposit}
    )
    tx_initiate.wait(1)
    tx_send = escrow.sendOrder(0, {"from": account})
    tx_send.wait(1)
    block_send = tx_send.block_number
    tx_dispute = escrow.disputeOrder(0, {"from": account_1})
    tx_dispute.wait(1)
    assert escrow.orders(0) == (5, account_1, account, amount, deposit, 0, block_send)


def test_seller_can_dispute_order_after_send():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    escrow = deploy_escrow()
    amount = Web3.toWei(2 * MIN_ORDER, "ether")
    deposit = Web3.toWei(DISPUTE_FEE, "ether")
    tx_create = escrow.createOrder(amount, deposit, {"from": account})
    tx_create.wait(1)
    tx_initiate = escrow.initiateOrder(
        0, {"from": account_1, "value": amount + deposit}
    )
    tx_initiate.wait(1)
    tx_send = escrow.sendOrder(0, {"from": account})
    tx_send.wait(1)
    block_send = tx_send.block_number
    tx_dispute = escrow.disputeOrder(0, {"from": account})
    tx_dispute.wait(1)
    assert escrow.orders(0) == (5, account_1, account, amount, deposit, 0, block_send)


def test_buyer_cant_cancel_order_after_send():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    escrow = deploy_escrow()
    amount = Web3.toWei(2 * MIN_ORDER, "ether")
    deposit = Web3.toWei(DISPUTE_FEE, "ether")
    tx_create = escrow.createOrder(amount, deposit, {"from": account})
    tx_create.wait(1)
    tx_initiate = escrow.initiateOrder(
        0, {"from": account_1, "value": amount + deposit}
    )
    tx_initiate.wait(1)
    tx_send = escrow.sendOrder(0, {"from": account})
    tx_send.wait(1)
    with pytest.raises(exceptions.VirtualMachineError):
        escrow.cancelBuyOrder(0, {"from": account_1})


def test_admin_can_resolve_dispute():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    account_2 = get_account(index=2)
    escrow = deploy_escrow()
    amount = Web3.toWei(3 * MIN_ORDER, "ether")  # 0.03
    deposit = Web3.toWei(DISPUTE_FEE, "ether")  # 0.005
    tx_create = escrow.createOrder(amount, deposit, {"from": account_2})
    tx_create.wait(1)
    tx_initiate = escrow.initiateOrder(
        0, {"from": account_1, "value": amount + deposit}
    )
    tx_initiate.wait(1)
    tx_send = escrow.sendOrder(0, {"from": account_2})
    tx_send.wait(1)
    block_send = tx_send.block_number
    tx_dispute = escrow.disputeOrder(0, {"from": account_2})
    tx_dispute.wait(1)
    buyer_refund = Web3.toWei(MIN_ORDER, "ether")  # 0.01
    seller_old_balance = account_2.balance()
    buyer_old_balance = account_1.balance()
    admin_old_balance = account.balance()
    tx_resolve = escrow.resolveDispute(0, buyer_refund, {"from": account})
    tx_resolve.wait(1)
    assert account_2.balance() == seller_old_balance + Web3.toWei(
        2 * MIN_ORDER, "ether"
    )
    assert account_1.balance() == buyer_old_balance + buyer_refund
    assert account.balance() == admin_old_balance + Web3.toWei(DISPUTE_FEE, "ether")
    assert escrow.orders(0) == (6, account_1, account_2, amount, deposit, 0, block_send)
