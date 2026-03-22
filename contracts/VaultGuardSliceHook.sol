// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "./ISliceProductPrice.sol";
import "./ISliceProductAction.sol";
import "./PrivacyVault.sol";

/**
 * @title VaultGuardSliceHook
 * @notice A Slice commerce hook that integrates VaultGuard's privacy-preserving
 *         reasoning proofs with Slice product purchases.
 *
 *         PRICING STRATEGY (Track 2 - "Slice Hooks" $700):
 *         - Dynamic pricing based on buyer's VaultGuard verification history
 *         - Verified agents (with committed reasoning proofs) get discounted pricing
 *         - Unverified buyers pay the base price
 *
 *         ONCHAIN ACTION (Track 2 - "Slice Hooks" $700):
 *         - On purchase, automatically commits a commerce proof to the PrivacyVault
 *         - Links Slice product purchases to verifiable onchain reasoning sessions
 *         - Enables privacy-preserving purchase analytics
 *
 *         COMMERCE INTEGRATION (Track 1 - "Future of Commerce" $750):
 *         - Products represent AI agent services (analysis, monitoring, etc.)
 *         - Pricing reflects trust level based on verifiable reasoning history
 *         - Bridges decentralized commerce with privacy-preserving AI
 *
 * @dev Implements both ISliceProductPrice and ISliceProductAction from
 *      the Slice hooks framework (https://github.com/slice-so/hooks).
 *      Designed for deployment on Base / Base Sepolia.
 */
contract VaultGuardSliceHook is ISliceProductPrice, ISliceProductAction {
    // ─── State ──────────────────────────────────────────────────────────

    /// @notice The PrivacyVault contract for reasoning proof verification
    PrivacyVault public immutable vault;

    /// @notice Contract owner (deployer)
    address public owner;

    /// @notice Base price in wei per product unit (default: 0.001 ETH)
    uint256 public basePrice;

    /// @notice Discount basis points for verified agents (e.g., 2000 = 20% off)
    uint256 public verifiedDiscountBps;

    /// @notice Minimum sessions required to qualify as "verified"
    uint256 public minSessionsForDiscount;

    /// @notice Track total purchases processed through this hook
    uint256 public totalPurchases;

    /// @notice Track purchases per buyer
    mapping(address => uint256) public buyerPurchaseCount;

    /// @notice Session IDs of commerce proofs committed by this hook
    uint256[] public commerceSessionIds;

    // ─── Events ─────────────────────────────────────────────────────────

    event PurchaseProcessed(
        uint256 indexed slicerId,
        uint256 indexed productId,
        address indexed buyer,
        uint256 quantity,
        uint256 pricePaid,
        bool verifiedBuyer,
        uint256 vaultSessionId
    );

    event PricingConfigured(
        uint256 basePrice,
        uint256 verifiedDiscountBps,
        uint256 minSessionsForDiscount
    );

    // ─── Errors ─────────────────────────────────────────────────────────

    error OnlyOwner();
    error InvalidDiscount();

    // ─── Constructor ────────────────────────────────────────────────────

    /**
     * @param _vault                 Address of the deployed PrivacyVault
     * @param _basePrice             Base price in wei per unit
     * @param _verifiedDiscountBps   Discount for verified agents (basis points, max 5000 = 50%)
     * @param _minSessions           Minimum vault sessions to qualify for discount
     */
    constructor(
        address _vault,
        uint256 _basePrice,
        uint256 _verifiedDiscountBps,
        uint256 _minSessions
    ) {
        if (_verifiedDiscountBps > 5000) revert InvalidDiscount();

        vault = PrivacyVault(_vault);
        owner = msg.sender;
        basePrice = _basePrice;
        verifiedDiscountBps = _verifiedDiscountBps;
        minSessionsForDiscount = _minSessions;

        emit PricingConfigured(_basePrice, _verifiedDiscountBps, _minSessions);
    }

    // ─── ISliceProductPrice ─────────────────────────────────────────────

    /**
     * @notice Dynamic pricing: verified agents (with enough vault sessions) get a discount.
     * @dev Returns ethPrice only; currencyPrice is 0 (ETH-only pricing).
     */
    function productPrice(
        uint256 /* slicerId */,
        uint256 /* productId */,
        address /* currency */,
        uint256 quantity,
        address buyer,
        bytes memory /* data */
    ) external view override returns (uint256 ethPrice, uint256 currencyPrice) {
        uint256 unitPrice = basePrice;

        // Check if buyer has enough verified sessions in the PrivacyVault
        if (_isVerifiedAgent(buyer)) {
            // Apply discount: price * (10000 - discountBps) / 10000
            unitPrice = (basePrice * (10000 - verifiedDiscountBps)) / 10000;
        }

        ethPrice = unitPrice * quantity;
        currencyPrice = 0;
    }

    // ─── ISliceProductAction ────────────────────────────────────────────

    /**
     * @notice Gate: all purchases are allowed (no restriction).
     *         Override this in a subclass for allowlist/NFT-gated behavior.
     */
    function isPurchaseAllowed(
        uint256 /* slicerId */,
        uint256 /* productId */,
        address /* buyer */,
        uint256 /* quantity */,
        bytes memory /* slicerCustomData */,
        bytes memory /* buyerCustomData */
    ) external pure override returns (bool) {
        return true;
    }

    /**
     * @notice Post-purchase action: commit a commerce proof to the PrivacyVault.
     *         This creates a verifiable onchain record linking the Slice purchase
     *         to a reasoning session, enabling privacy-preserving purchase analytics.
     */
    function onProductPurchase(
        uint256 slicerId,
        uint256 productId,
        address buyer,
        uint256 quantity,
        bytes memory /* slicerCustomData */,
        bytes memory /* buyerCustomData */
    ) external payable override {
        // Build the commerce proof hashes
        bytes32 inputHash = keccak256(
            abi.encodePacked(slicerId, productId, buyer, quantity, block.timestamp)
        );
        bytes32 reasoningHash = keccak256(
            abi.encodePacked(
                "commerce_proof",
                slicerId,
                productId,
                buyer,
                quantity,
                _isVerifiedAgent(buyer)
            )
        );

        // Build action string
        string memory action = string(
            abi.encodePacked(
                "slice_purchase:slicer=",
                _uint2str(slicerId),
                ",product=",
                _uint2str(productId),
                ",qty=",
                _uint2str(quantity)
            )
        );

        // Commit commerce proof to PrivacyVault
        uint256 sessionId = vault.commitReasoning(inputHash, reasoningHash, action);

        // Track
        totalPurchases++;
        buyerPurchaseCount[buyer]++;
        commerceSessionIds.push(sessionId);

        emit PurchaseProcessed(
            slicerId,
            productId,
            buyer,
            quantity,
            basePrice * quantity,
            _isVerifiedAgent(buyer),
            sessionId
        );
    }

    // ─── Admin ──────────────────────────────────────────────────────────

    /**
     * @notice Update pricing configuration.
     */
    function configurePricing(
        uint256 _basePrice,
        uint256 _verifiedDiscountBps,
        uint256 _minSessions
    ) external {
        if (msg.sender != owner) revert OnlyOwner();
        if (_verifiedDiscountBps > 5000) revert InvalidDiscount();

        basePrice = _basePrice;
        verifiedDiscountBps = _verifiedDiscountBps;
        minSessionsForDiscount = _minSessions;

        emit PricingConfigured(_basePrice, _verifiedDiscountBps, _minSessions);
    }

    // ─── View Helpers ───────────────────────────────────────────────────

    /**
     * @notice Check if an address qualifies as a verified agent.
     */
    function isVerifiedAgent(address agent) external view returns (bool) {
        return _isVerifiedAgent(agent);
    }

    /**
     * @notice Get the number of commerce proofs committed through this hook.
     */
    function totalCommerceProofs() external view returns (uint256) {
        return commerceSessionIds.length;
    }

    /**
     * @notice Get a commerce proof session ID by index.
     */
    function getCommerceSessionId(uint256 index) external view returns (uint256) {
        return commerceSessionIds[index];
    }

    // ─── Internal ───────────────────────────────────────────────────────

    function _isVerifiedAgent(address agent) internal view returns (bool) {
        uint256[] memory sessions = vault.getAgentSessions(agent);
        return sessions.length >= minSessionsForDiscount;
    }

    function _uint2str(uint256 value) internal pure returns (string memory) {
        if (value == 0) return "0";
        uint256 temp = value;
        uint256 digits;
        while (temp != 0) {
            digits++;
            temp /= 10;
        }
        bytes memory buffer = new bytes(digits);
        while (value != 0) {
            digits -= 1;
            buffer[digits] = bytes1(uint8(48 + uint256(value % 10)));
            value /= 10;
        }
        return string(buffer);
    }
}
