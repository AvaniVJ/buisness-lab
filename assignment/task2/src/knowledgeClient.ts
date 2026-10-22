import {config} from "./config.js";
export type Knowledge = {answer:string;status:"answered"|"insufficient_evidence";sources:{title:string;url:string;relevance:number;excerpt:string}[];needs_human:boolean};
export async function queryBrain(question:string):Promise<Knowledge>{
 const controller=new AbortController(); const timer=setTimeout(()=>controller.abort(),15000);
 try {
  const r=await fetch(`${config.brainUrl}/query`,{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({question,top_k:5}),signal:controller.signal});
  if(!r.ok) throw new Error(`Knowledge Brain HTTP ${r.status}`);
  return await r.json() as Knowledge;
 } finally {clearTimeout(timer);}
}
