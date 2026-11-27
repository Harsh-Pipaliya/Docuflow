let csrf;
export async function api(path,method="GET",body){
 const r=await fetch(path,{method,headers:{"X-CSRF-Token":csrf||"",...(body?{"Content-Type":"application/json"}:{})},body:body?JSON.stringify(body):undefined});
 if(!r.ok){const data=await r.json();throw Error(data.error?.message||"Request failed")}
 if(r.status===204)return;const data=await r.json();if(data.csrf)csrf=data.csrf;return data;
}
export function upload(file,progress){
 return new Promise((resolve,reject)=>{const x=new XMLHttpRequest();x.open("POST","/api/documents");x.setRequestHeader("X-CSRF-Token",csrf);x.upload.onprogress=e=>{if(e.lengthComputable)progress.value=e.loaded/e.total};x.onload=()=>x.status===201?resolve(JSON.parse(x.responseText)):reject(Error(JSON.parse(x.responseText).error.message));x.onerror=()=>reject(Error("Connection failed"));const data=new FormData();data.append("file",file);x.send(data)});
}
