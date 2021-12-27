from brownie import network, config, interface, EscrowAave
from scripts import escrow_aave
from scripts.helpful_scripts import get_account
from scripts.escrow_aave.get_weth import get_weth
from web3 import Web3

# 0.1
AMOUNT = Web3.toWei(0.1, "ether")


def main():
    account = get_account()
    account_1 = get_account(index=1)
    erc20_address = config["networks"][network.show_active()]["weth_token"]
    ierc20 = interface.IERC20(erc20_address)
    if network.show_active() in ["mainnet-fork"]:
        get_weth()
    lending_pool = get_lending_pool()
    escrow_aave = EscrowAave.deploy(
        erc20_address, lending_pool.address, {"from": account}
    )
    print(f"Escrow_Aave Deployed at {escrow_aave}")
    print("Creating the Escrow transaction")
    blocks = 10
    tx_create = escrow_aave.createOrder(AMOUNT, blocks, {"from": account_1})
    tx_create.wait(1)
    print("Approving Spend of Weth")
    tx_approve = approve_erc20(AMOUNT, escrow_aave.address, erc20_address, account)
    tx_approve.wait(1)
    print("Initiating The Escrow, Depositing ...")
    tx_initiate = escrow_aave.initiateOrder({"from": account})
    tx_initiate.wait(1)
    print("Initiated!")
    print("Sending Order")
    tx_send = escrow_aave.sendOrder({"from": account_1})
    tx_send.wait(1)
    print("Sent")
    print("Receiving Order")
    tx_receive = escrow_aave.receiveOrder({"from": account})
    tx_receive.wait(1)
    print(
        f"Received ! Balance of WETH token of seller is {ierc20.balanceOf(account_1)}"
    )


def approve_erc20(amount, spender, erc20_address, account):
    print("Approving ERC20 token...")
    erc20 = interface.IERC20(erc20_address)
    tx = erc20.approve(spender, amount, {"from": account})
    tx.wait(1)
    print("Approved!")
    return tx


def get_lending_pool():
    lending_pool_addresses_provider = interface.ILendingPoolAddressesProvider(
        config["networks"][network.show_active()]["lending_pool_addresses_provider"]
    )
    lending_pool_address = lending_pool_addresses_provider.getLendingPool()
    lending_pool = interface.ILendingPool(lending_pool_address)
    return lending_pool
