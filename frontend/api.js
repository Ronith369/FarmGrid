/* FarmGrid API client shared by the HTML dashboards. */
(function(){
  const API_BASE = (window.FG_API_URL || '/api').replace(/\/$/, '');
  async function api(path, options={}) {
    const {method='GET', body, token=localStorage.getItem('fg_token'), formData} = options;
    const headers = {};
    if (token) headers.Authorization = 'Bearer ' + token;
    if (!formData) headers['Content-Type'] = 'application/json';
    const res = await fetch(API_BASE + path, { method, headers, body: formData || (body === undefined ? undefined : JSON.stringify(body)) });
    let data = null; try { data = await res.json(); } catch (_) {}
    if (!res.ok) {
      const detail = data && data.detail;
      const msg = typeof detail === 'string' ? detail : (detail && detail.message) || data?.error || `Request failed (${res.status})`;
      throw new Error(msg);
    }
    return data;
  }
  window.FG_API = api;
  window.FG_AUTH = {
    get token(){ return localStorage.getItem('fg_token') || ''; },
    get user(){ try { return JSON.parse(localStorage.getItem('fg_user') || 'null'); } catch (_) { return null; } },
    setSession(token,user){ localStorage.setItem('fg_token', token); localStorage.setItem('fg_user', JSON.stringify(user)); },
    startRoleSwitch(role,next){ this.clear(); location.href='login.html?role='+encodeURIComponent(role)+'&next='+encodeURIComponent(next); },
    clear(){ localStorage.removeItem('fg_token'); localStorage.removeItem('fg_user'); },
    async require(role){
      if (!localStorage.getItem('fg_token')) { location.href='login.html?next='+encodeURIComponent(location.pathname.split('/').pop())+'&role='+(role||''); return null; }
      try {
        const user = await api('/auth/me');
        localStorage.setItem('fg_user', JSON.stringify(user));
        if (role && user.role !== role && !(role === 'resource_owner' && user.role === 'admin')) {
          const target = user.role === 'farmer' ? 'farmer-overview.html' : 'provider-overview.html';
          if (!location.pathname.endsWith(target)) location.href = target;
          return null;
        }
        return user;
      } catch (_) { this.clear(); location.href='login.html'; return null; }
    }
  };
})();
