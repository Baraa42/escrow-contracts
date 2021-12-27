// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;


import "@openzeppelin/contracts/access/Ownable.sol";


/** @title Escrow
 *  @dev This contract implement an escrow mechanism, after deployment any user can create an escrow order.
 * Contract has an admin to settle disputes, for each dispute a disputeFee is charged by the admin.
 * Process : Seller create an order, sets amount and deposit for the buyer. Buyer initiate the escrow by paying. Seller
 * sends order, buyer receives. Contract release funds, deposit to buyer and amount to seller.
 * If no reaction from buyer after a while, order expires and seller can withdraw funds.
 * Orders can be cancelled by seller or buyer if in an appropriate status.
 * In case of disputes admins decides how to distribute funds
 */
contract Escrow is Ownable {


    /// fee charged by admin to handle a dispute
    uint256 public disputeFee;
    /// minimum amount to create an order
    uint256 public minOrderAmount;
    /// number of blocks for the order to expire after seller send it
    uint256 public numBlocksToExpire; 
    /// tracks num of orders
    uint256 public orderCount; 
    /// Array holding all orders
    Order[] public orders;
    /// track all disputed orders by orderId for admin to resolve
    uint256[] public disputedOrdersId; 
    
    
    enum OrderStatus {CREATED, INITIATED, SENT, RECEIVED, CANCELLED, DISPUTED, RESOLVED, EXPIRED}

    /// @dev struct representing the order/escrow
    /// @param sendBlock representing the block when the order was sent by seller.
    struct Order {
        OrderStatus status;
        address payable buyer;
        address payable seller;
        uint256 amount;
        uint256 deposit;
        uint256 orderId;
        uint256 sendBlock;
    }

    event OrderCreated(address _seller, uint256 _amount, uint256 _deposit, uint256 _orderId);
    event OrderInitiated(address buyer, uint256 _orderId);
    event OrderSent(uint256 _orderId, uint256 _sendBlock);
    event OrderReceived(uint256 _orderId);
    event OrderExpired(uint256 _orderId);
    event OrderCancelled(address canceller, uint256 _orderId, OrderStatus _statusBeforeCancell);
    event OrderDisputed(address disputer, uint256 _orderId);
    event OrderResolved(uint256 _orderId, uint256 buyerRefund, uint256 sellerRefund);

    /**
     * @dev Throws if called by an account other than the buyer of `orders[_orderId]`
     */
    modifier onlyBuyer(uint256 _orderId) {
        require(orders[_orderId].buyer == msg.sender, 'Only Buyer Allowed');
        _;
    }
    /**
     * @dev Throws if called by an account other than the seller of `orders[_orderId]`
     */
    modifier onlySeller(uint256 _orderId) {
        require(orders[_orderId].seller == msg.sender, 'Only Seller Allowed');
        _;
    }

    /**
     * @dev Throws if called by an account other than the buyer or seller of `orders[_orderId]`
     */
    modifier onlyBuyerOrSeller(uint256 _orderId) {
        require(orders[_orderId].seller == msg.sender || orders[_orderId].buyer == msg.sender , 'Only Buyer or Seller Allowed');
        _;
    }

    /**
     * @dev Initialize the contract settings, and owner to the deployer.
     */
    constructor(uint256 _minOrderAmount, uint256 _disputeFee, uint256 _numBlocksToExpire)  {
        require(_disputeFee < _minOrderAmount, 'Review settings');
        //admin = payable(msg.sender);
        disputeFee = _disputeFee;
        minOrderAmount = _minOrderAmount; 
        numBlocksToExpire = _numBlocksToExpire;
    }
    /**
     * @dev Creates a new order with status : `CREATED` and append it to the `orders` array.
     */
    function createOrder(uint256 _amount, uint256 _deposit) public {
        require(_amount >= minOrderAmount, 'Order Too Small');
        Order memory order = Order(OrderStatus.CREATED, payable(address(0)), payable(msg.sender),  _amount, _deposit, orderCount, 0);
        orders.push(order);
        emit OrderCreated(msg.sender, _amount, _deposit, orderCount);
        orderCount++;
        
    }

    /**
     * @dev Initiate the escrow order with `_orderId`, and send the funds.
     */
    function initiateOrder(uint256 _orderId) public payable {
        require(orders[_orderId].status == OrderStatus.CREATED, 'Order already initiated');
        require(orders[_orderId].buyer == address(0), 'Order already initiated');
        require(msg.value ==orders[_orderId].amount + orders[_orderId].deposit, 'wrong amount' );
        orders[_orderId].buyer = payable(msg.sender);
        orders[_orderId].status = OrderStatus.INITIATED;
        emit OrderInitiated(msg.sender, _orderId);
    }
    /**
     * @dev Change status order with `_orderId` to `SENT`. Only the seller of that order can call it.
     */
    function sendOrder(uint256 _orderId) public onlySeller(_orderId) {
        require(orders[_orderId].status == OrderStatus.INITIATED, "Can't send order now");
        orders[_orderId].status = OrderStatus.SENT;
        orders[_orderId].sendBlock = block.number;
        emit OrderSent(_orderId, block.number);
    }

    
    /**
     * @dev Change status order with `_orderId` to `RECEIVED`. Only the buyer of that order can call it.
     * Releases funds to buyer and seller.
     */
    function receiveOrder(uint256 _orderId) public onlyBuyer(_orderId) {
        require(orders[_orderId].status == OrderStatus.SENT, "Can't receive order now");
        orders[_orderId].status = OrderStatus.RECEIVED;
        orders[_orderId].buyer.transfer(orders[_orderId].deposit);
        orders[_orderId].seller.transfer(orders[_orderId].amount);
        emit OrderReceived(_orderId);
    }

    /**
     * @dev Change status order with `_orderId` to `EXPIRED`. Only the seller of that order can call it.
     * Can only be called if time after sending the order is bigger than `numBlocksToExpire` .
     * Release funds to seller, buyer loses deposit.
     */
    function expireOrder(uint256 _orderId) public onlySeller(_orderId) {
        require(orders[_orderId].status == OrderStatus.SENT, "Order not sent");
        require(orders[_orderId].sendBlock + numBlocksToExpire < block.number, 'Order not expired yet');
        uint256 transferAmount = orders[_orderId].deposit + orders[_orderId].amount;
        orders[_orderId].status = OrderStatus.EXPIRED;
        orders[_orderId].seller.transfer(transferAmount);
        emit OrderExpired(_orderId);
    }

    /**
     * @dev Change status order with `_orderId` to `CANCELLED`. Only the buyer of that order can call it.
     * Can only be called if order is in state `INITIATED`.
     * Makes order available again.
     */
    function cancelBuyOrder(uint256 _orderId) public onlyBuyer(_orderId) {
        require(orders[_orderId].status == OrderStatus.INITIATED, "Can't cancell order now");
        OrderStatus beforeCancell = OrderStatus.INITIATED;
        uint256 refund = orders[_orderId].amount + orders[_orderId].deposit;
        orders[_orderId].status = OrderStatus.CREATED;
        orders[_orderId].buyer = payable(address(0));
        payable(msg.sender).transfer(refund);
        emit OrderCancelled(msg.sender, _orderId, beforeCancell);
    }

    /**
    * @dev Change status order with `_orderId` to `CANCELLED`. Only the seller of that order can call it.
    * Can only be called if order is in state `INITIATED`, `CREATED` or `SENT`.
    * If the order is in state `INITIATED` or `SENT` funds are sent back to the buyer.
    */
    function cancelSellOrder(uint256 _orderId) public onlySeller(_orderId) {
        require(orders[_orderId].status == OrderStatus.CREATED || orders[_orderId].status == OrderStatus.INITIATED || orders[_orderId].status == OrderStatus.SENT, "Can't cancell order now");
        OrderStatus beforeCancell = orders[_orderId].status;
        if( orders[_orderId].status == OrderStatus.INITIATED || orders[_orderId].status == OrderStatus.SENT) {
            uint256 refund = orders[_orderId].amount + orders[_orderId].deposit;
            orders[_orderId].buyer.transfer(refund);
        }
        orders[_orderId].status = OrderStatus.CANCELLED;
        emit OrderCancelled(msg.sender, _orderId, beforeCancell);
    }

    /**
    * @dev Change status order with `_orderId` to `DISPUTED`. Only the seller or buyer of that order can call it.
    * Can only be called if order is in state `SENT`.
    */
    function disputeOrder(uint256 _orderId) public onlyBuyerOrSeller(_orderId) {
        require(orders[_orderId].status == OrderStatus.SENT, "Can't dispute order now");
        orders[_orderId].status = OrderStatus.DISPUTED;
        disputedOrdersId.push(_orderId);
        emit OrderDisputed(msg.sender, _orderId );
    }

    /**
    * @dev Change status order with `_orderId` to `RESOLVED`. Only the owner of the contract can call it.
    * Can only be called if order is in state `DISPUTED`.
    * Owner collect the fee `disputeFee` and release the rest of the funds to buyer and seller.
    */
    function resolveDispute(uint256 _orderId,uint256 refundToBuyer) public onlyOwner() {
        address payable admin = payable(owner());
        require(orders[_orderId].status == OrderStatus.DISPUTED, 'Cant resolve order');
        require(refundToBuyer + disputeFee < orders[_orderId].amount + orders[_orderId].deposit, 'High refund' );
        uint256 refundToSeller = orders[_orderId].amount + orders[_orderId].deposit - refundToBuyer - disputeFee;
        orders[_orderId].status = OrderStatus.RESOLVED;
        admin.transfer(disputeFee);
        orders[_orderId].buyer.transfer(refundToBuyer);
        orders[_orderId].seller.transfer(refundToSeller);
        emit OrderResolved(_orderId, refundToBuyer, refundToSeller);
    }


  

}