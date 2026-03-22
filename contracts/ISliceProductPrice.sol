// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title ISliceProductPrice (Slice Hook Interface)
 * @notice Interface for Slice commerce protocol pricing hooks.
 *         Implements the IProductPrice interface from slice-so/hooks.
 *         See: https://github.com/slice-so/hooks/tree/main/src/interfaces
 */
interface ISliceProductPrice {
    /**
     * @notice Calculate dynamic price for a Slice product purchase.
     * @param slicerId   The slicer (store) ID
     * @param productId  The product ID within the slicer
     * @param currency   The ERC20 currency address (address(0) for ETH)
     * @param quantity   Number of units being purchased
     * @param buyer      The buyer's address
     * @param data       Arbitrary calldata for custom logic
     * @return ethPrice      Price in ETH (wei)
     * @return currencyPrice Price in the specified ERC20 currency
     */
    function productPrice(
        uint256 slicerId,
        uint256 productId,
        address currency,
        uint256 quantity,
        address buyer,
        bytes memory data
    ) external view returns (uint256 ethPrice, uint256 currencyPrice);
}
