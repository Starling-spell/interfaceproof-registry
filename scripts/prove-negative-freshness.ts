import {createAccount,createClient} from "genlayer-js";
import {studionet} from "genlayer-js/chains";
import {TransactionStatus} from "genlayer-js/types";
const address=process.env.CONTRACT_ADDRESS as `0x${string}`;
const originalRevision=process.env.ORIGINAL_REVISION??"swagger-pets-available-v3";
if(!address)throw new Error("Set CONTRACT_ADDRESS");
const account=createAccount(),client=createClient({chain:studionet,account});
async function write(functionName:string,args:any[]){const hash=await client.writeContract({address,functionName,args,account,value:0n});console.log(`${functionName}=${hash}`);const r=await client.waitForTransactionReceipt({hash:hash as never,status:TransactionStatus.FINALIZED,interval:5000,retries:180})as any;const fatal=(r.consensus_data?.leader_receipt??[]).filter((x:any)=>x.execution_result!=="SUCCESS"&&x.genvm_result?.error_code!=="CONSENSUS_VALIDATOR_QUORUM_REACHED");if(r.result_name!=="MAJORITY_AGREE"||fatal.length)throw new Error(`${functionName} failed ${JSON.stringify({hash,result:r.result_name,fatal})}`);return{hash,explorer:`https://explorer-studio.genlayer.com/tx/${hash}`}}
const suffix=String(Date.now()),revision=`freshness-clock-${suffix}`,attestation=`freshness-clock-proof-${suffix}`;
const registered=await write("register_revision",[revision,"Freshness clock proof","https://petstore3.swagger.io/api/v3/openapi.json","https://petstore3.swagger.io/api/v3","/pet/findByStatus","get",'{"status":"available"}']);
const attested=await write("attest_interface",[revision,attestation]);
const[originalLatest,freshness,fresh0,fresh1]=await Promise.all([
 client.readContract({address,functionName:"get_latest",args:[originalRevision]}),
 client.readContract({address,functionName:"get_freshness",args:[originalRevision]}),
 client.readContract({address,functionName:"is_fresh_and_compatible",args:[originalRevision,0]}),
 client.readContract({address,functionName:"is_fresh_and_compatible",args:[originalRevision,1]}),
]);
console.log(JSON.stringify({address,originalRevision,registered,attested,originalLatest,freshness,fresh0,fresh1},null,2));
