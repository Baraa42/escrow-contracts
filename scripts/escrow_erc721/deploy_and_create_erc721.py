from scripts.escrow_erc20.deploy_escrow_erc20 import ADMIN_FEE
from scripts.helpful_scripts import get_account

from brownie import EscrowNFT, EscrowERC721, interface
from web3 import Web3

ADMIN_FEE = 0.005


def deploy_and_create_nft():
    account = get_account()
    escrow_nft = EscrowNFT.deploy({"from": account})
    tx = escrow_nft.createNFT({"from": account})
    tx.wait(1)
    print(
        f"Your NFT address : {escrow_nft.address} and Token Id : {escrow_nft.tokenCounter()-1} "
    )
    return escrow_nft


def deploy_escrow_erc721():
    account = get_account()
    escrow = EscrowERC721.deploy(Web3.toWei(ADMIN_FEE, "ether"), {"from": account})
    print("Escrow Deployed!")
    return escrow


def deploy_escrow_and_erc721():
    account = get_account()
    escrow_nft = deploy_and_create_nft()
    escrow = EscrowERC721.deploy(Web3.toWei(ADMIN_FEE, "ether"), {"from": account})
    print("Escrow Deployed!")
    return escrow, escrow_nft


def approve_erc721(erc721_address, tokenId, recipient, account):

    print("Approving ERC721 transfer")
    erc721 = interface.IERC20(erc721_address)
    tx = erc721.approve(recipient, tokenId, {"from": account})
    tx.wait(1)
    print("Approved !")
    return tx


def main():
    deploy_escrow_erc721()
