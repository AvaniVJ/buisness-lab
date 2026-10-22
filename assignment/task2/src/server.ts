import express from "express";
import {config} from "./config.js";
import {db,saveEmail,reviewEmail} from "./db.js";
import {EmailSchema,ReviewSchema} from "./types.js";
import {draftEmail} from "./agent.js";
const app=express(); app.use(express.json({limit:"1mb"}));
app.get("/health",(_q,res)=>res.json({status:"ok",service:"inbox-agent"}));
app.post("/emails/draft",async(req,res)=>{
 const parsed=EmailSchema.safeParse(req.body);
 if(!parsed.success) return res.status(400).json({error:"Invalid email",details:parsed.error.flatten()});
 try {const draft=await draftEmail(parsed.data); const id=saveEmail(parsed.data,draft); return res.status(201).json({id,...draft,status:"drafted"});}
 catch(err){return res.status(502).json({error:"Draft generation failed",detail:err instanceof Error?err.message:"Unknown error"});}
});
app.get("/emails",(_q,res)=>{
 const items=db.prepare("SELECT * FROM emails ORDER BY id DESC LIMIT 100").all();
 res.json({items:items.map((x:any)=>({...x,sourceUrls:JSON.parse(x.source_urls)}))});
});
app.get("/emails/:id",(req,res)=>{
 const row=db.prepare("SELECT * FROM emails WHERE id=?").get(Number(req.params.id)) as any;
 if(!row) return res.status(404).json({error:"Email not found"});
 return res.json({...row,sourceUrls:JSON.parse(row.source_urls)});
});
app.post("/emails/:id/review",(req,res)=>{
 const id=Number(req.params.id), row=db.prepare("SELECT draft FROM emails WHERE id=?").get(id) as {draft:string}|undefined;
 if(!row) return res.status(404).json({error:"Email not found"});
 const p=ReviewSchema.safeParse(req.body);
 if(!p.success) return res.status(400).json({error:"Invalid review",details:p.error.flatten()});
 if(p.data.action==="edit"&&!p.data.finalReply?.trim()) return res.status(400).json({error:"finalReply required for edit"});
 const final=p.data.action==="approve"?(p.data.finalReply??row.draft):p.data.action==="edit"?p.data.finalReply!:null;
 try {const learning=reviewEmail(id,p.data.action,row.draft,final,p.data.reviewer,p.data.correctionReason);
 return res.json({status:"review_recorded",id,learning,note:"No email is sent automatically. Twenty unchanged approvals only mark a category eligible for a separately reviewed autonomy feature."});}
 catch{return res.status(500).json({error:"Could not record review"});}
});
app.get("/learning/status",(_q,res)=>{
 res.json({autoSendEnabled:config.autoSend,streaks:db.prepare("SELECT * FROM streaks ORDER BY category").all(),
 reviews:db.prepare("SELECT action,COUNT(*) count FROM reviews GROUP BY action").all(),
 policy:"This starter never auto-sends emails; keep high-risk categories human-reviewed."});
});
app.listen(config.port,()=>console.log(`Inbox Agent listening at http://127.0.0.1:${config.port}`));
