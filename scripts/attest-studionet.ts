import { createAccount, createClient } from "genlayer-js";
import { studionet } from "genlayer-js/chains";
import { TransactionStatus } from "genlayer-js/types";

const address = process.env.CONTRACT_ADDRESS as `0x${string}` | undefined;
if (!address) throw new Error("Set CONTRACT_ADDRESS.");
const account = createAccount();
const client = createClient({ chain: studionet, account });
const revisionId = process.env.REVISION_ID ?? "swagger-pets-available-v3";
const attestationId = `${revisionId}-${Date.now()}`;

const hash = await client.writeContract({
  address, functionName: "attest_interface", args: [revisionId, attestationId], account, value: 0n,
});
console.log(`attestationTransaction=${hash}`);
try {
  const receipt = await client.waitForTransactionReceipt({
    hash: hash as never, status: TransactionStatus.FINALIZED, interval: 5000, retries: 180,
  }) as Record<string, unknown>;
  const data = receipt.consensus_data as { votes?: Record<string, string> } | undefined;
  const votes = Object.values(data?.votes ?? {});
  const record = await client.readContract({ address, functionName: "get_attestation", args: [attestationId] });
  console.log(JSON.stringify({
    contractAddress: address, attestationId, attestationTransaction: hash,
    transactionExplorer: `https://explorer-studio.genlayer.com/tx/${hash}`,
    status: receipt.status_name, consensus: receipt.result_name,
    agree: votes.filter((vote) => vote === "agree").length,
    disagree: votes.filter((vote) => vote === "disagree").length,
    attestation: record,
  }, null, 2));
} catch (error) {
  const message = error instanceof Error ? error.message : "attestation verification failed";
  throw new Error(`Attestation ${hash} was submitted but could not be verified: ${message.split("\n")[0]}`);
}
