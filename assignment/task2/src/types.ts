import { z } from "zod";
export const EmailSchema = z.object({
 from: z.string().email(), subject: z.string().min(1).max(500),
 body: z.string().min(1).max(20000), threadContext: z.string().max(10000).optional().default("")
});
export type IncomingEmail = z.infer<typeof EmailSchema>;
export const DraftSchema = z.object({
 category: z.enum(["how_to","troubleshooting","project_request","refund_cancellation","complaint","quote_request","follow_up","other"]),
 summary: z.string(), urgency: z.enum(["low","normal","high","critical"]),
 risk: z.enum(["low","medium","high"]), reply: z.string(), sourceUrls: z.array(z.string()),
 needsHumanApproval: z.boolean(), nextAction: z.string(), confidence: z.number().min(0).max(1)
});
export const ReviewSchema = z.object({
 action: z.enum(["approve","edit","reject","escalate"]), finalReply: z.string().optional(),
 reviewer: z.string().min(1).max(200), correctionReason: z.string().max(1000).optional()
});
export type EmailDraft = z.infer<typeof DraftSchema>;
