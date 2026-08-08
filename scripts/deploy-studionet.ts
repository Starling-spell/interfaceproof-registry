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
console.log(JSON.stringify({
  contractAddress,
  deploymentTransaction: transactionHash,
  contractExplorer: `https://explorer-studio.genlayer.com/address/${contractAddress}`,
  transactionExplorer: `https://explorer-studio.genlayer.com/tx/${transactionHash}`,
}, null, 2));
