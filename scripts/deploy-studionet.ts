import fs from "node:fs";
import path from "node:path";
import { createAccount, createClient } from "genlayer-js";
import { studionet } from "genlayer-js/chains";
import { TransactionStatus } from "genlayer-js/types";

const account = createAccount();
const client = createClient({ chain: studionet, account });
const code = fs.readFileSync(path.resolve("contracts/InterfaceProofRegistry.py"), "utf8");

console.log(`Deploying from ephemeral StudioNet account ${account.address}`);
const transactionHash = await client.deployContract({ account, code, args: [] });
const receipt = (await client.waitForTransactionReceipt({
  hash: transactionHash as never,
  status: TransactionStatus.FINALIZED,
  interval: 5000,
  retries: 180,
})) as Record<string, unknown>;
const data = receipt.data as { contract_address?: string } | undefined;
const decoded = receipt.txDataDecoded as { contractAddress?: string } | undefined;
const contractAddress = data?.contract_address ?? decoded?.contractAddress;
if (!contractAddress) throw new Error("Finalized deployment has no contract address.");
const address = contractAddress as `0x${string}`;
console.log(`contractAddress=${address}`);
console.log(`deploymentTransaction=${transactionHash}`);

async function write(functionName: string, args: any[]) {
  const hash = await client.writeContract({ address, functionName, args, account, value: 0n });
  console.log(`${functionName}Transaction=${hash}`);
  const result = await client.waitForTransactionReceipt({
    hash: hash as never, status: TransactionStatus.FINALIZED, interval: 5000, retries: 180,
  }) as Record<string, unknown>;
  const consensus = result.consensus_data as { votes?: Record<string, string> } | undefined;
  const leaderReceipts = (consensus as { leader_receipt?: Array<{ execution_result?: string; genvm_result?: { error_code?: string } }> } | undefined)?.leader_receipt ?? [];
  const executions = leaderReceipts.map((item) => item.execution_result ?? "UNKNOWN");
  const votes = Object.values(consensus?.votes ?? {});
  const summary = { hash, status: result.status_name, consensus: result.result_name,
    agree: votes.filter((vote) => vote === "agree").length,
    disagree: votes.filter((vote) => vote === "disagree").length, executions };
  console.log(`${functionName}Result=${JSON.stringify(summary)}`);
  const fatal = leaderReceipts.filter((item) =>
    item.execution_result !== "SUCCESS" &&
    item.genvm_result?.error_code !== "CONSENSUS_VALIDATOR_QUORUM_REACHED"
  );
  if (result.result_name !== "MAJORITY_AGREE" || fatal.length > 0) {
    throw new Error(`${functionName} finalized with execution failure`);
  }
  return summary;
}

const revisionId = "swagger-pets-available-v3";
const registered = await write("register_revision", [
  revisionId, "Swagger Petstore available-pets API", "https://petstore3.swagger.io/api/v3/openapi.json",
  "https://petstore3.swagger.io/api/v3", "/pet/findByStatus", "get", '{"status":"available"}',
]);
const attestationId = `swagger-pets-available-v3-${Date.now()}`;
const attested = await write("attest_interface", [revisionId, attestationId]);
const attestation = await client.readContract({ address, functionName: "get_attestation", args: [attestationId] });
console.log(JSON.stringify({
  contractAddress,
  deploymentTransaction: transactionHash,
  contractExplorer: `https://explorer-studio.genlayer.com/address/${contractAddress}`,
  transactionExplorer: `https://explorer-studio.genlayer.com/tx/${transactionHash}`,
  revisionId,
  registerTransaction: registered.hash,
  registerResult: registered,
  attestationId,
  attestationTransaction: attested.hash,
  attestationResult: attested,
  attestation,
}, null, 2));
