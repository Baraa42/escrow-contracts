from scripts.escrow_erc721.deploy_and_create_erc721 import (
    deploy_and_create_nft,
    deploy_escrow_erc721,
    deploy_escrow_and_erc721,
    approve_erc721,
    ADMIN_FEE,
)

from scripts.helpful_scripts import get_account, LOCAL_BLOCKCHAIN_ENVIRONMENTS
from brownie import network, exceptions, interface
import pytest
from web3 import Web3

zero_address = "0x0000000000000000000000000000000000000000"
AMOUNT = 10
DEPOSIT = 0.1
BLOCKS = 10


def test_deploy_escrow_erc721():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    escrow = deploy_escrow_erc721()
    admin_fee = Web3.toWei(ADMIN_FEE, "ether")
    assert escrow.owner() == account
    assert escrow.buyer() == zero_address
    assert escrow.seller() == zero_address
    assert escrow.status() == 0
    assert escrow.deposit() == 0
    assert escrow.numBlocksToExpire() == 1
    assert escrow.adminFee() == admin_fee
    print("Test Deploy OK!")


def test_deploy_escrow_nft():
    account = get_account()
    escrow_nft = deploy_and_create_nft()
    erc721 = interface.IERC721(escrow_nft)

    assert escrow_nft.tokenCounter() == 1
    assert erc721.ownerOf(0) == account


def test_can_create_order_erc721():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    escrow, escrow_nft = deploy_escrow_and_erc721()
    blocks = 10
    deposit = Web3.toWei(DEPOSIT, "ether")
    tx = escrow.createOrder(escrow_nft, 0, deposit, blocks, {"from": account})
    tx.wait(1)
    assert escrow.tokenContract() == escrow_nft
    assert escrow.tokenId() == 0
    assert escrow.deposit() == deposit
    assert escrow.numBlocksToExpire() == blocks
    assert escrow.seller() == account
    assert escrow.buyer() == zero_address
    assert escrow.status() == 1


def test_can_initiate_order_erc721():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    escrow, escrow_nft = deploy_escrow_and_erc721()
    blocks = 10
    deposit = Web3.toWei(DEPOSIT, "ether")
    admin_fee = Web3.toWei(ADMIN_FEE, "ether")
    tx_create = escrow.createOrder(escrow_nft, 0, deposit, blocks, {"from": account_1})
    tx_create.wait(1)
    tx_approve = approve_erc721(escrow_nft, 0, escrow, account)
    tx_approve.wait(1)
    tx_initiate = escrow.initiateOrder({"from": account, "value": deposit + admin_fee})
    tx_initiate.wait(1)
    erc721 = interface.IERC721(escrow_nft)
    assert escrow.buyer() == account
    assert erc721.ownerOf(0) == escrow
    assert escrow.status() == 2


def test_can_send_order_erc721():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    escrow, escrow_nft = deploy_escrow_and_erc721()
    blocks = 10
    deposit = Web3.toWei(DEPOSIT, "ether")
    admin_fee = Web3.toWei(ADMIN_FEE, "ether")
    tx_create = escrow.createOrder(escrow_nft, 0, deposit, blocks, {"from": account_1})
    tx_create.wait(1)
    tx_approve = approve_erc721(escrow_nft, 0, escrow, account)
    tx_approve.wait(1)
    tx_initiate = escrow.initiateOrder({"from": account, "value": deposit + admin_fee})
    tx_initiate.wait(1)
    tx_send = escrow.sendOrder({"from": account_1})
    tx_send.wait(1)
    send_block = tx_send.block_number
    assert escrow.status() == 3
    assert escrow.sendBlock() == send_block


def test_only_seller_can_send_order_erc721():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    account_2 = get_account(index=2)
    escrow, escrow_nft = deploy_escrow_and_erc721()
    blocks = 10
    deposit = Web3.toWei(DEPOSIT, "ether")
    admin_fee = Web3.toWei(ADMIN_FEE, "ether")
    tx_create = escrow.createOrder(escrow_nft, 0, deposit, blocks, {"from": account_1})
    tx_create.wait(1)
    tx_approve = approve_erc721(escrow_nft, 0, escrow, account)
    tx_approve.wait(1)
    tx_initiate = escrow.initiateOrder({"from": account, "value": deposit + admin_fee})
    tx_initiate.wait(1)
    with pytest.raises(exceptions.VirtualMachineError):
        escrow.sendOrder({"from": account_2})


def test_can_receive_order_erc721():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    escrow, escrow_nft = deploy_escrow_and_erc721()
    blocks = 10
    deposit = Web3.toWei(DEPOSIT, "ether")
    admin_fee = Web3.toWei(ADMIN_FEE, "ether")
    tx_create = escrow.createOrder(escrow_nft, 0, deposit, blocks, {"from": account_1})
    tx_create.wait(1)
    tx_approve = approve_erc721(escrow_nft, 0, escrow, account)
    tx_approve.wait(1)
    tx_initiate = escrow.initiateOrder({"from": account, "value": deposit + admin_fee})
    tx_initiate.wait(1)
    tx_send = escrow.sendOrder({"from": account_1})
    tx_send.wait(1)
    buyer_old_balance = account.balance()
    tx_receive = escrow.receiveOrder({"from": account})
    tx_receive.wait(1)
    erc721 = interface.IERC721(escrow_nft)
    assert erc721.ownerOf(0) == account_1
    assert account.balance() == buyer_old_balance + admin_fee + deposit
    assert escrow.status() == 4


def test_can_expire_order_erc721():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    escrow, escrow_nft = deploy_escrow_and_erc721()
    deposit = Web3.toWei(DEPOSIT, "ether")
    admin_fee = Web3.toWei(ADMIN_FEE, "ether")
    tx_create = escrow.createOrder(escrow_nft, 0, deposit, 0, {"from": account_1})
    tx_create.wait(1)
    tx_approve = approve_erc721(escrow_nft, 0, escrow, account)
    tx_approve.wait(1)
    tx_initiate = escrow.initiateOrder({"from": account, "value": deposit + admin_fee})
    tx_initiate.wait(1)
    tx_send = escrow.sendOrder({"from": account_1})
    tx_send.wait(1)
    seller_old_balance = account_1.balance()
    buyer_old_balance = account.balance()
    tx_expire = escrow.expireOrder({"from": account_1})
    tx_expire.wait(1)
    erc721 = interface.IERC721(escrow_nft)
    assert erc721.ownerOf(0) == account_1
    assert account.balance() == buyer_old_balance + admin_fee
    assert account_1.balance() == seller_old_balance + deposit
    assert escrow.status() == 8


def test_cant_expire_order_erc721():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    escrow, escrow_nft = deploy_escrow_and_erc721()
    deposit = Web3.toWei(DEPOSIT, "ether")
    admin_fee = Web3.toWei(ADMIN_FEE, "ether")
    blocks = BLOCKS
    tx_create = escrow.createOrder(escrow_nft, 0, deposit, blocks, {"from": account_1})
    tx_create.wait(1)
    tx_approve = approve_erc721(escrow_nft, 0, escrow, account)
    tx_approve.wait(1)
    tx_initiate = escrow.initiateOrder({"from": account, "value": deposit + admin_fee})
    tx_initiate.wait(1)
    tx_send = escrow.sendOrder({"from": account_1})
    tx_send.wait(1)
    with pytest.raises(exceptions.VirtualMachineError):
        escrow.expireOrder({"from": account_1})


def test_buyer_can_cancel_order_before_send_erc721():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    escrow, escrow_nft = deploy_escrow_and_erc721()
    deposit = Web3.toWei(DEPOSIT, "ether")
    admin_fee = Web3.toWei(ADMIN_FEE, "ether")
    blocks = BLOCKS
    tx_create = escrow.createOrder(escrow_nft, 0, deposit, blocks, {"from": account_1})
    tx_create.wait(1)
    tx_approve = approve_erc721(escrow_nft, 0, escrow, account)
    tx_approve.wait(1)
    tx_initiate = escrow.initiateOrder({"from": account, "value": deposit + admin_fee})
    tx_initiate.wait(1)
    admin_old_eth_balance = account.balance()
    tx_cancel = escrow.cancelBuyOrder({"from": account})
    tx_cancel.wait(1)
    erc721 = interface.IERC721(escrow_nft)
    assert erc721.ownerOf(0) == account
    assert account.balance() == admin_old_eth_balance + admin_fee + deposit
    assert escrow.status() == 5


def test_seller_can_cancel_order_after_create_erc721():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account_1 = get_account(index=1)
    escrow, escrow_nft = deploy_escrow_and_erc721()
    deposit = Web3.toWei(DEPOSIT, "ether")
    admin_fee = Web3.toWei(ADMIN_FEE, "ether")
    blocks = BLOCKS
    tx_create = escrow.createOrder(escrow_nft, 0, deposit, blocks, {"from": account_1})
    tx_create.wait(1)
    tx_cancel = escrow.cancelSellOrder({"from": account_1})
    tx_cancel.wait(1)
    assert escrow.status() == 5


def test_seller_can_cancel_order_after_initiate_erc721():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    escrow, escrow_nft = deploy_escrow_and_erc721()
    deposit = Web3.toWei(DEPOSIT, "ether")
    admin_fee = Web3.toWei(ADMIN_FEE, "ether")
    blocks = BLOCKS
    tx_create = escrow.createOrder(escrow_nft, 0, deposit, blocks, {"from": account_1})
    tx_create.wait(1)
    tx_approve = approve_erc721(escrow_nft, 0, escrow, account)
    tx_approve.wait(1)
    tx_initiate = escrow.initiateOrder({"from": account, "value": deposit + admin_fee})
    tx_initiate.wait(1)
    buyer_old_balance = account.balance()
    tx_cancel = escrow.cancelSellOrder({"from": account_1})
    tx_cancel.wait(1)
    erc721 = interface.IERC721(escrow_nft)
    assert erc721.ownerOf(0) == account
    assert escrow.status() == 5
    assert account.balance() == buyer_old_balance + deposit + admin_fee


def test_seller_can_cancel_order_after_send_erc721():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    escrow, escrow_nft = deploy_escrow_and_erc721()
    deposit = Web3.toWei(DEPOSIT, "ether")
    admin_fee = Web3.toWei(ADMIN_FEE, "ether")
    blocks = BLOCKS
    tx_create = escrow.createOrder(escrow_nft, 0, deposit, blocks, {"from": account_1})
    tx_create.wait(1)
    tx_approve = approve_erc721(escrow_nft, 0, escrow, account)
    tx_approve.wait(1)
    tx_initiate = escrow.initiateOrder({"from": account, "value": deposit + admin_fee})
    tx_initiate.wait(1)
    tx_send = escrow.sendOrder({"from": account_1})
    tx_send.wait(1)
    buyer_old_balance = account.balance()
    tx_cancel = escrow.cancelSellOrder({"from": account_1})
    tx_cancel.wait(1)
    erc721 = interface.IERC721(escrow_nft)
    assert erc721.ownerOf(0) == account
    assert escrow.status() == 5
    assert account.balance() == buyer_old_balance + deposit + admin_fee


def test_buyer_can_dispute_order_after_send_erc721():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    escrow, escrow_nft = deploy_escrow_and_erc721()
    deposit = Web3.toWei(DEPOSIT, "ether")
    admin_fee = Web3.toWei(ADMIN_FEE, "ether")
    blocks = BLOCKS
    tx_create = escrow.createOrder(escrow_nft, 0, deposit, blocks, {"from": account_1})
    tx_create.wait(1)
    tx_approve = approve_erc721(escrow_nft, 0, escrow, account)
    tx_approve.wait(1)
    tx_initiate = escrow.initiateOrder({"from": account, "value": deposit + admin_fee})
    tx_initiate.wait(1)
    tx_send = escrow.sendOrder({"from": account_1})
    tx_send.wait(1)
    tx_dispute = escrow.disputeOrder({"from": account})
    tx_dispute.wait(1)
    assert escrow.status() == 6


def test_seller_can_dispute_order_after_send_erc721():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    escrow, escrow_nft = deploy_escrow_and_erc721()
    deposit = Web3.toWei(DEPOSIT, "ether")
    admin_fee = Web3.toWei(ADMIN_FEE, "ether")
    blocks = BLOCKS
    tx_create = escrow.createOrder(escrow_nft, 0, deposit, blocks, {"from": account_1})
    tx_create.wait(1)
    tx_approve = approve_erc721(escrow_nft, 0, escrow, account)
    tx_approve.wait(1)
    tx_initiate = escrow.initiateOrder({"from": account, "value": deposit + admin_fee})
    tx_initiate.wait(1)
    tx_send = escrow.sendOrder({"from": account_1})
    tx_send.wait(1)
    tx_dispute = escrow.disputeOrder({"from": account_1})
    tx_dispute.wait(1)
    assert escrow.status() == 6


def test_stranger_cant_dispute_order_erc721():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    stranger = get_account(index=2)
    escrow, escrow_nft = deploy_escrow_and_erc721()
    deposit = Web3.toWei(DEPOSIT, "ether")
    admin_fee = Web3.toWei(ADMIN_FEE, "ether")
    blocks = BLOCKS
    tx_create = escrow.createOrder(escrow_nft, 0, deposit, blocks, {"from": account_1})
    tx_create.wait(1)
    tx_approve = approve_erc721(escrow_nft, 0, escrow, account)
    tx_approve.wait(1)
    tx_initiate = escrow.initiateOrder({"from": account, "value": deposit + admin_fee})
    tx_initiate.wait(1)
    tx_send = escrow.sendOrder({"from": account_1})
    tx_send.wait(1)
    with pytest.raises(exceptions.VirtualMachineError):
        escrow.disputeOrder({"from": stranger})


def test_buyer_cant_cancel_order_after_send_erc721():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    escrow, escrow_nft = deploy_escrow_and_erc721()
    deposit = Web3.toWei(DEPOSIT, "ether")
    admin_fee = Web3.toWei(ADMIN_FEE, "ether")
    blocks = BLOCKS
    tx_create = escrow.createOrder(escrow_nft, 0, deposit, blocks, {"from": account_1})
    tx_create.wait(1)
    tx_approve = approve_erc721(escrow_nft, 0, escrow, account)
    tx_approve.wait(1)
    tx_initiate = escrow.initiateOrder({"from": account, "value": deposit + admin_fee})
    tx_initiate.wait(1)
    tx_send = escrow.sendOrder({"from": account_1})
    tx_send.wait(1)
    with pytest.raises(exceptions.VirtualMachineError):
        escrow.cancelBuyOrder({"from": account})


def test_admin_can_resolve_dispute_erc721_frist_case():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    account_2 = get_account(index=2)
    escrow, escrow_nft = deploy_escrow_and_erc721()
    erc721 = interface.IERC721(escrow_nft)
    erc721.transferFrom(account, account_2, 0, {"from": account})
    deposit = Web3.toWei(DEPOSIT, "ether")
    admin_fee = Web3.toWei(ADMIN_FEE, "ether")
    blocks = BLOCKS
    tx_create = escrow.createOrder(escrow_nft, 0, deposit, blocks, {"from": account_1})
    tx_create.wait(1)
    tx_approve = approve_erc721(escrow_nft, 0, escrow, account_2)
    tx_approve.wait(1)
    tx_initiate = escrow.initiateOrder(
        {"from": account_2, "value": deposit + admin_fee}
    )
    tx_initiate.wait(1)
    tx_send = escrow.sendOrder({"from": account_1})
    tx_send.wait(1)
    tx_dispute = escrow.disputeOrder({"from": account_2})
    tx_dispute.wait(1)
    buyer_refund_token = True  # 0.01
    buyer_refund_deposit = False
    seller_old_balance = account_1.balance()
    admin_old_balance = account.balance()
    tx_resolve = escrow.resolveDispute(
        buyer_refund_token, buyer_refund_deposit, {"from": account}
    )
    tx_resolve.wait(1)
    assert erc721.ownerOf(0) == account_2
    assert account.balance() == admin_old_balance + admin_fee
    assert account_1.balance() == seller_old_balance + deposit
    assert escrow.status() == 7


def test_admin_can_resolve_dispute_erc721_second_case():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    account_2 = get_account(index=2)
    escrow, escrow_nft = deploy_escrow_and_erc721()
    erc721 = interface.IERC721(escrow_nft)
    erc721.transferFrom(account, account_2, 0, {"from": account})
    deposit = Web3.toWei(DEPOSIT, "ether")
    admin_fee = Web3.toWei(ADMIN_FEE, "ether")
    blocks = BLOCKS
    tx_create = escrow.createOrder(escrow_nft, 0, deposit, blocks, {"from": account_1})
    tx_create.wait(1)
    tx_approve = approve_erc721(escrow_nft, 0, escrow, account_2)
    tx_approve.wait(1)
    tx_initiate = escrow.initiateOrder(
        {"from": account_2, "value": deposit + admin_fee}
    )
    tx_initiate.wait(1)
    tx_send = escrow.sendOrder({"from": account_1})
    tx_send.wait(1)
    tx_dispute = escrow.disputeOrder({"from": account_2})
    tx_dispute.wait(1)
    buyer_refund_token = True  # 0.01
    buyer_refund_deposit = True
    buyer_old_balance = account_2.balance()
    admin_old_balance = account.balance()
    tx_resolve = escrow.resolveDispute(
        buyer_refund_token, buyer_refund_deposit, {"from": account}
    )
    tx_resolve.wait(1)
    assert erc721.ownerOf(0) == account_2
    assert account.balance() == admin_old_balance + admin_fee
    assert account_2.balance() == buyer_old_balance + deposit
    assert escrow.status() == 7


def test_admin_can_resolve_dispute_erc721_third_case():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    account_2 = get_account(index=2)
    escrow, escrow_nft = deploy_escrow_and_erc721()
    erc721 = interface.IERC721(escrow_nft)
    erc721.transferFrom(account, account_2, 0, {"from": account})
    deposit = Web3.toWei(DEPOSIT, "ether")
    admin_fee = Web3.toWei(ADMIN_FEE, "ether")
    blocks = BLOCKS
    tx_create = escrow.createOrder(escrow_nft, 0, deposit, blocks, {"from": account_1})
    tx_create.wait(1)
    tx_approve = approve_erc721(escrow_nft, 0, escrow, account_2)
    tx_approve.wait(1)
    tx_initiate = escrow.initiateOrder(
        {"from": account_2, "value": deposit + admin_fee}
    )
    tx_initiate.wait(1)
    tx_send = escrow.sendOrder({"from": account_1})
    tx_send.wait(1)
    tx_dispute = escrow.disputeOrder({"from": account_2})
    tx_dispute.wait(1)
    buyer_refund_token = False  # 0.01
    buyer_refund_deposit = True
    buyer_old_balance = account_2.balance()
    admin_old_balance = account.balance()
    tx_resolve = escrow.resolveDispute(
        buyer_refund_token, buyer_refund_deposit, {"from": account}
    )
    tx_resolve.wait(1)
    assert erc721.ownerOf(0) == account_1
    assert account.balance() == admin_old_balance + admin_fee
    assert account_2.balance() == buyer_old_balance + deposit
    assert escrow.status() == 7


def test_admin_can_resolve_dispute_erc721_fourth_case():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    account_2 = get_account(index=2)
    escrow, escrow_nft = deploy_escrow_and_erc721()
    erc721 = interface.IERC721(escrow_nft)
    erc721.transferFrom(account, account_2, 0, {"from": account})
    deposit = Web3.toWei(DEPOSIT, "ether")
    admin_fee = Web3.toWei(ADMIN_FEE, "ether")
    blocks = BLOCKS
    tx_create = escrow.createOrder(escrow_nft, 0, deposit, blocks, {"from": account_1})
    tx_create.wait(1)
    tx_approve = approve_erc721(escrow_nft, 0, escrow, account_2)
    tx_approve.wait(1)
    tx_initiate = escrow.initiateOrder(
        {"from": account_2, "value": deposit + admin_fee}
    )
    tx_initiate.wait(1)
    tx_send = escrow.sendOrder({"from": account_1})
    tx_send.wait(1)
    tx_dispute = escrow.disputeOrder({"from": account_2})
    tx_dispute.wait(1)
    buyer_refund_token = False  # 0.01
    buyer_refund_deposit = False
    seller_old_balance = account_1.balance()
    admin_old_balance = account.balance()
    tx_resolve = escrow.resolveDispute(
        buyer_refund_token, buyer_refund_deposit, {"from": account}
    )
    tx_resolve.wait(1)
    assert erc721.ownerOf(0) == account_1
    assert account.balance() == admin_old_balance + admin_fee
    assert account_1.balance() == seller_old_balance + deposit
    assert escrow.status() == 7


def test_non_admin_cant_resolve_dispute_erc721():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    account_1 = get_account(index=1)
    account_2 = get_account(index=2)
    escrow, escrow_nft = deploy_escrow_and_erc721()
    erc721 = interface.IERC721(escrow_nft)
    erc721.transferFrom(account, account_2, 0, {"from": account})
    deposit = Web3.toWei(DEPOSIT, "ether")
    admin_fee = Web3.toWei(ADMIN_FEE, "ether")
    blocks = BLOCKS
    tx_create = escrow.createOrder(escrow_nft, 0, deposit, blocks, {"from": account_1})
    tx_create.wait(1)
    tx_approve = approve_erc721(escrow_nft, 0, escrow, account_2)
    tx_approve.wait(1)
    tx_initiate = escrow.initiateOrder(
        {"from": account_2, "value": deposit + admin_fee}
    )
    tx_initiate.wait(1)
    tx_send = escrow.sendOrder({"from": account_1})
    tx_send.wait(1)
    tx_dispute = escrow.disputeOrder({"from": account_2})
    tx_dispute.wait(1)
    buyer_refund_token = False  # 0.01
    buyer_refund_deposit = False
    with pytest.raises(exceptions.VirtualMachineError):
        escrow.resolveDispute(
            buyer_refund_token, buyer_refund_deposit, {"from": account_1}
        )
