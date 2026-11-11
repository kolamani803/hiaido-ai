/* HiAIDo.ai operational workspace enhancement layer */
(()=>{
 const kinds={
  incident:{label:"Incidents",desc:"Track operational disruptions, ownership, severity and remediation.",fields:[["service","Affected service"],["impact","Business impact"],["summary","Incident summary"],["runbook","Runbook / reference"]],priority:true},
  workflow:{label:"Automation workflows",desc:"Catalog repeatable operational workflows. Execution remains disabled until a worker runtime is deployed.",fields:[["trigger","Trigger"],["steps","Workflow steps"],["risk","Risk / safeguards"]]},
  knowledge:{label:"Knowledge articles",desc:"Store tenant-scoped runbooks, standards and operational notes.",fields:[["category","Category"],["content","Article content"],["source","Source reference"]]},
  dashboard:{label:"Saved dashboards",desc:"Save dashboard definitions and team views. Live widgets require connected providers.",fields:[["audience","Audience"],["widgets","Widget configuration"],["description","Description"]]},
  task:{label:"Tasks & investigations",desc:"Assign operational follow-ups and track work through completion.",fields:[["description","Description"],["due_date","Due date"],["related_incident","Related incident"]]},
  approval:{label:"Approval queue",desc:"Record approval requests. This registry does not execute infrastructure changes.",fields:[["requested_action","Requested action"],["target","Target environment/resource"],["justification","Justification"],["risk","Risk assessment"]]},
  slo:{label:"Service level objectives",desc:"Define reliability targets and ownership; telemetry integration is required for measured compliance.",fields:[["service","Service"],["target","Target (e.g. 99.9%)"],["window","Measurement window"],["owner","Service owner"]]}
 };
 const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
 const panel=(title,sub,body)=>'<div class="panel hiaido-panel"><div class="panel-head"><h2>'+title+'</h2><span>'+sub+'</span></div>'+body+'</div>';
 const field=(id,label,type="text")=>'<div class="field"><label>'+label+'</label><'+(type==="textarea"?'textarea':'input type="'+type+'"')+' id="ws-'+id+'" '+(type==="textarea"?'':'')+' placeholder="'+label+'"></'+(type==="textarea"?'textarea':'input')+'></div>';
 function section(kind){
  const cfg=kinds[kind],view=document.getElementById(({incident:"incidents",workflow:"automation",knowledge:"knowledge",dashboard:"dashboards",task:"activity",approval:"governance",slo:"observability"})[kind]);
  if(!view||view.querySelector('[data-workspace-kind="'+kind+'"]'))return;
  const root=document.createElement("div");root.className="enhanced-workspace";root.dataset.workspaceKind=kind;
  root.innerHTML=panel("Workspace registry", "PostgreSQL-backed · tenant scoped",
   '<div class="ws-toolbar"><div><strong>'+cfg.label+'</strong><p>'+cfg.desc+'</p></div><button class="btn primary" data-create="'+kind+'">＋ Create '+cfg.label.slice(0,-1)+'</button></div>'+
   '<div class="ws-filters"><input id="filter-'+kind+'" placeholder="Search '+cfg.label.toLowerCase()+'..." aria-label="Search '+cfg.label+'"><select id="status-'+kind+'"><option value="">All statuses</option><option>open</option><option>in_progress</option><option>blocked</option><option>pending_approval</option><option>completed</option><option>archived</option></select></div>'+
   '<div id="items-'+kind+'" class="workspace-items"><div class="empty"><b>Sign in to load workspace data</b>Records are stored in your Neon PostgreSQL database.</div></div>');
  const hero=view.querySelector(".hero");if(hero)hero.insertAdjacentElement("afterend",root);else view.prepend(root);
  root.querySelector('[data-create]').addEventListener("click",()=>createForm(kind));
  root.querySelector('#filter-'+kind).addEventListener("input",()=>render(kind,cache[kind]||[]));
  root.querySelector('#status-'+kind).addEventListener("change",()=>render(kind,cache[kind]||[]));
 }
 const cache={};
 async function load(kind){
  const target=document.getElementById("items-"+kind);if(!target)return;
  if(!window.currentUser){target.innerHTML='<div class="empty"><b>Sign in required</b>Sign in to create and view private workspace records.</div>';return}
  target.innerHTML='<div class="loading-line">Loading records from PostgreSQL…</div>';
  try{const d=await window.api('/api/v1/workspace/'+kind);cache[kind]=d.items||[];render(kind,cache[kind])}
  catch(e){target.innerHTML='<div class="empty"><b>Unable to load '+kinds[kind].label.toLowerCase()+'</b>'+esc(e.message)+'</div>'}
 }
 function render(kind,items){
  const target=document.getElementById("items-"+kind);if(!target)return;
  const q=(document.getElementById('filter-'+kind)?.value||'').toLowerCase(),status=document.getElementById('status-'+kind)?.value||'';
  const filtered=items.filter(x=>(!status||x.status===status)&&[x.title,x.owner,x.status,JSON.stringify(x.payload||{})].join(' ').toLowerCase().includes(q));
  if(!filtered.length){target.innerHTML='<div class="empty"><b>No '+kinds[kind].label.toLowerCase()+' yet</b>Create your first record. Data will be isolated to this workspace.</div>';return}
  target.innerHTML=filtered.map(x=>'<article class="workspace-card"><div class="ws-card-top"><div><span class="priority p-'+esc(x.priority)+'">'+esc(x.priority||'normal')+'</span><h3>'+esc(x.title)+'</h3><small>'+esc(x.owner||'Unassigned')+' · '+new Date(x.updated_at||x.created_at).toLocaleString()+'</small></div><span class="ws-status s-'+esc(x.status)+'">'+esc((x.status||'open').replaceAll('_',' '))+'</span></div><p>'+esc(Object.entries(x.payload||{}).filter(([k,v])=>v).map(([k,v])=>k.replaceAll('_',' ')+': '+v).join(' · ')||'No additional details')+'</p><div class="ws-card-actions">'+(x.status!=="completed"&&x.status!=="archived"?'<button class="btn" data-complete="'+esc(x.id)+'">Mark complete</button>':'')+'<button class="btn ghost" data-archive="'+esc(x.id)+'">Archive</button></div></article>').join('');
  target.querySelectorAll('[data-complete]').forEach(b=>b.addEventListener('click',()=>update(kind,b.dataset.complete,{status:'completed'})));
  target.querySelectorAll('[data-archive]').forEach(b=>b.addEventListener('click',()=>update(kind,b.dataset.archive,{status:'archived'})));
 }
 async function update(kind,id,patch){try{await window.api('/api/v1/workspace/'+kind+'/'+encodeURIComponent(id),{method:'PATCH',body:JSON.stringify(patch)});await load(kind)}catch(e){window.showModal('Update failed',e.message)}}
 function createForm(kind){
  if(!window.currentUser){window.openLogin();return}
  const cfg=kinds[kind],formId='hiaido-create-form';
  document.getElementById(formId)?.remove();
  const wrap=document.createElement('div');wrap.id=formId;wrap.className='modal-backdrop open';
  wrap.innerHTML='<div class="modal hiaido-form"><h2>Create '+cfg.label.slice(0,-1)+'</h2><p>Saved to your private HiAIDo workspace.</p><form id="hiaido-record-form"><div class="field"><label>Title</label><input id="ws-title" required minlength="2" maxlength="200" placeholder="Enter a clear title"></div><div class="field"><label>Owner (optional)</label><input id="ws-owner" maxlength="254" placeholder="team or email"></div><div class="split"><div class="field"><label>Priority</label><select id="ws-priority"><option>normal</option><option>low</option><option>high</option><option>critical</option></select></div><div class="field"><label>Status</label><select id="ws-status"><option>open</option><option>in_progress</option><option>blocked</option><option>pending_approval</option></select></div></div>'+cfg.fields.map(([id,label])=>field(id,label,id==="content"||id==="steps"||id==="summary"||id==="justification"||id==="description"?"textarea":"text")).join('')+'<p id="ws-error" class="form-error"></p><div class="modal-actions"><button type="button" class="btn" id="ws-cancel">Cancel</button><button type="submit" class="btn primary">Save record</button></div></form></div>';
  document.body.appendChild(wrap);wrap.querySelector('#ws-cancel').onclick=()=>wrap.remove();wrap.addEventListener('click',e=>{if(e.target===wrap)wrap.remove()});
  wrap.querySelector('form').onsubmit=async e=>{e.preventDefault();const payload={};cfg.fields.forEach(([id])=>{const v=document.getElementById('ws-'+id)?.value.trim();if(v)payload[id]=v});
   const body={title:document.getElementById('ws-title').value.trim(),owner:document.getElementById('ws-owner').value.trim()||null,priority:document.getElementById('ws-priority').value,status:document.getElementById('ws-status').value,payload};
   try{await window.api('/api/v1/workspace/'+kind,{method:'POST',body:JSON.stringify(body)});wrap.remove();await load(kind)}catch(err){wrap.querySelector('#ws-error').textContent=err.message}
  };
 }
 async function enhance(){
  Object.keys(kinds).forEach(section);
  const navMap={incidents:'incident',automation:'workflow',knowledge:'knowledge',dashboards:'dashboard',activity:'task',governance:'approval',observability:'slo'};
  const oldNavigate=window.navigate;
  window.navigate=function(id){oldNavigate(id);if(navMap[id])load(navMap[id]);if(id==='audit')loadAudit();if(id==='resources')loadResources();if(id==='admin')loadPlatform()};
  if(window.currentUser){Object.values(navMap).forEach(load);loadAudit();loadPlatform()}
  const oldLogin=window.login;
  window.login=async function(){await oldLogin();if(window.currentUser){Object.values(navMap).forEach(load);loadAudit();loadPlatform()}};
 }
 async function loadAudit(){const view=document.getElementById('audit');if(!view||view.querySelector('#hiaido-audit-table'))return;const root=document.createElement('div');root.id='hiaido-audit-table';root.className='panel';root.innerHTML='<div class="panel-head"><h2>Audit trail</h2><button class="btn" id="audit-refresh">Refresh</button></div><div id="audit-rows" class="workspace-items"></div>';view.appendChild(root);root.querySelector('#audit-refresh').onclick=()=>{root.querySelector('#audit-rows').innerHTML='Loading…';fetchAudit(root)};fetchAudit(root)}
 async function fetchAudit(root){if(!window.currentUser){root.querySelector('#audit-rows').innerHTML='Sign in to view audit events.';return}try{const d=await window.api('/api/v1/audit');root.querySelector('#audit-rows').innerHTML=(d.items||[]).map(x=>'<div class="audit-row"><b>'+esc(x.action)+'</b><span>'+esc(x.outcome)+'</span><small>'+esc(x.actor_id)+' · '+new Date(x.created_at).toLocaleString()+'</small></div>').join('')||'<div class="empty">No audit events yet.</div>'}catch(e){root.querySelector('#audit-rows').textContent=e.message}}
 async function loadResources(){const view=document.getElementById('resources');if(!view||view.querySelector('#hiaido-resource-panel'))return;const root=document.createElement('div');root.id='hiaido-resource-panel';root.className='panel';root.innerHTML='<div class="panel-head"><h2>Live infrastructure inventory</h2><button class="btn" id="resource-refresh">Refresh</button></div><div id="resource-data" class="workspace-items">Loading live API…</div>';view.appendChild(root);root.querySelector('#resource-refresh').onclick=()=>fetchResources(root);fetchResources(root)}
 async function fetchResources(root){if(!window.currentUser){root.querySelector('#resource-data').textContent='Sign in to load infrastructure inventory.';return}try{const d=await window.api('/api/v1/overview');root.querySelector('#resource-data').innerHTML=(d.resources||[]).map(x=>'<div class="audit-row"><b>'+esc(x.name)+'</b><span>'+esc(x.status)+'</span><small>'+esc(x.type)+' · '+esc(x.environment)+'</small></div>').join('')||'<div class="empty">No resources discovered. Connect Kubernetes or ONTAP.</div>'}catch(e){root.querySelector('#resource-data').textContent=e.message}}
 async function loadPlatform(){const admin=document.getElementById('admin');if(!admin||admin.querySelector('#platform-capabilities'))return;const root=document.createElement('div');root.id='platform-capabilities';root.className='panel';root.innerHTML='<div class="panel-head"><h2>Runtime capability status</h2><button class="btn" id="platform-refresh">Refresh</button></div><div id="platform-status" class="workspace-items">Loading…</div>';admin.appendChild(root);root.querySelector('#platform-refresh').onclick=fetchPlatform;fetchPlatform()}
 async function fetchPlatform(){const el=document.getElementById('platform-status');if(!el)return;try{const d=await window.api('/api/v1/platform');el.innerHTML='<div class="cap-grid">'+Object.entries(d).map(([k,v])=>'<div class="cap-item"><small>'+esc(k.replaceAll('_',' '))+'</small><b>'+esc(typeof v==='object'?JSON.stringify(v):v)+'</b></div>').join('')+'</div>'}catch(e){el.textContent=e.message}}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',enhance);else enhance();
 window.hiaidoWorkspace={load,createForm};
})();