import "dotenv/config";
export const config = {
 port: Number(process.env.PORT || 3002),
 apiKey: process.env.ANTHROPIC_API_KEY || "",
 model: process.env.CLAUDE_MODEL || "claude-3-5-haiku-latest",
 brainUrl: process.env.KNOWLEDGE_BRAIN_URL || "http://127.0.0.1:8000",
 dbPath: process.env.DATABASE_PATH || "data/inbox.db",
 autoSend: (process.env.AUTO_SEND_ENABLED || "false").toLowerCase() === "true"
};
