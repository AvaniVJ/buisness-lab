import {describe,it,expect} from "vitest";
import {EmailSchema,DraftSchema} from "../src/types.js";
describe("schemas",()=>{
 it("accepts valid email",()=>expect(EmailSchema.safeParse({from:"a@example.com",subject:"Help",body:"Question"}).success).toBe(true));
 it("rejects invalid sender",()=>expect(EmailSchema.safeParse({from:"bad",subject:"Help",body:"Question"}).success).toBe(false));
 it("rejects confidence above one",()=>expect(DraftSchema.safeParse({category:"how_to",summary:"x",urgency:"normal",risk:"low",reply:"x",sourceUrls:[],needsHumanApproval:false,nextAction:"x",confidence:1.1}).success).toBe(false));
});
