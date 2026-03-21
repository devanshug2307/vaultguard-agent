// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title PrivacyVault
 * @notice A vault that stores computation proofs (hashes) without storing raw data.
 *         Agents can commit to computations onchain via hashes without revealing
 *         the underlying data, enabling privacy-preserving AI reasoning.
 */
contract PrivacyVault {
    struct Session {
        address agent;
        bytes32 inputHash;
        bytes32 reasoningHash;
        string action;
        uint256 timestamp;
    }

    /// @notice All committed sessions, indexed by sessionId (0-based)
    Session[] private sessions;

    /// @notice Mapping from agent address to their list of session IDs
    mapping(address => uint256[]) private agentSessions;

    /// @notice Emitted when a new reasoning proof is committed
    event ReasoningCommitted(
        uint256 indexed sessionId,
        address indexed agent,
        bytes32 inputHash,
        bytes32 reasoningHash,
        string action,
        uint256 timestamp
    );

    /**
     * @notice Commit a reasoning proof onchain.
     * @param inputHash   SHA-256 (or keccak) hash of the private input data
     * @param reasoningHash Hash of the private reasoning output
     * @param action      Public-safe action string derived from the reasoning
     * @return sessionId  The ID assigned to this session
     */
    function commitReasoning(
        bytes32 inputHash,
        bytes32 reasoningHash,
        string calldata action
    ) external returns (uint256 sessionId) {
        require(inputHash != bytes32(0), "Input hash cannot be zero");
        require(reasoningHash != bytes32(0), "Reasoning hash cannot be zero");
        require(bytes(action).length > 0, "Action cannot be empty");

        sessionId = sessions.length;

        sessions.push(Session({
            agent: msg.sender,
            inputHash: inputHash,
            reasoningHash: reasoningHash,
            action: action,
            timestamp: block.timestamp
        }));

        agentSessions[msg.sender].push(sessionId);

        emit ReasoningCommitted(
            sessionId,
            msg.sender,
            inputHash,
            reasoningHash,
            action,
            block.timestamp
        );
    }

    /**
     * @notice Verify a session by retrieving its stored proof data.
     * @param sessionId The session to look up
     * @return agent         The address that committed the session
     * @return inputHash     Hash of the private input
     * @return reasoningHash Hash of the private reasoning
     * @return action        The public action string
     * @return timestamp     Block timestamp of the commit
     */
    function verifySession(uint256 sessionId)
        external
        view
        returns (
            address agent,
            bytes32 inputHash,
            bytes32 reasoningHash,
            string memory action,
            uint256 timestamp
        )
    {
        require(sessionId < sessions.length, "Session does not exist");

        Session storage s = sessions[sessionId];
        return (s.agent, s.inputHash, s.reasoningHash, s.action, s.timestamp);
    }

    /**
     * @notice Get all session IDs belonging to a given agent.
     * @param agent The agent address to query
     * @return An array of session IDs
     */
    function getAgentSessions(address agent)
        external
        view
        returns (uint256[] memory)
    {
        return agentSessions[agent];
    }

    /**
     * @notice Get the total number of committed sessions.
     * @return The count of all sessions
     */
    function totalSessions() external view returns (uint256) {
        return sessions.length;
    }
}
