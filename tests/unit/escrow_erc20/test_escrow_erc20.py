from scripts.escrow_erc20.deploy_escrow_erc20 import (
    deploy_escrow_erc20,
    fund_account,
    deploy_escrow_token,
    approve_erc20,
    ADMIN_FEE,
)

from scripts.helpful_scripts import get_account, LOCAL_BLOCKCHAIN_ENVIRONMENTS
from brownie import network, exceptions
import pytest
from web3 import Web3

zero_address = "0x0000000000000000000000000000000000000000"
INITIAL_SUPPLY = 1000000000000000000000000
AMOUNT = 10
DEPOSIT = 1
BLOCKS = 10


def test_deploy_escrow_erc20():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    escrow_erc20 = deploy_escrow_erc20()
    admin_fee = Web3.toWei(ADMIN_FEE, "ether")
    assert escrow_erc20.owner() == account
    assert escrow_erc20.buyer() == zero_address
    assert escrow_erc20.seller() == zero_address
    assert escrow_erc20.status() == 0
    assert escrow_erc20.amount() == 0
    assert escrow_erc20.deposit() == 0
    assert escrow_erc20.numBlocksToExpire() == 1
    assert escrow_erc20.adminFee() == admin_fee
    print("Test Deploy OK!")


def test_deploy_escrow_token():
    account = get_account()
    escrow_token = deploy_escrow_token()
    account_balance = escrow_token.balanceOf(account)
    assert account_balance == INITIAL_SUPPLY


def test_can_create_order_erc20():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    escrow = deploy_escrow_erc20()
    escrow_token = deploy_escrow_token()
    blocks = 10
    tx = escrow.createOrder(escrow_token, AMOUNT, DEPOSIT, blocks, {"from": account})
    tx.wait(1)
    assert escrow.token() == escrow_token
    assert escrow.amount() == AMOUNT
    assert escrow.deposit() == DEPOSIT
    assert escrow.numBlocksToExpire() == blocks
    assert escrow.seller() == account
    assert escrow.buyer() == zero_address
    assert escrow.status() == 1


def test_can_initiate_order_erc20():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    escrow = deploy_escrow_erc20()
    escrow_token = deploy_escrow_token()
    admin_fee = Web3.toWei(ADMIN_FEE, "ether")
    blocks = 10
    tx_create = escrow.createOrder(
        escrow_token, AMOUNT, DEPOSIT, blocks, {"from": account_1}
    )
    tx_create.wait(1)
    tx_approve = approve_erc20(AMOUNT + DEPOSIT, escrow, escrow_token, account)
    tx_approve.wait(1)
    tx_initiate = escrow.initiateOrder({"from": account, "value": admin_fee})
    tx_initiate.wait(1)
    assert escrow.buyer() == account
    assert escrow_token.balanceOf(escrow) == AMOUNT + DEPOSIT
    assert escrow.status() == 2


def test_can_send_order_erc20():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    escrow = deploy_escrow_erc20()
    escrow_token = deploy_escrow_token()
    admin_fee = Web3.toWei(ADMIN_FEE, "ether")
    blocks = 10
    tx_create = escrow.createOrder(
        escrow_token, AMOUNT, DEPOSIT, blocks, {"from": account_1}
    )
    tx_create.wait(1)
    tx_approve = approve_erc20(AMOUNT + DEPOSIT, escrow, escrow_token, account)
    tx_approve.wait(1)
    tx_initiate = escrow.initiateOrder({"from": account, "value": admin_fee})
    tx_initiate.wait(1)
    tx_send = escrow.sendOrder({"from": account_1})
    tx_send.wait(1)
    send_block = tx_send.block_number
    assert escrow.status() == 3
    assert escrow.sendBlock() == send_block


def test_only_seller_can_send_order_erc20():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    account_2 = get_account(index=2)
    escrow = deploy_escrow_erc20()
    escrow_token = deploy_escrow_token()
    admin_fee = Web3.toWei(ADMIN_FEE, "ether")
    blocks = 10
    tx_create = escrow.createOrder(
        escrow_token, AMOUNT, DEPOSIT, blocks, {"from": account_1}
    )
    tx_create.wait(1)
    tx_approve = approve_erc20(AMOUNT + DEPOSIT, escrow, escrow_token, account)
    tx_approve.wait(1)
    tx_initiate = escrow.initiateOrder({"from": account, "value": admin_fee})
    tx_initiate.wait(1)
    with pytest.raises(exceptions.VirtualMachineError):
        escrow.sendOrder({"from": account_2})


def test_can_receive_order_erc20():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    escrow = deploy_escrow_erc20()
    escrow_token = deploy_escrow_token()
    admin_fee = Web3.toWei(ADMIN_FEE, "ether")
    blocks = 10
    tx_create = escrow.createOrder(
        escrow_token, AMOUNT, DEPOSIT, blocks, {"from": account_1}
    )
    tx_create.wait(1)
    tx_approve = approve_erc20(AMOUNT + DEPOSIT, escrow, escrow_token, account)
    tx_approve.wait(1)
    tx_initiate = escrow.initiateOrder({"from": account, "value": admin_fee})
    tx_initiate.wait(1)
    tx_send = escrow.sendOrder({"from": account_1})
    tx_send.wait(1)
    seller_old_balance = escrow_token.balanceOf(account_1)
    buyer_old_balance = escrow_token.balanceOf(account)
    buyer_old_eth_balance = account.balance()
    tx_receive = escrow.receiveOrder({"from": account})
    tx_receive.wait(1)
    assert escrow_token.balanceOf(account) == buyer_old_balance + DEPOSIT
    assert escrow_token.balanceOf(account_1) == seller_old_balance + AMOUNT
    assert account.balance() == buyer_old_eth_balance + admin_fee
    assert escrow.status() == 4


def test_can_expire_order_erc20():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    escrow = deploy_escrow_erc20()
    escrow_token = deploy_escrow_token()
    admin_fee = Web3.toWei(ADMIN_FEE, "ether")
    tx_create = escrow.createOrder(
        escrow_token, AMOUNT, DEPOSIT, 0, {"from": account_1}
    )
    tx_create.wait(1)
    tx_approve = approve_erc20(AMOUNT + DEPOSIT, escrow, escrow_token, account)
    tx_approve.wait(1)
    tx_initiate = escrow.initiateOrder({"from": account, "value": admin_fee})
    tx_initiate.wait(1)
    tx_send = escrow.sendOrder({"from": account_1})
    tx_send.wait(1)
    seller_old_balance = escrow_token.balanceOf(account_1)
    buyer_old_eth_balance = account.balance()
    tx_expire = escrow.expireOrder({"from": account_1})
    tx_expire.wait(1)
    assert escrow_token.balanceOf(account_1) == seller_old_balance + AMOUNT + DEPOSIT
    assert account.balance() == buyer_old_eth_balance + admin_fee
    assert escrow.status() == 8


def test_cant_expire_order_erc20():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    escrow = deploy_escrow_erc20()
    escrow_token = deploy_escrow_token()
    admin_fee = Web3.toWei(ADMIN_FEE, "ether")
    blocks = 10
    tx_create = escrow.createOrder(
        escrow_token, AMOUNT, DEPOSIT, blocks, {"from": account_1}
    )
    tx_create.wait(1)
    tx_approve = approve_erc20(AMOUNT + DEPOSIT, escrow, escrow_token, account)
    tx_approve.wait(1)
    tx_initiate = escrow.initiateOrder({"from": account, "value": admin_fee})
    tx_initiate.wait(1)
    tx_send = escrow.sendOrder({"from": account_1})
    tx_send.wait(1)
    with pytest.raises(exceptions.VirtualMachineError):
        escrow.expireOrder({"from": account_1})


def test_buyer_can_cancel_order_before_send_erc20():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    account_2 = get_account(index=2)
    escrow = deploy_escrow_erc20()
    escrow_token = deploy_escrow_token()
    escrow_token.transfer(account_2, AMOUNT + DEPOSIT, {"from": account})
    admin_fee = Web3.toWei(ADMIN_FEE, "ether")
    tx_create = escrow.createOrder(
        escrow_token, AMOUNT, DEPOSIT, 0, {"from": account_1}
    )
    tx_create.wait(1)
    tx_approve = approve_erc20(AMOUNT + DEPOSIT, escrow, escrow_token, account_2)
    tx_approve.wait(1)
    tx_initiate = escrow.initiateOrder({"from": account_2, "value": admin_fee})
    tx_initiate.wait(1)
    buyer_old_balance = escrow_token.balanceOf(account_2)
    admin_old_eth_balance = account.balance()
    tx_cancel = escrow.cancelBuyOrder({"from": account_2})
    tx_cancel.wait(1)
    assert escrow_token.balanceOf(account_2) == buyer_old_balance + AMOUNT + DEPOSIT
    assert account.balance() == admin_old_eth_balance + admin_fee
    assert escrow.status() == 1


def test_seller_can_cancel_order_after_create_erc20():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account_1 = get_account(index=1)
    escrow = deploy_escrow_erc20()
    escrow_token = deploy_escrow_token()
    blocks = 10
    tx_create = escrow.createOrder(
        escrow_token, AMOUNT, DEPOSIT, blocks, {"from": account_1}
    )
    tx_create.wait(1)
    tx_cancel = escrow.cancelSellOrder({"from": account_1})
    tx_cancel.wait(1)
    assert escrow.status() == 5


def test_seller_can_cancel_order_after_initiate_erc20():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    escrow = deploy_escrow_erc20()
    escrow_token = deploy_escrow_token()
    admin_fee = Web3.toWei(ADMIN_FEE, "ether")
    blocks = 10
    tx_create = escrow.createOrder(
        escrow_token, AMOUNT, DEPOSIT, blocks, {"from": account_1}
    )
    tx_create.wait(1)
    tx_approve = approve_erc20(AMOUNT + DEPOSIT, escrow, escrow_token, account)
    tx_approve.wait(1)
    buyer_old_balance = escrow_token.balanceOf(account)
    buyer_old_eth_balance = account.balance()
    tx_initiate = escrow.initiateOrder({"from": account, "value": admin_fee})
    tx_initiate.wait(1)
    tx_cancel = escrow.cancelSellOrder({"from": account_1})
    tx_cancel.wait(1)
    assert escrow.status() == 5
    assert escrow_token.balanceOf(account) == buyer_old_balance
    assert account.balance() == buyer_old_eth_balance


def test_seller_can_cancel_order_after_send_erc20():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    escrow = deploy_escrow_erc20()
    escrow_token = deploy_escrow_token()
    admin_fee = Web3.toWei(ADMIN_FEE, "ether")
    tx_create = escrow.createOrder(
        escrow_token, AMOUNT, DEPOSIT, 0, {"from": account_1}
    )
    tx_create.wait(1)
    tx_approve = approve_erc20(AMOUNT + DEPOSIT, escrow, escrow_token, account)
    tx_approve.wait(1)
    buyer_old_balance = escrow_token.balanceOf(account)
    buyer_old_eth_balance = account.balance()
    tx_initiate = escrow.initiateOrder({"from": account, "value": admin_fee})
    tx_initiate.wait(1)
    tx_send = escrow.sendOrder({"from": account_1})
    tx_send.wait(1)
    tx_cancel = escrow.cancelSellOrder({"from": account_1})
    tx_cancel.wait(1)
    assert escrow.status() == 5
    assert escrow_token.balanceOf(account) == buyer_old_balance
    assert account.balance() == buyer_old_eth_balance


def test_buyer_can_dispute_order_after_send_erc20():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    escrow = deploy_escrow_erc20()
    escrow_token = deploy_escrow_token()
    admin_fee = Web3.toWei(ADMIN_FEE, "ether")
    tx_create = escrow.createOrder(
        escrow_token, AMOUNT, DEPOSIT, 0, {"from": account_1}
    )
    tx_create.wait(1)
    tx_approve = approve_erc20(AMOUNT + DEPOSIT, escrow, escrow_token, account)
    tx_approve.wait(1)
    tx_initiate = escrow.initiateOrder({"from": account, "value": admin_fee})
    tx_initiate.wait(1)
    tx_send = escrow.sendOrder({"from": account_1})
    tx_send.wait(1)
    tx_dispute = escrow.disputeOrder({"from": account})
    tx_dispute.wait(1)
    assert escrow.status() == 6


def test_seller_can_dispute_order_after_send_erc20():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    escrow = deploy_escrow_erc20()
    escrow_token = deploy_escrow_token()
    admin_fee = Web3.toWei(ADMIN_FEE, "ether")
    tx_create = escrow.createOrder(
        escrow_token, AMOUNT, DEPOSIT, 0, {"from": account_1}
    )
    tx_create.wait(1)
    tx_approve = approve_erc20(AMOUNT + DEPOSIT, escrow, escrow_token, account)
    tx_approve.wait(1)
    tx_initiate = escrow.initiateOrder({"from": account, "value": admin_fee})
    tx_initiate.wait(1)
    tx_send = escrow.sendOrder({"from": account_1})
    tx_send.wait(1)
    tx_dispute = escrow.disputeOrder({"from": account_1})
    tx_dispute.wait(1)
    assert escrow.status() == 6


def test_stranger_cant_dispute_order_erc20():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    stranger = get_account(index=2)
    escrow = deploy_escrow_erc20()
    escrow_token = deploy_escrow_token()
    admin_fee = Web3.toWei(ADMIN_FEE, "ether")
    tx_create = escrow.createOrder(
        escrow_token, AMOUNT, DEPOSIT, 0, {"from": account_1}
    )
    tx_create.wait(1)
    tx_approve = approve_erc20(AMOUNT + DEPOSIT, escrow, escrow_token, account)
    tx_approve.wait(1)
    tx_initiate = escrow.initiateOrder({"from": account, "value": admin_fee})
    tx_initiate.wait(1)
    tx_send = escrow.sendOrder({"from": account_1})
    tx_send.wait(1)
    with pytest.raises(exceptions.VirtualMachineError):
        escrow.disputeOrder({"from": stranger})


def test_buyer_cant_cancel_order_after_send_erc20():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    escrow = deploy_escrow_erc20()
    escrow_token = deploy_escrow_token()
    admin_fee = Web3.toWei(ADMIN_FEE, "ether")
    tx_create = escrow.createOrder(
        escrow_token, AMOUNT, DEPOSIT, 0, {"from": account_1}
    )
    tx_create.wait(1)
    tx_approve = approve_erc20(AMOUNT + DEPOSIT, escrow, escrow_token, account)
    tx_approve.wait(1)
    tx_initiate = escrow.initiateOrder({"from": account, "value": admin_fee})
    tx_initiate.wait(1)
    tx_send = escrow.sendOrder({"from": account_1})
    tx_send.wait(1)
    with pytest.raises(exceptions.VirtualMachineError):
        escrow.cancelBuyOrder({"from": account})


def test_admin_can_resolve_dispute_erc20():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    account_2 = get_account(index=2)
    escrow = deploy_escrow_erc20()
    escrow_token = deploy_escrow_token()
    escrow_token.transfer(account_2, 2 * AMOUNT + DEPOSIT, {"from": account})
    admin_fee = Web3.toWei(ADMIN_FEE, "ether")
    tx_create = escrow.createOrder(
        escrow_token, 2 * AMOUNT, DEPOSIT, 0, {"from": account_1}
    )
    tx_create.wait(1)
    tx_approve = approve_erc20(2 * AMOUNT + DEPOSIT, escrow, escrow_token, account_2)
    tx_approve.wait(1)
    tx_initiate = escrow.initiateOrder({"from": account_2, "value": admin_fee})
    tx_initiate.wait(1)
    tx_send = escrow.sendOrder({"from": account_1})
    tx_send.wait(1)
    tx_dispute = escrow.disputeOrder({"from": account_2})
    tx_dispute.wait(1)
    buyer_refund = AMOUNT + DEPOSIT  # 0.01
    seller_old_balance = escrow_token.balanceOf(account_1)
    buyer_old_balance = escrow_token.balanceOf(account_2)
    admin_old_balance = account.balance()
    tx_resolve = escrow.resolveDispute(buyer_refund, {"from": account})
    tx_resolve.wait(1)
    assert escrow_token.balanceOf(account_2) == buyer_old_balance + buyer_refund
    assert escrow_token.balanceOf(account_1) == seller_old_balance + AMOUNT
    assert account.balance() == admin_old_balance + admin_fee
    assert escrow.status() == 7


def test_non_admin_cant_resolve_dispute_erc20():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    account_2 = get_account(index=2)
    escrow = deploy_escrow_erc20()
    escrow_token = deploy_escrow_token()
    escrow_token.transfer(account_2, 2 * AMOUNT + DEPOSIT, {"from": account})
    admin_fee = Web3.toWei(ADMIN_FEE, "ether")
    tx_create = escrow.createOrder(
        escrow_token, 2 * AMOUNT, DEPOSIT, 0, {"from": account_1}
    )
    tx_create.wait(1)
    tx_approve = approve_erc20(2 * AMOUNT + DEPOSIT, escrow, escrow_token, account_2)
    tx_approve.wait(1)
    tx_initiate = escrow.initiateOrder({"from": account_2, "value": admin_fee})
    tx_initiate.wait(1)
    tx_send = escrow.sendOrder({"from": account_1})
    tx_send.wait(1)
    tx_dispute = escrow.disputeOrder({"from": account_2})
    tx_dispute.wait(1)
    buyer_refund = AMOUNT + DEPOSIT  # 0.01
    seller_old_balance = escrow_token.balanceOf(account_1)
    buyer_old_balance = escrow_token.balanceOf(account_2)
    admin_old_balance = account.balance()
    with pytest.raises(exceptions.VirtualMachineError):
        escrow.resolveDispute(buyer_refund, {"from": account_1})
