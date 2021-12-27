// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
contract EscrowToken is ERC20 {
    constructor() public ERC20("Escrow Token", "ESCRW"){
        _mint(msg.sender, 1000000000000000000000000);
    }
}