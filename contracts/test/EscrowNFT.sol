// contracts/GameItem.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

contract EscrowNFT is ERC721 {
   
    uint256 public tokenCounter;
    constructor() public ERC721("Escrow NFT", "ESCR721") {
        tokenCounter = 0;
    }

    function createNFT() public returns (uint256) {
        uint256 newTokenId = tokenCounter;
        _safeMint(msg.sender, newTokenId);
        tokenCounter++;
        return newTokenId;

    }

    
}