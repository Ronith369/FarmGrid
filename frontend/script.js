/* Authentication/session glue for the static dashboard UI. */
document.addEventListener('DOMContentLoaded', async function(){
  if (!window.FG_AUTH) return;
  const file = location.pathname.split('/').pop().toLowerCase();
  if (file === 'index.html' || file === '' || file === 'login.html') return;
  const role = file.startsWith('farmer-') ? 'farmer' : file.startsWith('provider-') ? 'resource_owner' : null;
  const user = await FG_AUTH.require(role);
  if (!user) return;
  document.querySelectorAll('.sb-user').forEach(el=>{
    const avatar=el.querySelector('.sb-avatar'), name=el.querySelector('.un'), sub=el.querySelector('.ul');
    if(avatar) avatar.textContent=(user.name||'User').split(/\s+/).map(x=>x[0]).join('').slice(0,2).toUpperCase();
    if(name) name.textContent=user.name||'User';
    if(sub) sub.textContent=user.email||user.role;
  });
  initFarmGridNotifications();

  document.querySelectorAll('.tb-right').forEach(el=>{
    if(!el.querySelector('[data-fg-logout]')){
      const b=document.createElement('button'); b.className='tb-icon-btn'; b.setAttribute('data-fg-logout','1'); b.title='Sign out'; b.textContent='↪'; b.onclick=()=>{FG_AUTH.clear();location.href='index.html'}; el.appendChild(b);
    }
  });
});

function openModal(id){ document.getElementById(id).classList.add('active'); }
function closeModal(id){ document.getElementById(id).classList.remove('active'); }
document.addEventListener('DOMContentLoaded', function(){
  document.querySelectorAll('.modal-bg').forEach(function(m){
    m.addEventListener('click', function(e){ if(e.target===m) m.classList.remove('active'); });
  });
  var ham = document.getElementById('hamburger');
  if(ham){ ham.addEventListener('click', function(){ document.querySelector('.sidebar').classList.toggle('open'); }); }
});
function toast(msg){
  var t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(window._tt);
  window._tt = setTimeout(function(){ t.classList.remove('show'); }, 2600);
}
function switchTab(btn, tab){
  var tabs = btn.parentElement.querySelectorAll('.tab-btn');
  tabs.forEach(function(t){ t.classList.remove('active'); });
  btn.classList.add('active');
  document.getElementById('tab-fert').style.display = tab==='fert' ? 'grid' : 'none';
  document.getElementById('tab-pest').style.display = tab==='pest' ? 'grid' : 'none';
}
function acceptRow(btn){
  var row = btn.closest('.list-row');
  var actions = row.querySelector('.lactions');
  actions.outerHTML = '<span class="tag tag-marigold">Accepted</span>';
  toast('Crew assigned \u2014 farmer notified');
}
function declineRow(btn){
  var row = btn.closest('.list-row');
  row.style.opacity = '0.35';
  var actions = row.querySelector('.lactions');
  if(actions) actions.outerHTML = '<span class="tag tag-muted">Declined</span>';
}


async function initFarmGridNotifications(){
  try{
    const items=await FG_API('/notifications');
    const unread=items.filter(n=>!n.is_read).length;
    document.querySelectorAll('.tb-right').forEach(el=>{
      const bell=el.querySelector('[title="Notifications"]');
      if(!bell) return;
      bell.setAttribute('data-fg-notify','1');
      const dot=bell.querySelector('.dot');
      if(dot) dot.style.display=unread?'block':'none';
      bell.onclick=()=>showNotificationPanel(items);
    });
  }catch(e){ console.warn('Notifications:',e.message); }
}

function showNotificationPanel(items){
  let panel=document.getElementById('fg-notification-panel');
  if(panel) panel.remove();
  panel=document.createElement('div');
  panel.id='fg-notification-panel';
  panel.style.cssText='position:fixed;right:22px;top:74px;width:min(420px,calc(100vw - 44px));max-height:70vh;overflow:auto;background:var(--panel);border:1px solid var(--line);border-radius:14px;box-shadow:0 20px 60px #0008;z-index:9999;padding:16px;';
  panel.innerHTML='<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px"><strong>Notifications</strong><button class="btn btn-ghost small" id="fg-close-notify">Close</button></div>' +
    (items.length?items.map(n=>'<div style="padding:12px 0;border-top:1px solid var(--line);opacity:'+(n.is_read?'.7':'1')+'"><div style="font-weight:700">'+escNotify(n.title)+'</div><div style="font-size:.82rem;color:var(--muted);margin-top:4px">'+escNotify(n.message)+'</div><div style="display:flex;justify-content:space-between;align-items:center;margin-top:8px;font-size:.72rem;color:var(--muted)"><span>'+new Date(n.created_at).toLocaleString('en-IN')+'</span>'+(!n.is_read?'<button class="btn btn-ghost small" data-read="'+n.id+'">Mark read</button>':'')+'</div></div>').join(''):'<div style="padding:20px 0;color:var(--muted)">No notifications yet.</div>');
  document.body.appendChild(panel);
  document.getElementById('fg-close-notify').onclick=()=>panel.remove();
  panel.querySelectorAll('[data-read]').forEach(b=>b.onclick=async()=>{await FG_API('/notifications/'+b.dataset.read+'/read',{method:'POST'});panel.remove();initFarmGridNotifications();});
}
function escNotify(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
