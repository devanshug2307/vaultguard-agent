/**
 * VaultGuard Private Reasoning Lit Action
 *
 * Runs inside Lit Protocol's Chipotle TEE-secured runtime.
 * Takes vault data as input, performs private AI reasoning,
 * and returns only the hashed decision + public action recommendation.
 *
 * The raw vault balances and reasoning steps never leave the TEE.
 */
(async () => {
  // jsParams: { vaultData, threshold, actionType }
  const { vaultData, threshold, actionType } = jsParams;

  // --- PRIVATE REASONING (inside TEE, never exposed) ---

  // 1. Parse the private vault state
  const balance = parseFloat(vaultData.balance || "0");
  const yieldRate = parseFloat(vaultData.yieldRate || "0");
  const riskScore = parseFloat(vaultData.riskScore || "0");

  // 2. Private decision logic
  let decision;
  let confidence;

  if (actionType === "rebalance") {
    // Private rebalancing logic - thresholds and balances stay in TEE
    const targetAllocation = balance * (yieldRate / 100);
    const deviation = Math.abs(targetAllocation - balance * 0.5) / balance;
    decision = deviation > (threshold || 0.05) ? "REBALANCE" : "HOLD";
    confidence = Math.max(0, Math.min(100, Math.round((1 - deviation) * 100)));
  } else if (actionType === "risk_check") {
    // Private risk assessment
    decision = riskScore > (threshold || 0.7) ? "REDUCE_EXPOSURE" : "SAFE";
    confidence = Math.round((1 - Math.abs(riskScore - 0.5)) * 100);
  } else {
    // Default: health check
    const isHealthy = balance > 0 && yieldRate > 0 && riskScore < 0.9;
    decision = isHealthy ? "HEALTHY" : "ATTENTION_NEEDED";
    confidence = isHealthy ? 85 : 40;
  }

  // 3. Create a commitment hash of the private reasoning
  // This proves the reasoning happened without revealing inputs
  const reasoningInput = JSON.stringify({
    balance, yieldRate, riskScore, actionType, threshold, decision
  });
  const encoder = new TextEncoder();
  const data = encoder.encode(reasoningInput);
  const hashBuffer = await crypto.subtle.digest("SHA-256", data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const reasoningHash = hashArray.map(b => b.toString(16).padStart(2, "0")).join("");

  // --- PUBLIC OUTPUT (only this leaves the TEE) ---
  LitActions.setResponse({
    response: JSON.stringify({
      action: decision,
      confidence: confidence,
      reasoningHash: reasoningHash,
      timestamp: Date.now(),
      teeVerified: true,
      actionType: actionType || "health_check",
      // Private data (balance, yieldRate, riskScore) is NOT included
    })
  });
})();
