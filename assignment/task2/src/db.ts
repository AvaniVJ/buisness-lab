import Database from "better-sqlite3";
import fs from "node:fs";
import path from "node:path";
import { config } from "./config.js";
fs.mkdirSync(path.dirname(config.dbPath), {recursive:true});
export const db = new Database(config.dbPath);
db.pragma("journal_mode = WAL");
db.exec(`
CREATE TABLE IF NOT EXISTS emails(
 id INTEGER PRIMARY KEY, from_address TEXT NOT NULL, subject TEXT NOT NULL, body TEXT NOT NULL,
 thread_context TEXT DEFAULT '', category TEXT, urgency TEXT, risk TEXT, draft TEXT,
 source_urls TEXT DEFAULT '[]', confidence REAL, needs_approval INTEGER DEFAULT 1,
 status TEXT DEFAULT 'drafted', created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS reviews(
 id INTEGER PRIMARY KEY, email_id INTEGER NOT NULL REFERENCES emails(id), action TEXT NOT NULL,
 generated_reply TEXT NOT NULL, final_reply TEXT, reviewer TEXT NOT NULL, correction_reason TEXT,
 unchanged INTEGER NOT NULL, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS streaks(
 category TEXT PRIMARY KEY, count INTEGER NOT NULL DEFAULT 0, eligible INTEGER NOT NULL DEFAULT 0);
`);
export function saveEmail(e:any,d:any):number {
 const r=db.prepare(`INSERT INTO emails(from_address,subject,body,thread_context,category,urgency,risk,draft,source_urls,confidence,needs_approval)
 VALUES(?,?,?,?,?,?,?,?,?,?,?)`).run(e.from,e.subject,e.body,e.threadContext,d.category,d.urgency,d.risk,d.reply,JSON.stringify(d.sourceUrls),d.confidence,d.needsHumanApproval?1:0);
 return Number(r.lastInsertRowid);
}
export function reviewEmail(id:number, action:string, generated:string, finalReply:string|null, reviewer:string, reason?:string) {
 const e=db.prepare("SELECT category FROM emails WHERE id=?").get(id) as {category:string}|undefined;
 if(!e) throw new Error("Email not found");
 const unchanged=action==="approve" && (finalReply ?? generated).trim()===generated.trim();
 const tx=db.transaction(()=>{
  db.prepare("INSERT INTO reviews(email_id,action,generated_reply,final_reply,reviewer,correction_reason,unchanged) VALUES(?,?,?,?,?,?,?)")
   .run(id,action,generated,finalReply,reviewer,reason??null,unchanged?1:0);
  db.prepare("UPDATE emails SET status=? WHERE id=?").run(action==="approve"?"approved":action==="edit"?"edited":action==="reject"?"rejected":"escalated",id);
  const old=db.prepare("SELECT count FROM streaks WHERE category=?").get(e.category) as {count:number}|undefined;
  const count=unchanged?(old?.count??0)+1:0, eligible=count>=20?1:0;
  db.prepare("INSERT INTO streaks(category,count,eligible) VALUES(?,?,?) ON CONFLICT(category) DO UPDATE SET count=excluded.count,eligible=excluded.eligible")
   .run(e.category,count,eligible);
  return {unchanged,count,eligible:!!eligible};
 });
 return tx();
}
