// SPDX-License-Identifier: MIT

pragma solidity ^0.6.0;

import '../../interfaces/ILendingPool.sol';
import '../../interfaces/IERC20.sol';
import '../access/Ownable.sol';

/** @title EscrowAave
 *  @dev This contract implement a simple Escrow contract of an ERC20 token.
 * Tokens are deposited in Aave to earn yield while escrow contract is running.
 * Contract has an admin to settle disputes. Admin is paid adminFee for handling the escrow contract.
 * Process : Admin deploy contract. Seller create an order, sets token, amount and deposit, blockExpiry for the buyer. 
 * Buyer initiate the escrow by paying, fund are deposited in Aave. 
 * Seller sends order, buyer receives. Contract wihtdraw fund from Aave, and release `deposit` to buyer, `amount` to seller and 
 * `adminFee` to the owner.
 * If no reaction from buyer after a while, order expires and seller can withdraw funds.
 * In case of disputes admins decides how to distribute funds
 */

contract EscrowAave is Ownable  {


    address payable public buyer;
    address payable public seller;
    address public token;
    OrderStatus public status;
    uint256 public amount;
    uint256 public sendBlock;
    uint256 public numBlocksToExpire;
    /// Aave Lending pool to deposit tokens
    ILendingPool public lendingPool;
    enum OrderStatus {BLANK, CREATED, INITIATED, SENT, RECEIVED, CANCELLED, DISPUTED, RESOLVED, EXPIRED}

  
    event OrderCreated(address _seller, uint256 _amount);
    event OrderInitiated(address _buyer );
    event OrderSent(uint256 _sendBlock );
    event OrderReceived( );
    event OrderExpired( );
    event OrderCancelled(address canceller );
    event OrderDisputed(address disputer);
    event OrderResolved(bool refundBuyer);

    /**
     * @dev Throws if called by an account other than the buyer of `orders[_orderId]`
     */
    modifier onlyBuyer( ) {
        require(buyer == msg.sender, 'Only Buyer Allowed');
        _;
    }

     /**
     * @dev Throws if called by an account other than the seller of `orders[_orderId]`
     */
    
     modifier onlySeller( ) {
        require(seller == msg.sender, 'Only Seller Allowed');
        _;
    }
     /**
     * @dev Throws if called by an account other than the buyer or seller of `orders[_orderId]`
     */

    modifier onlyBuyerOrSeller() {
        require(seller == msg.sender || buyer == msg.sender, 'Only Buyer or Seller Allowed');
        _;
    }

    /**
     * @dev Initialize the contract settings : `token` and `lendingPool`
     * and owner to the deployer.
     */
    constructor(address _token, address _lendingPoolAddress) public {
        status = OrderStatus.BLANK;
        token = _token;
        lendingPool = ILendingPool(_lendingPoolAddress);

    }

    /**
     * @dev Creates a new order with status : `CREATED` and sets the escrow contract settings.
     */
    function createOrder(uint256 _amount,  uint256 _numBlocksToExpire) public {
        require(status == OrderStatus.BLANK, 'Cant create with the current status');
        require(_amount > 0, 'Amount must be positive');
        amount = _amount;
        seller = payable(msg.sender);
        numBlocksToExpire = _numBlocksToExpire;
        status = OrderStatus.CREATED;
        emit OrderCreated(msg.sender, _amount); 
    }

    /**
     * @dev Initiate the escrow and send the funds.
     * Can only be called if the order state is `CREATED`
     * Contract deposit funds to Aave
     */
    function initiateOrder() public payable {
        require(status == OrderStatus.CREATED, 'Cant Initiate with the current status');
        uint256 allowance = IERC20(token).allowance(msg.sender, address(this));
        require(allowance >= amount, "Check the token allowance");
        IERC20(token).transferFrom(msg.sender, address(this), amount);
        buyer = payable(msg.sender);
        status = OrderStatus.INITIATED;
        emit OrderInitiated(msg.sender);
        IERC20(token).approve(address(lendingPool), amount);
        lendingPool.deposit(token, amount, address(this),0);
    }

    /**
     * @dev Change the order status to `SENT`. Only the seller can call it.
     */
    function sendOrder() public onlySeller() {
        require(status == OrderStatus.INITIATED, "Can't send order now");
        status = OrderStatus.SENT;
        sendBlock = block.number;
        emit OrderSent(sendBlock);
    }

    
    /**
     * @dev Change the order status to `RECEIVED`. Only the buyer can call it.
     * Withdraw tokens from Aave
     * Releases tokens and funds to buyer and seller and admin.
     * Can only be called if the order status is `SENT`
     */
    function receiveOrder() public onlyBuyer() {
        require(status == OrderStatus.SENT, "Can't receive order now");
        status = OrderStatus.RECEIVED;
        emit OrderReceived();
        // add Aave logic 
        lendingPool.withdraw(token, type(uint).max, seller);
    }

    /**
     * @dev Change the order status to `EXPIRED`. Only the seller of that order can call it.
     * Withdraw tokens from Aave
     * Can only be called if time after sending the order is bigger than `numBlocksToExpire` .
     * Can only be called if the order status is `SENT`.
     * Release funds to seller and admin, buyer loses deposit.
     */
    function expireOrder() public onlySeller() {
        require(status == OrderStatus.SENT, "Order not sent");
        require(sendBlock + numBlocksToExpire < block.number, 'Order not expired yet');
        status = OrderStatus.EXPIRED;
        emit OrderExpired();
        // Add aave logic
        lendingPool.withdraw(token, type(uint).max, seller); 
    }

    /**
    * @dev Change order status to`DISPUTED`. Only the seller or buyer of that order can call it.
    * Can only be called if order is in state `SENT`.
    */
    function disputeOrder( ) public onlyBuyerOrSeller() {
        require(status == OrderStatus.SENT, "Can't dispute order now");
        status = OrderStatus.DISPUTED;
        emit OrderDisputed(msg.sender);
    }

    /**
    * @dev Change order status to `RESOLVED`. Only the owner of the contract can call it.
    * Can only be called if order is in state `DISPUTED`.
    * Withdraw from aave
    * Release funds the parties according to distribution.
    */
    function resolveDispute(bool refundBuyer ) public onlyOwner() {
        require(status == OrderStatus.DISPUTED, 'Cant resolve order');
        status = OrderStatus.RESOLVED;
        emit OrderResolved(refundBuyer);

        if(refundBuyer){
            lendingPool.withdraw(token, type(uint).max, buyer);
        } else {
            lendingPool.withdraw(token, type(uint).max, seller);
        }

    }


}