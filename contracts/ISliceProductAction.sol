// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title ISliceProductAction (Slice Hook Interface)
 * @notice Interface for Slice commerce protocol action hooks.
 *         Implements the IProductAction interface from slice-so/hooks.
 *         See: https://github.com/slice-so/hooks/tree/main/src/interfaces
 */
interface ISliceProductAction {
    /**
     * @notice Check if a purchase is allowed (pre-payment gate).
     * @param slicerId          The slicer (store) ID
     * @param productId         The product ID within the slicer
     * @param buyer             The buyer's address
     * @param quantity          Number of units being purchased
     * @param slicerCustomData  Data set by the slicer owner
     * @param buyerCustomData   Data provided by the buyer
     * @return Whether the purchase should proceed
     */
    function isPurchaseAllowed(
        uint256 slicerId,
        uint256 productId,
        address buyer,
        uint256 quantity,
        bytes memory slicerCustomData,
        bytes memory buyerCustomData
    ) external view returns (bool);

    /**
     * @notice Execute post-purchase logic (after payment).
     * @param slicerId          The slicer (store) ID
     * @param productId         The product ID within the slicer
     * @param buyer             The buyer's address
     * @param quantity          Number of units being purchased
     * @param slicerCustomData  Data set by the slicer owner
     * @param buyerCustomData   Data provided by the buyer
     */
    function onProductPurchase(
        uint256 slicerId,
        uint256 productId,
        address buyer,
        uint256 quantity,
        bytes memory slicerCustomData,
        bytes memory buyerCustomData
    ) external payable;
}
