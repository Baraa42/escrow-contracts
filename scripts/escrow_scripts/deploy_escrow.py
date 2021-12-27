from brownie import Escrow
from scripts.helpful_scripts import get_account
from web3 import Web3

MIN_ORDER = 0.01
DISPUTE_FEE = 0.005
EXPIRY_BLOCKS = 1


def deploy_escrow(expiry_blocks=1):
    account = get_account()
    escrow = Escrow.deploy(
        Web3.toWei(MIN_ORDER, "ether"),
        Web3.toWei(DISPUTE_FEE, "ether"),
        expiry_blocks,
        {"from": account},
    )
    print("Escrow Deployed!")
    return escrow


def main():
    deploy_escrow()
