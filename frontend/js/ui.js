export const el=(name,text)=>{const n=document.createElement(name);if(text!==undefined)n.textContent=text;return n};
export const time=s=>new Intl.DateTimeFormat("en-IN",{dateStyle:"medium",timeStyle:"medium",timeZone:"Asia/Kolkata"}).format(new Date(s))+" IST";
export const message=text=>document.querySelector("#message").textContent=text;
