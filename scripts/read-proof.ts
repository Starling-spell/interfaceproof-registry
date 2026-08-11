import { createClient } from "genlayer-js";
import { studionet } from "genlayer-js/chains";

const address = process.env.CONTRACT_ADDRESS as `0x${string}` | undefined;
const revisionId = process.env.REVISION_ID ?? "swagger-pets-available-v3";
if (!address) throw new Error("Set CONTRACT_ADDRESS.");

const client = createClient({ chain: studionet });
const [latest, compatible] = await Promise.all([
  client.readContract({ address, functionName: "get_latest", args: [revisionId] }),
  client.readContract({ address, functionName: "is_continuously_compatible", args: [revisionId] }),
]);

console.log(JSON.stringify({ contractAddress: address, revisionId, compatible, latest }, null, 2));
