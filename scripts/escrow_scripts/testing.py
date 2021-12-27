from scripts.helpful_scripts import get_account
from web3 import Web3
from scripts.deploy_escrow import deploy_escrow, MIN_ORDER, DISPUTE_FEE
from scripts.helpful_scripts import get_account


def test_can_expire_order():
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
    print(f"block_send : {block_send}")
    seller_old_balance = account.balance()
    buyer_old_balance = account_1.balance()
    tx_expire = escrow.expireOrder(0, {"from": account})
    tx_expire.wait(1)
    block_expire = tx_expire.block_number
    print(f"block_expire : {block_expire}")


def main():
    test_can_expire_order()
