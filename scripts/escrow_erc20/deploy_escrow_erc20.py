from brownie import EscrowERC20, EscrowToken, interface
from scripts.helpful_scripts import get_account
from web3 import Web3


ADMIN_FEE = 0.005


def deploy_escrow_erc20():
    account = get_account()
    escrow = EscrowERC20.deploy(
        Web3.toWei(ADMIN_FEE, "ether"),
        {"from": account},
    )
    print("Escrow Deployed!")
    print(type(escrow))
    return escrow


def deploy_escrow_token():
    account = get_account()
    account_1 = get_account(index=1)
    escrow_token = EscrowToken.deploy(
        {"from": account},
    )
    print("Escrow Token deployed !")
    return escrow_token


def fund_account(escrow_token, receiver, amount):
    account = get_account()
    tx = escrow_token.transfer(receiver, amount, {"from": account})
    tx.wait(1)
    print(f"Balance of Receiver {receiver} is : {escrow_token.balanceOf(receiver)}")
    print(f"Balance of Sender {account} is : {escrow_token.balanceOf(account)}")


def approve_erc20(amount, spender, erc20_address, account):

    print("Approving ERC20 token")
    erc20 = interface.IERC20(erc20_address)
    tx = erc20.approve(spender, amount, {"from": account})
    tx.wait(1)
    print("Approved !")
    return tx


def main():
    deploy_escrow_erc20()
