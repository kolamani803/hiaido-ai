/* HiAIDo.ai guided demo: clearly simulated, browser-local and safe */
(()=>{
 const $=s=>document.querySelector(s), esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const modules=[
  ['☸','Infrastructure','Unified Kubernetes, OpenShift, cloud and storage inventory','resources'],
  ['⌘','Incident Command','Triage, severity, ownership, response timeline and postmortems','incidents'],
  ['✧','AI Operations Copilot','Troubleshooting, runbook drafting and guided investigation','copilot'],
  ['ϟ','Automation Studio','Workflow templates, approvals, schedules and run history','automation'],
  ['◉','Observability','Service health, SLOs, alert correlation and event context','observability'],
  ['▥','Dashboard Builder','Role-based dashboards, saved views and operational KPIs','dashboards'],
  ['⌁','MCP Marketplace','Connect tools using scoped permissions and governed access','marketplace'],
  ['▧','Knowledge Hub','Runbooks, troubleshooting articles and team knowledge','knowledge'],
  ['◒','FinOps','Cost allocation, rightsizing and optimization opportunities','cost'],
  ['♙','Governance','Workspace roles, policy controls and approval records','governance'],
  ['⌨','Secure Terminal','Brokered sessions, command guardrails and session evidence','terminal'],
  ['≋','Audit & Compliance','Trace user, model, tool and automation activity','audit']
 ];
 const seed=[
  {id:'INC-2048',kind:'Incident',title:'Checkout API elevated latency',service:'commerce-api',priority:'critical',status:'investigating',owner:'SRE Platform',age:'8 min ago'},
  {id:'INC-2047',kind:'Incident',title:'Worker nodes nearing memory pressure',service:'openshift-prod',priority:'high',status:'mitigating',owner:'Cloud Operations',age:'26 min ago'},
  {id:'CHG-881',kind:'Change',title:'Storage firmware maintenance',service:'ontap-prod',priority:'normal',status:'awaiting approval',owner:'Storage Team',age:'1 hr ago'},
  {id:'AUT-109',kind:'Automation',title:'Restart unhealthy deployment replicas',service:'Kubernetes',priority:'normal',status:'draft',owner:'Platform Engineering',age:'Today'},
  {id:'SLO-021',kind:'SLO',title:'Customer API availability',service:'customer-api',priority:'high',status:'watch',owner:'Application SRE',age:'Today'}
 ];
 let records=seed.slice(),filter='';
 function mount(){
  const nav=$('.nav');if(!nav||$('#demo-nav'))return;
  const label=document.createElement('div');label.className='nav-label';label.textContent='GET STARTED';
  const b=document.createElement('button');b.id='demo-nav';b.innerHTML='<span class="ico">✦</span><span>Interactive Demo</span>';b.onclick=()=>show();
  nav.insertBefore(b,nav.firstChild);nav.insertBefore(label,b);
  const section=document.createElement('section');section.className='view';section.id='demo-workspace';
  section.innerHTML='<div class="hero"><div><div class="eyebrow">EXPLORE HIAIDO.AI</div><h1>One workspace. Every operation.</h1><p>Explore the product with a guided, interactive sample organization. No account or infrastructure connection required.</p></div><div class="actions"><button class="btn" id="demo-reset">↻ Reset demo</button><button class="btn primary" id="demo-add">＋ Create sample incident</button></div></div>'+
  '<div class="demo-banner"><div><strong>Interactive demonstration environment</strong><p>All records and metrics on this page are illustrative sample data stored only in this browser. Nothing is sent to your infrastructure.</p></div><span class="demo-tag">SIMULATED DATA</span></div>'+
  '<div class="demo-intro"><div class="demo-welcome"><div class="eyebrow">WELCOME TO YOUR OPERATIONS COMMAND CENTER</div><h2>See the whole estate.<br>Act with confidence.</h2><p>Bring infrastructure signals, incidents, automation, AI assistance and governance into a single operational experience designed for platform, SRE, cloud and IT teams.</p><div class="actions"><button class="btn primary" id="demo-tour">Explore capabilities ↓</button><button class="btn" id="demo-open-incidents">Open incident queue →</button></div></div><div class="demo-score"><div><span>Managed services</span><b>24</b><span>Across 4 environments</span></div><div><span>Service health</span><b>98.7%</b><span>Illustrative availability</span></div><div><span>Open incidents</span><b id="demo-inc-count">2</b><span>Sample incident records</span></div><div><span>Automation runs</span><b>186</b><span>Illustrative · last 30 days</span></div></div></div>'+
  '<div class="demo-section-title"><div><h2>Explore product capabilities</h2><p>Open any module to explore its current interface and integration path.</p></div></div><div class="demo-module-grid" id="demo-modules"></div>'+
  '<div class="demo-section-title"><div><h2>Operations at a glance</h2><p>Sample work queue · interact by searching or creating a sample incident.</p></div><div class="demo-actions"><input id="demo-search" placeholder="Search sample records"><select id="demo-kind"><option value="">All record types</option><option>Incident</option><option>Change</option><option>Automation</option><option>SLO</option></select></div></div>'+
  '<div class="panel"><div class="table-wrap"><table class="demo-table"><thead><tr><th>REFERENCE</th><th>WORK ITEM</th><th>PRIORITY</th><th>STATUS</th><th>OWNER</th><th>UPDATED</th></tr></thead><tbody id="demo-records"></tbody></table></div></div>'+
  '<div class="demo-section-title"><div><h2>Recent operational timeline</h2><p>Example cross-platform activity feed.</p></div></div><div class="panel demo-timeline"><div class="demo-event"><time>09:42 UTC</time><div><b>Alert correlated to INC-2048</b><p>API latency alert grouped with recent deployment event. Sample event.</p></div></div><div class="demo-event"><time>09:31 UTC</time><div><b>Change approval requested</b><p>Storage maintenance requires owner and change-window approval. Sample event.</p></div></div><div class="demo-event"><time>09:18 UTC</time><div><b>Automation policy evaluated</b><p>Restart workflow held for approval because target is production. Sample event.</p></div></div><div class="demo-event"><time>08:55 UTC</time><div><b>Knowledge article suggested</b><p>Runbook recommendation attached to an OpenShift memory-pressure investigation. Sample event.</p></div></div></div>'+
  '<div class="info">Production capabilities require the protected HiAIDo API, configured identity, connected providers and approved runtime services. This demo does not imply those systems are connected.</div>';
  $('.main').appendChild(section);
  $('#demo-modules').innerHTML=modules.map(([ico,name,desc,id])=>'<article class="demo-module"><div class="demo-icon">'+ico+'</div><h3>'+name+'</h3><p>'+desc+'</p><button class="btn" data-open="'+id+'">Explore module →</button></article>').join('');
  $('#demo-modules').querySelectorAll('[data-open]').forEach(x=>x.onclick=()=>{const id=x.dataset.open;const n=document.querySelector('[data-view="'+id+'"]');if(n)window.navigate(id);else show()});
  $('#demo-add').onclick=addRecord;$('#demo-reset').onclick=()=>{records=seed.slice();renderRecords()};
  $('#demo-tour').onclick=()=>$('#demo-modules').scrollIntoView({behavior:'smooth'});
  $('#demo-open-incidents').onclick=()=>window.navigate('incidents');
  $('#demo-search').oninput=renderRecords;$('#demo-kind').onchange=renderRecords;renderRecords();
 }
 function renderRecords(){
  const q=($('#demo-search')?.value||'').toLowerCase(),k=$('#demo-kind')?.value||'';
  const rows=records.filter(r=>(!k||r.kind===k)&&Object.values(r).join(' ').toLowerCase().includes(q));
  $('#demo-records').innerHTML=rows.map(r=>'<tr><td><b>'+esc(r.id)+'</b></td><td>'+esc(r.title)+'<br><span style="color:#8e9db8">'+esc(r.service)+'</span></td><td><span class="demo-chip '+esc(r.priority)+'">'+esc(r.priority)+'</span></td><td><span class="demo-chip">'+esc(r.status)+'</span></td><td>'+esc(r.owner)+'</td><td>'+esc(r.age)+'</td></tr>').join('')||'<tr><td colspan="6"><div class="demo-empty">No sample records match your search.</div></td></tr>';
  $('#demo-inc-count').textContent=records.filter(x=>x.kind==='Incident').length;
 }
 function addRecord(){
  const title=prompt('Sample incident title (saved in this browser only):');if(!title||!title.trim())return;
  records.unshift({id:'INC-'+(2050+records.length),kind:'Incident',title:title.trim(),service:'sample-service',priority:'normal',status:'new',owner:'Demo Operator',age:'Just now'});renderRecords();
 }
 function show(){if(typeof window.navigate==='function')window.navigate('demo-workspace');else{$('.view.active')?.classList.remove('active');$('#demo-workspace').classList.add('active')};document.querySelectorAll('.nav button').forEach(b=>b.classList.toggle('active',b.id==='demo-nav'));$('#crumb').textContent='Interactive Demo'}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount);else mount();
})();
