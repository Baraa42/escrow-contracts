# Escrow - contracts



## The Contracts

The repo contain 4 main contracts. 

### Escrow.sol
This contract implement an escrow mechanism, after deployment any user can create an escrow order. The order is appended to the Orders array. Contract has an admin to settle disputes, for each dispute a disputeFee is charged by the admin.

**Process** 
  1. Admin deploy, sets : `disputeFee`, `minOrderAmount`, `numBlocksToExpire`.
  2. Seller create an order, sets : `amount`, `deposit`.
  3. Buyer initiate the order, sends funds : `amount` + `deposit`.
  4. Seller send the order.
  5. Buyer receives the order, contract release `amount` to seller and `deposit` to buyer.
  
**Buyer can**
  1. Cancel order after initiating ( before seller sends )
  2. Dispute order after seller sends.

**Seller can**
  1. Cancel order after seller creates / buyer initiate / seller sends.
  2. Dispute order after seller sends.
  3. Expire order after sending, if user dont confirm reception and time after `sending > numBlocksToExpire`.
  
**Admin/Owner can**
  1. Solve dispute after order is disputed.
  
**Params** 
  1. `disputeFee` : Collected by admin to resolve dispute.
  2. `minOrderAmount` : min amount to create an order.
  3. `numBlocksToExpire` : Number of blocks for the order to expire after the seller sends.
  4. `sendBlock` : The block number when the order was sent by the seller.
  5. `deposit` : Is set to incentivize buyer to confirm reception early.

### EscrowERC20.sol
This contract implement an ERC20 token escrow mechanism, after deployment the user can create an escrow order.

**Process**
  1. Admin deploy, sets : `adminFee`.
  2. Seller create an order, sets : token, `amount`, `deposit`.
  3. Buyer initiate the order, sends funds : `amount` + `deposit` + `adminFee`.
  4. Seller send the order.
  5. Buyer receives the order, contract release amount to seller, deposit to buyer and adminFee to the owner.

**Buyer can**
  1. Cancel order after initiating ( before seller sends )
  2. Dispute order after seller sends.

**Seller can**
  1. Cancel order after seller creates / buyer initiate / seller sends.
  2. Dispute order after seller sends.
  3. Expire order after sending, if user dont confirm reception and time after sending > `numBlocksToExpire`.
  
**Admin/Owner can**
  1. Solve dispute after order is disputed.

**Params**
  1. `adminFee` : Collected by admin to deploy contract and solve issues.
  2. `token` : ERC20 token address.
  3. `numBlocksToExpire` : Number of blocks for the order to expire after the seller sends.
  4. `sendBlock` : The block number when the order was sent by the seller.
  5. `deposit` : Is set to incentivize buyer to confirm reception early.

### EscrowERC721.sol
Similar to `ERC20.sol`.

**New Params** : 
  1. `tokenContract` : ERC721 token contract address.
  2. `tokenId` : token id.
 
### EscrowAave.sol
Similar to `ERC20.sol` with the additional functionality the tokens are deposited in Aave to earn yield while escrow contract is running. And opposite to `ERC20.sol`, only Refund Buyer or Refund Seller is supported when resolving dispute. Haven't implemented dividing the funds functionality but it's straightforward...
 
## Tests
All tests are written with `brownie`.  

### Escrow.sol : 
Local testing using Ganache.
Test Process : 
  * Unit testing all functionalities.

### EscrowERC20.sol : 
Local testing using Ganache.
Test Process : 
  1. Deploying an ERC20 'ESCRW' Token, it's contract is in the 'contracts/test' directory.
  2. Unit testing all functionalities with this ESCRW token.
  
### EscrowERC721.sol : 
Local testing using Ganache.
Test Process : 
  1. Deploying an ERC721 'ESCRW' Token, it's contract is in the 'contracts/test' directory.
  2. Unit testing all functionalities with this ESCRW NFT.
 
### EscrowAave.sol : 
Local testing using mainnet-fork.
No unit test yet, deployed contract on mainnet-fork and tested the escrow process with a script end to end using the `weth` token. Worked fine, but need to test the rest of functionalities.  



    
    
## Compononets used
1. Node JS  (everything was tested under `v14.18.1`) 
2. Brownie  - ( the version used is `v1.17.2`) :
2. Ganache CLI ( the version used is `v6.12.2` )   :
