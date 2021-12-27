// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;


import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

/** @title EscrowERC20
 *  @dev This contract implement a simple Escrow contract of an ERC20 token.
 * Contract has an admin to settle disputes. Admin is paid adminFee for handling the escrow contract.
 * Process : Admin deploy contract. Seller create an order, sets token, amount and deposit, blockExpiry for the buyer. Buyer initiate the escrow by paying. Seller
 * sends order, buyer receives. Contract release funds, `deposit` to buyer, `amount` to seller and 
 * `adminFee` to the owner.
 * If no reaction from buyer after a while, order expires and seller can withdraw funds.
 * Orders can be cancelled by seller or buyer if in an appropriate status.
 * In case of disputes admins decides how to distribute funds
 */
contract EscrowERC20 is Ownable {


    address payable public buyer;
    address payable public seller;
    address public token;
    OrderStatus public status;
    uint256 public adminFee;
    uint256 public amount;
    /// @dev deposit is set to incentivize buyer to release funds early
    uint256 public deposit;
    /// @dev block when seller sent the order
    uint256 public sendBlock;
    uint256 public numBlocksToExpire; 
    
    enum OrderStatus {BLANK, CREATED, INITIATED, SENT, RECEIVED, CANCELLED, DISPUTED, RESOLVED, EXPIRED}


    event OrderCreated(address _seller, uint256 _amount, uint256 _deposit);
    event OrderInitiated(address _buyer);
    event OrderSent(uint256 _block);
    event OrderReceived();
    event OrderExpired();
    event OrderCancelled(address canceller);
    event OrderDisputed(address disputer);
    event OrderResolved(uint256 buyerRefund, uint256 sellerRefund);

    /**
     * @dev Throws if called by an account other than the buyer of `orders[_orderId]`
     */
    modifier onlyBuyer() {
        require(buyer == msg.sender, 'Only Buyer Allowed');
        _;
    }
    
    /**
     * @dev Throws if called by an account other than the seller of `orders[_orderId]`
     */
    modifier onlySeller() {
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
     * @dev Initialize the contract settings, and owner to the deployer.
     */

    constructor(uint256 _adminFee)  {
        buyer = payable(address(0));
        seller = payable(address(0));
        amount = 0;
        deposit = 0;
        sendBlock = block.number;
        numBlocksToExpire = 1;
        status = OrderStatus.BLANK;
        adminFee = _adminFee;
    }

    /**
     * @dev Creates a new order with status : `CREATED` and sets the escrow contract settings.
     */
    function createOrder(address _token, uint256 _amount, uint256 _deposit, uint256 _numBlocksToExpire ) public {
        require(seller == address(0), 'Order already Created');
        require(status == OrderStatus.BLANK, 'Cant create with the current status');
        require(_amount > 0, 'Order Too Small');
        require(_amount > _deposit, 'Deposit must be smaller than amount');
        
        token = _token;
        amount = _amount;
        deposit = _deposit;
        seller = payable(msg.sender);
        numBlocksToExpire = _numBlocksToExpire;
        
        status = OrderStatus.CREATED;
        emit OrderCreated(msg.sender, _amount, _deposit);
        
    }

    /**
     * @dev Initiate the escrow and send the funds.
     * Can only be called if the order state is `CREATED`
     */
    function initiateOrder() public payable {
        require(buyer == address(0), 'Buyer already exists');
        require(status == OrderStatus.CREATED, 'Cant Initiate with the current status');
        require(msg.value ==adminFee, 'Not enough fund for fee' );

        IERC20(token).transferFrom(msg.sender, address(this), amount + deposit);

        buyer = payable(msg.sender);
        status = OrderStatus.INITIATED;
        emit OrderInitiated(msg.sender);
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
     * Releases tokens and funds to buyer and seller and admin.
     * Can only be called if the order status is `SENT`
     */
    function receiveOrder( ) public onlyBuyer() {
        require(status == OrderStatus.SENT, "Can't receive order now");
        status = OrderStatus.RECEIVED;
        emit OrderReceived();
        IERC20(token).transfer(buyer, deposit);
        IERC20(token).transfer(seller, amount);
        payable(owner()).transfer(adminFee);
        
    }

     /**
     * @dev Change the order status to `EXPIRED`. Only the seller of that order can call it.
     * Can only be called if time after sending the order is bigger than `numBlocksToExpire` .
     * Can only be called if the order status is `SENT`.
     * Release funds to seller and admin, buyer loses deposit.
     */
    function expireOrder() public onlySeller() {
        require(status == OrderStatus.SENT, "Order not sent");
        require(sendBlock + numBlocksToExpire < block.number, 'Order not expired yet');
        status = OrderStatus.EXPIRED;
        emit OrderExpired();
        IERC20(token).transfer(seller, amount + deposit);
        payable(owner()).transfer(adminFee);
    }

    /**
     * @dev Change order status to `CANCELLED`. Only the buyer of that order can call it.
     * Can only be called if order is in state `INITIATED`.
     * Release funds to buyer and admin.
     */
    function cancelBuyOrder( ) public onlyBuyer() {
        require(status == OrderStatus.INITIATED, "Can't cancell order now");
        status = OrderStatus.CREATED;
        buyer = payable(address(0));
        emit OrderCancelled(msg.sender);
        IERC20(token).transfer(payable(msg.sender), amount + deposit); 
        payable(owner()).transfer(adminFee); 
    }
        
    /**
    * @dev Change order status to `CANCELLED`. Only the seller of that order can call it.
    * Can only be called if order is in state `INITIATED`, `CREATED` or `SENT`.
    * If the order is in state `INITIATED` or `SENT` funds are sent back to the buyer.
    * This is only case where admin collect no fees.
    */
    function cancelSellOrder( ) public onlySeller() {
        require(status == OrderStatus.CREATED || status == OrderStatus.INITIATED || status == OrderStatus.SENT, "Can't cancell order now");
        OrderStatus old_status = status;
        status = OrderStatus.CANCELLED;
        emit OrderCancelled(msg.sender);

        if( old_status == OrderStatus.INITIATED || old_status == OrderStatus.SENT) {
            uint256 refund = amount + deposit;
            IERC20(token).transfer(buyer, amount + deposit);
            buyer.transfer(adminFee);
        }
        
        
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
    * Release funds the parties according to distribution.
    */
    function resolveDispute(uint256 refundToBuyer) public onlyOwner() {
        require(refundToBuyer  < amount + deposit, 'High refund' );
        require(status == OrderStatus.DISPUTED, 'Cant resolve order');
        uint256 refundToSeller = amount + deposit - refundToBuyer ;
        status = OrderStatus.RESOLVED;
        emit OrderResolved(refundToBuyer, refundToSeller);
        IERC20(token).transfer(buyer, refundToBuyer);
        IERC20(token).transfer(seller, refundToSeller);
        payable(owner()).transfer(adminFee);

    }


  

}