/* HiAIDo.ai enterprise UX: command palette, quick actions and responsive navigation */
(()=>{
 const $=s=>document.querySelector(s);
 const navItems=[...document.querySelectorAll('.nav button[data-view]')];
 const groups=[...document.querySelectorAll('.nav .nav-label')];
 const icons={overview:'▦',resources:'▤',environments:'◈',incidents:'⌘',copilot:'✧',observability:'◉',automation:'ϟ',dashboards:'▥',knowledge:'▧',marketplace:'⌁',terminal:'⌨',cost:'◒',activity:'◷',governance:'⬡',audit:'≋',admin:'⚙'};
 const descriptions={overview:'Operational health and workspace overview',resources:'Clusters, workloads, cloud and storage inventory',environments:'Development, staging and production landscapes',incidents:'Incident response, SRE and remediation',copilot:'Ask questions and investigate operations with AI',observability:'Metrics, alerts, events and service objectives',automation:'Build governed workflows and runbooks',dashboards:'Create and manage operational dashboards',knowledge:'Runbooks, standards and troubleshooting articles',marketplace:'Connect MCP servers and enterprise providers',terminal:'Secure, policy-controlled access sessions',cost:'Cloud spend, allocation and optimization',activity:'Tasks, investigations and operational activity',governance:'Users, permissions, policies and approvals',audit:'Evidence and audit history',admin:'Accounts and platform configuration'};
 const overlay=document.createElement('div');overlay.className='command-overlay';overlay.id='hiaido-command-overlay';
 overlay.innerHTML='<div class="command-box" role="dialog" aria-modal="true" aria-label="Command menu"><div class="command-search"><span>⌕</span><input id="hiaido-command-input" placeholder="Search pages, actions and capabilities..." autocomplete="off"><span class="enterprise-shortcut">ESC</span></div><div class="command-list" id="hiaido-command-list"></div><div class="command-footer"><span>↑ ↓ Navigate · Enter Open · Esc Close</span><span><kbd>Ctrl</kbd> + <kbd>K</kbd> to open</span></div></div>';
 document.body.appendChild(overlay);
 const toast=document.createElement('div');toast.className='enterprise-toast';toast.setAttribute('role','status');document.body.appendChild(toast);
 let selected=0,commands=[];
 function notify(message){toast.textContent=message;toast.classList.add('show');clearTimeout(notify.timer);notify.timer=setTimeout(()=>toast.classList.remove('show'),2600)}
 function buildCommands(){
  commands=navItems.map(b=>({type:'Navigate',title:b.innerText.trim(),description:descriptions[b.dataset.view]||'Open workspace',icon:icons[b.dataset.view]||'◇',run:()=>window.navigate(b.dataset.view)}));
  commands.push(
   {type:'Quick action',title:'Create an incident',description:'Open the incident creation form',icon:'＋',run:()=>openCreate('incidents','incident')},
   {type:'Quick action',title:'Create an automation workflow',description:'Draft a governed workflow record',icon:'ϟ',run:()=>openCreate('automation','workflow')},
   {type:'Quick action',title:'Create a task',description:'Add an operational follow-up',icon:'✓',run:()=>openCreate('activity','task')},
   {type:'Quick action',title:'Register an MCP integration',description:'Configure a server endpoint and access scope',icon:'⌁',run:()=>openCreate('marketplace','integration')},
   {type:'Quick action',title:'Refresh live infrastructure data',description:'Request the latest connected provider snapshot',icon:'↻',run:()=>{window.refreshData?.();notify('Refresh requested from connected providers')}} ,
   {type:'Help',title:'Keyboard shortcuts',description:'Ctrl / Cmd + K opens this command menu',icon:'⌨',run:()=>notify('Use Ctrl / Cmd + K to open the command menu. Use Esc to close it.')}
  );
 }
 function openCreate(view,kind){
  window.navigate(view);
  setTimeout(()=>{
   if(kind==='integration'){const form=$('#integration-form')||$('#add-integration')||document.querySelector('[data-open-integration]');if(form){form.click();return}notify('Open the integration registration panel from this workspace.');return}
   const button=document.querySelector('[data-create="'+kind+'"]');if(button){button.click();return}
   notify('Open the '+view+' workspace to continue.');
  },80);
 }
 function render(query=''){
  const q=query.trim().toLowerCase(),filtered=commands.filter(c=>(c.title+' '+c.description+' '+c.type).toLowerCase().includes(q));
  const list=$('#hiaido-command-list');if(!filtered.length){list.innerHTML='<div class="command-empty">No matching pages or actions. Try “incident”, “copilot” or “integration”.</div>';return}
  const types=[...new Set(filtered.map(x=>x.type))];list.innerHTML=types.map(type=>'<div class="command-group">'+type+'</div>'+filtered.filter(x=>x.type===type).map((x)=>'<button class="command-item" data-command="'+commands.indexOf(x)+'"><span class="cmd-icon">'+x.icon+'</span><span><strong>'+x.title+'</strong><small>'+x.description+'</small></span><span>↵</span></button>').join('')).join('');
  list.querySelectorAll('[data-command]').forEach(b=>b.addEventListener('click',()=>execute(Number(b.dataset.command))));
  selected=0;highlight();
 }
 function highlight(){const rows=[...$('#hiaido-command-list').querySelectorAll('.command-item')];rows.forEach((r,i)=>r.classList.toggle('selected',i===selected));rows[selected]?.scrollIntoView({block:'nearest'})}
 function execute(index){const q=commands[index];if(!q)return;close();q.run()}
 function open(){buildCommands();overlay.classList.add('open');$('#hiaido-command-input').value='';render();setTimeout(()=>$('#hiaido-command-input').focus(),20)}
 function close(){overlay.classList.remove('open')}
 const tools=$('.top-actions');if(tools){const group=document.createElement('div');group.className='enterprise-tools';group.innerHTML='<button class="enterprise-icon-btn" id="hiaido-command-open" title="Command menu (Ctrl+K)" aria-label="Open command menu">⌕</button><button class="enterprise-icon-btn" id="hiaido-quick-create" title="Quick create" aria-label="Quick create">＋</button>';const search=$('#global-search');if(search)search.insertAdjacentElement('afterend',group);else tools.prepend(group);$('#hiaido-command-open').addEventListener('click',open);$('#hiaido-quick-create').addEventListener('click',open)}
 $('#hiaido-command-input').addEventListener('input',e=>render(e.target.value));
 $('#hiaido-command-input').addEventListener('keydown',e=>{
  const rows=[...$('#hiaido-command-list').querySelectorAll('.command-item')];
  if(e.key==='ArrowDown'){e.preventDefault();selected=Math.min(selected+1,rows.length-1);highlight()}
  if(e.key==='ArrowUp'){e.preventDefault();selected=Math.max(0,selected-1);highlight()}
  if(e.key==='Enter'){e.preventDefault();const row=rows[selected];if(row)execute(Number(row.dataset.command))}
  if(e.key==='Escape')close();
 });
 overlay.addEventListener('click',e=>{if(e.target===overlay)close()});
 document.addEventListener('keydown',e=>{
  if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){e.preventDefault();open()}
  if(e.key==='Escape'&&overlay.classList.contains('open'))close();
 });
 // Collapsible navigation groups make a large enterprise information architecture easier to scan.
 groups.forEach((label,i)=>{
  const members=[];let n=label.nextElementSibling;while(n&&!n.classList.contains('nav-label')){if(n.matches('button[data-view]'))members.push(n);n=n.nextElementSibling}
  if(!members.length)return;
  label.style.cursor='pointer';label.title='Collapse or expand navigation group';label.setAttribute('aria-expanded','true');
  label.addEventListener('click',()=>{const hidden=label.getAttribute('aria-expanded')==='true';label.setAttribute('aria-expanded',String(!hidden));members.forEach(b=>b.hidden=hidden);label.textContent=(hidden?'＋ ':'− ')+label.textContent.replace(/^[＋−] /,'')});
 });
 // Keep the currently active navigation group expanded after route changes.
 const originalNavigate=window.navigate;
 if(typeof originalNavigate==='function')window.navigate=function(id){originalNavigate(id);const active=navItems.find(b=>b.dataset.view===id);if(active){let p=active.previousElementSibling;while(p&&!p.classList.contains('nav-label'))p=p.previousElementSibling;if(p&&p.getAttribute('aria-expanded')==='false')p.click()}};
 buildCommands();
 window.hiaidoCommand={open,close,notify};
})();
