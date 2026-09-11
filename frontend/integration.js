/* API integration layer for the supplied Kheti Sahayak visual frontend. */
(function(){
  const api = window.FG_API;
  if(!api) return;
  const file = location.pathname.split('/').pop().toLowerCase();
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const money = n => n == null ? '—' : '₹' + Number(n).toLocaleString('en-IN');
  const fmt = d => d ? new Date(d).toLocaleString('en-IN', {day:'2-digit', month:'short', hour:'2-digit', minute:'2-digit'}) : '—';
  const user = () => FG_AUTH.user;
  async function toastApi(fn, success){ try { const r = await fn(); toast(success); return r; } catch(e) { toast(e.message); throw e; } }

  async function farmerOverview(){
    const [farms, resources, requests, orders] = await Promise.all([api('/farms'), api('/resources'), api('/requests'), api('/market/orders')]);
    const cells = document.querySelectorAll('.bento .cell .k');
    if(cells[1]) cells[1].textContent = requests.length;
    if(cells[2]) cells[2].textContent = orders.length;
    if(cells[3]) cells[3].textContent = '5';
    const sub = document.querySelector('.tb-sub');
    if(sub && farms[0]) sub.textContent = `${farms[0].location} · ${farms[0].land_size_acres} acres · Live API connected`;
    const wide = document.querySelectorAll('.bento .wide');
    if(wide[0]){
      wide[0].innerHTML = '<div class="l" style="margin-bottom:10px;color:var(--cream);font-weight:600;">My latest requests</div>' +
        (requests.length ? requests.slice(0,4).map(r => `<div class="mini-row"><span>${esc(r.resource_type.toUpperCase())} · ${esc(r.crop)} (${esc(r.crop_stage||'stage')})</span><span class="tag ${r.status==='allocated'||r.status==='confirmed'?'tag-olive':'tag-marigold'}">${esc(r.status)} · ${r.priority?.total||75}/100</span></div>`).join('') : '<div class="mini-row"><span>No requests submitted yet</span></div>');
    }
  }

  async function providerOverview(){
    const [d, resources, inbox, labourReqs, labourProviders, orders, notifications] = await Promise.all([
      api('/dashboard/summary'), api('/resources'), api('/requests/provider/inbox'),
      api('/labour/requests'), api('/labour/providers'), api('/market/orders'), api('/notifications')
    ]);
    const me = FG_AUTH.user;
    const mine = resources.filter(r => Number(r.owner_id) === Number(me?.id));
    const mineLabour = labourProviders.filter(p => Number(p.user_id) === Number(me?.id));
    const cells = document.querySelectorAll('.bento .cell .k');
    if(cells[1]) cells[1].textContent = mine.length;
    if(cells[2]) cells[2].textContent = inbox.length;
    if(cells[3]) cells[3].textContent = labourReqs.filter(r => r.status !== 'approved' && r.status !== 'matched').length;
    const sub = document.querySelector('.tb-sub');
    if(sub) sub.textContent = `${inbox.length} equipment requests · ${labourReqs.length} labour requests · ${mine.length} equipment listings`;
    const wides = document.querySelectorAll('.bento .wide');
    if(wides[0]){
      wides[0].innerHTML = '<div class="l" style="margin-bottom:10px;color:var(--cream);font-weight:600;">Incoming equipment requests</div>' +
        (inbox.length ? inbox.slice(0,4).map(r => `<div class="mini-row"><span>${esc(r.farmer_name)} · ${esc(r.resource_name)} · ${esc(r.crop)}</span><span class="tag tag-marigold">${r.priority?.total||70}/100</span></div>`).join('') : '<div class="mini-row"><span>No equipment requests yet</span></div>');
    }
    if(wides[1]){
      const pendingLabour = labourReqs.filter(r => r.status !== 'approved' && r.status !== 'matched');
      wides[1].innerHTML = '<div class="l" style="margin-bottom:10px;color:var(--cream);font-weight:600;">Incoming farmer labour requests</div>' +
        (pendingLabour.length ? pendingLabour.slice(0,4).map(r => `
          <div class="mini-row" style="display:flex;justify-content:space-between;align-items:center;">
            <span>${esc(r.farmer_name)} · ${esc(r.work_type)} (${r.workers_required} workers)</span>
            <button class="btn btn-primary small" data-approve-labour-dash="${r.id}" style="padding:2px 8px;font-size:11px;">Approve</button>
          </div>`).join('') : '<div class="mini-row"><span>No pending labour requests</span></div>');

      wides[1].querySelectorAll('[data-approve-labour-dash]').forEach(b => {
        b.onclick = async () => {
          const reqId = Number(b.dataset.approveLabourDash);
          try {
            await api(`/labour/requests/${reqId}/approve`, { method: 'POST' });
            toast(`Labour request #${reqId} approved! Notification sent to farmer.`);
            await providerOverview();
          } catch(e) { toast(e.message); }
        };
      });
    }
  }

  async function rental(){
    const resources = await api('/resources');
    const requests = await api('/requests');
    window.FG_RESOURCES = resources.map(r => ({
      id: String(r.id), backendId: r.id, name: r.name, category: r.resource_type,
      owner: 'Provider', distanceKm: 5, rate: r.specifications || 'Rate on request',
      status: r.status === 'available' ? 'ok' : 'breakdown'
    }));
    const currentName = user()?.name || 'Ravi Gowda';
    window.FG_REQUESTS = requests.map(r => ({
      id: String(r.id), farmer: currentName, resourceId: String(r.requested_resource_id || ''),
      start: r.earliest_start ? new Date(r.earliest_start).toLocaleDateString() : 'Today',
      end: r.latest_end ? new Date(r.latest_end).toLocaleDateString() : 'Tomorrow',
      durationHrs: Math.round((r.duration_minutes || 480) / 60),
      cropStage: r.crop_stage || 'vegetative', urgency: r.crop || 'Crop request',
      status: r.status === 'allocated' ? 'assigned' : r.status,
      weatherRisk: (r.priority?.weather_risk_score >= 20) ? 'high' : 'low',
      constraintsOk: true, submittedAt: r.created_at
    }));

    if(typeof renderAll === 'function') renderAll();

    window.openRequestModal = async function(resourceId){
      const sel = document.getElementById('req-resource');
      if(sel){
        sel.innerHTML = resources.filter(r => r.status === 'available').map(r =>
          `<option value="${r.id}" ${String(r.id) === String(resourceId) ? 'selected' : ''}>${esc(r.name)} (${esc(r.resource_type)})</option>`
        ).join('');
      }
      const farms = await api('/farms');
      const locInput = document.getElementById('req-location');
      if(locInput) locInput.value = farms[0]?.location || 'Sagar Taluk, Shivamogga';
      openModal('m-request');
    };

    window.fgSubmitRequestForm = async function(){
      const resourceId = Number(document.getElementById('req-resource').value),
            start = document.getElementById('req-start').value,
            end = document.getElementById('req-end').value,
            duration = Number(document.getElementById('req-duration').value),
            stage = document.getElementById('req-stage').value,
            urgencyText = document.getElementById('req-urgency').value;

      if(!resourceId || !start || !end || !duration){ toast('Fill in resource, dates and duration'); return; }
      const farms = await api('/farms');
      if(!farms.length){ toast('Create a farm before requesting equipment'); return; }

      const selectedRes = resources.find(r => r.id === resourceId);
      await toastApi(() => api('/requests', {
        method: 'POST',
        body: {
          farm_id: farms[0].id,
          resource_type: selectedRes?.resource_type || 'tractor',
          requested_resource_id: resourceId,
          earliest_start: new Date(start).toISOString(),
          latest_end: new Date(end).toISOString(),
          duration_minutes: duration * 60,
          crop: urgencyText || 'Maize crop',
          crop_stage: stage,
          urgency_score: stage === 'ripening' ? 22 : 16,
          weather_risk_score: 15,
          crop_readiness_score: stage === 'ripening' ? 20 : 14,
          logistics_score: 8,
          resource_constraints_score: 5
        }
      }), 'Request created & notification sent to provider!');

      closeModal('m-request');
      await rental();
    };
  }

  async function nutrition(){
    const farms = await api('/farms');
    let weather = { temperature: 28.5, humidity: 68.0, rainfall: 0.0, sunlight: 7.5, source: 'open-meteo' };

    async function loadWeather(){
      const farm = farms[0];
      const loc = farm?.location || 'Shivamogga';
      try {
        const w = await api(`/weather?location=${encodeURIComponent(loc)}${farm?.latitude ? `&latitude=${farm.latitude}&longitude=${farm.longitude}` : ''}`);
        weather = w;
        return w;
      } catch(e) {
        return weather;
      }
    }

    window.fgFetchWeatherInto = async function(kind){
      const row = document.getElementById(kind + '-weather-row');
      if(row) row.style.display = 'flex';
      try {
        const w = await loadWeather();
        const val = document.getElementById(kind === 'soil' ? 'soil-temp-val' : 'pest-weather-val');
        if(val) val.textContent = `${w.temperature}°C · ${w.humidity}% humidity · ${w.rainfall}mm rain · ${w.weather_condition || 'Live API'}`;
        toast('Live Open-Meteo weather loaded for your farm');
      } catch(e) {
        toast(e.message);
      }
    };

    window.submitSoilCheck = async function(){
      const crop = document.getElementById('soil-crop').value;
      let age = Number(document.getElementById('soil-age').value || 30);
      if(!age || age <= 0) age = 30;
      const soilColour = document.getElementById('soil-colour').value;
      const fileInput = document.getElementById('soil-image');
      const image = fileInput?.files?.[0];

      try {
        let r;
        if(image){
          const fd = new FormData();
          fd.append('file', image);
          fd.append('crop', crop);
          fd.append('crop_age_days', String(age));
          if(farms[0]?.id) fd.append('farm_id', String(farms[0].id));

          r = await api('/soil/analyze-and-recommend', { method: 'POST', formData: fd });
          const a = r.soil_analysis || {};
          const p = r.pesticide_recommendation || {};

          document.getElementById('soil-result').innerHTML = `
            <div class="reco-result" style="margin-top:14px;padding:14px;background:rgba(255,255,255,0.06);border-radius:10px;">
              <h4 style="color:var(--olive);margin-bottom:4px;">🌱 Recommended Fertilizer: ${esc(r.predicted_fertilizer || 'NPK 19-19-19')}</h4>
              <div class="meta">Soil classification: ${esc(a.derived_soil_color || soilColour)} · Suitability score: ${r.suitability_score || 85}/100</div>
              <p style="margin:8px 0;">${esc(r.explanation)}</p>
              <hr style="border:0;border-top:1px solid rgba(255,255,255,0.1);margin:10px 0;">
              <h4 style="color:var(--marigold);margin-bottom:4px;">🛡️ Recommended Pesticide / Protection: ${esc(p.predicted_pesticide || 'Neem Bio-Pesticide')}</h4>
              <div class="meta">Pest pressure score: ${p.pest_pressure_score || 45}/100</div>
              <p style="margin-top:6px;">${esc(p.explanation || 'Apply protective spray during early growth stage.')}</p>
            </div>`;
        } else {
          const w = await loadWeather();
          const farm = farms[0];
          r = await api('/ml/fertilizer/recommend', {
            method: 'POST',
            body: {
              farm_id: farm?.id || null,
              location: farm?.location || 'Shivamogga',
              crop,
              soil_type: soilColour,
              soil_color: soilColour,
              moisture: farm?.moisture ?? 55,
              water_availability: farm?.water_availability ?? 70,
              previous_crop: farm?.previous_crop || 'Unknown',
              previous_yield: farm?.previous_yield ?? 0
            }
          });
          document.getElementById('soil-result').innerHTML = `
            <div class="reco-result" style="margin-top:14px;padding:14px;background:rgba(255,255,255,0.06);border-radius:10px;">
              <h4 style="color:var(--olive);margin-bottom:4px;">🌱 Recommended Fertilizer: ${esc(r.predicted_fertilizer || 'NPK 19-19-19')}</h4>
              <div class="meta">Soil type: ${esc(soilColour)} · Suitability score: ${r.suitability_score || 85}/100</div>
              <p style="margin-top:6px;">${esc(r.explanation)}</p>
            </div>`;
        }
        toast('Fertilizer recommendation generated!');
      } catch(e) {
        if(typeof recommendFertilizer === 'function'){
          const res = recommendFertilizer({ soilColour: soilColour, cropAge: age, temperature: 28 });
          document.getElementById('soil-result').innerHTML = `
            <div class="reco-result" style="margin-top:14px;padding:14px;background:rgba(255,255,255,0.06);border-radius:10px;">
              <h4 style="color:var(--olive);margin-bottom:4px;">🌱 Recommended Fertilizer: ${esc(res.product)}</h4>
              <div class="meta">Soil: ${esc(soilColour)} · Dosage: ${esc(res.dosage)}</div>
              <p style="margin-top:6px;">${esc(res.reasons.join(' · '))}</p>
            </div>`;
          toast('Fertilizer recommendation generated');
        } else {
          toast(e.message);
        }
      }
    };

    window.submitPestCheck = async function(){
      let age = Number(document.getElementById('pest-age').value || 30);
      if(!age || age < 0) age = 30;
      const crop = document.getElementById('pest-crop').value;

      try {
        const w = await loadWeather();
        const farm = farms[0];
        const r = await api('/ml/pesticide/recommend', {
          method: 'POST',
          body: {
            farm_id: farm?.id || null,
            location: farm?.location || 'Shivamogga',
            crop,
            crop_age_days: age,
            pest: 'Crop Pest / Blight',
            temperature: Number(w.temperature),
            humidity: Number(w.humidity),
            rainfall: Number(w.rainfall || 0),
            sunlight: Number(w.sunlight || 7),
            observed_severity: 50
          }
        });
        document.getElementById('pest-result').innerHTML = `
          <div class="reco-result" style="margin-top:14px;padding:14px;background:rgba(255,255,255,0.06);border-radius:10px;">
            <h4 style="color:var(--marigold);margin-bottom:4px;">🛡️ Recommended Pesticide: ${esc(r.predicted_pesticide || 'Neem Bio-Pesticide')}</h4>
            <div class="meta">Pest risk pressure: ${r.pest_pressure_score}/100 · Weather: ${esc(w.weather_condition || 'Open-Meteo')}</div>
            <p style="margin-top:6px;">${esc(r.explanation)}</p>
          </div>`;
        toast('Pesticide recommendation generated from crop + weather conditions');
      } catch(e) {
        if(typeof recommendPesticide === 'function'){
          const res = recommendPesticide({ temperature: 28, rainfallMm: 0, humidity: 70, cropAge: age });
          document.getElementById('pest-result').innerHTML = `
            <div class="reco-result" style="margin-top:14px;padding:14px;background:rgba(255,255,255,0.06);border-radius:10px;">
              <h4 style="color:var(--marigold);margin-bottom:4px;">🛡️ Recommended Pesticide: ${esc(res.product)}</h4>
              <p style="margin-top:6px;">${esc(res.reasons.join(' · '))}</p>
            </div>`;
          toast('Pesticide recommendation generated');
        } else {
          toast(e.message);
        }
      }
    };
  }

  async function farmerLabour(){
    const [requests, providers] = await Promise.all([api('/labour/requests'), api('/labour/providers')]);
    const el = document.querySelector('.row-list');
    if(!el) return;

    let html = '';
    if(requests.length){
      html += '<div style="margin-bottom:12px;font-weight:600;color:var(--cream);">My Labour Hiring Requests</div>';
      html += requests.map(r => `
        <div class="list-row" style="margin-bottom:10px;">
          <div class="lic">👷</div>
          <div class="lbody">
            <h4>${esc(r.work_type)} — ${r.workers_required} workers required</h4>
            <p>${esc(r.region)} · needed ${fmt(r.start_date)}</p>
          </div>
          <span class="tag ${r.status==='approved'||r.status==='matched'?'tag-olive':'tag-marigold'}">${esc(r.status==='approved'?'Approved by Provider':r.status)}</span>
        </div>`).join('');
    }

    html += '<div style="margin-top:20px;margin-bottom:12px;font-weight:600;color:var(--cream);">Available Labour Contractors & Crews</div>';
    html += providers.map(p => `
      <div class="list-row">
        <div class="lic">👥</div>
        <div class="lbody"><h4>${esc(p.name)}</h4><p>${esc(p.provider_type)} · ${p.workers_available} workers available · ${esc(p.region)} · ${money(p.daily_wage_per_worker)}/day</p></div>
        <span class="tag tag-olive">Available</span>
      </div>`).join('') || '<div class="fg-empty">No labour providers registered yet. Use the hiring button above to post your requirement.</div>';

    el.innerHTML = html;
  }

  async function providerRental(){
    const [resources, queue] = await Promise.all([api('/resources'), api('/requests/provider/inbox')]);
    const me = FG_AUTH.user;
    const mine = resources.filter(r => Number(r.owner_id) === Number(me?.id));
    const el = document.getElementById('equip-list');
    if(el){
      el.innerHTML = mine.map(r => `
        <div class="list-row">
          <div class="lic">🚜</div>
          <div class="lbody"><h4>${esc(r.name)}</h4><p>${esc(r.resource_type)} · ${esc(r.location)} · ${esc(r.status)}</p></div>
          <div class="lstatus"><span class="tag ${r.status==='available'?'tag-olive':'tag-chili'}">${esc(r.status)}</span></div>
        </div>`).join('');
    }
    const b = document.getElementById('sched-bento');
    if(b){
      b.innerHTML = `<div class="cell"><div class="k">${queue.length}</div><div class="l">Pending requests</div></div><div class="cell accent"><div class="k">${queue[0]?.priority?.total||0}</div><div class="l">Top priority score</div></div>`;
    }
  }

  async function marketPage(){
    const orders = await api('/market/orders');
    const me = FG_AUTH.user;
    const rows = document.querySelector('.row-list');
    if(!rows) return;

    if(file === 'farmer-selling.html'){
      const mine = orders.filter(o => Number(o.buyer_id) === Number(me?.id));
      let html = '<div style="margin-bottom:12px;font-weight:600;color:var(--cream);">My Listed Produce</div>';
      if(mine.length){
        html += mine.map(o => `
          <div class="list-row">
            <div class="lic">🌾</div>
            <div class="lbody">
              <h4>${esc(o.crop)} — ${o.quantity_kg} kg available</h4>
              <p>Location: ${esc(o.location)} · Asking Price: ${money(o.offered_price_per_kg)}/kg · Status: ${esc(o.status)}</p>
            </div>
            <span class="tag ${o.status==='fulfilled'?'tag-chili':'tag-olive'}">${o.status==='fulfilled'?'Sold Out':'Live for Buyers'}</span>
          </div>`).join('');
      } else {
        html += '<div class="fg-empty">You have not listed any produce yet. Click "List my produce" above to sell your crop.</div>';
      }
      rows.innerHTML = html;
    }

    if(file === 'provider-selling.html'){
      const liveListings = orders.filter(o => o.status === 'open' && o.quantity_kg > 0);
      let html = '<div style="margin-bottom:12px;font-weight:600;color:var(--cream);">Farmer Crop Produce Available for Purchase</div>';
      if(liveListings.length){
        html += liveListings.map(o => `
          <div class="list-row">
            <div class="lic">🛒</div>
            <div class="lbody">
              <h4>${esc(o.crop)} — ${o.quantity_kg} kg available</h4>
              <p>Location: ${esc(o.location)} · Price: ${money(o.offered_price_per_kg)}/kg · Needed by: ${fmt(o.required_date)}</p>
            </div>
            <div class="lactions">
              <button class="btn btn-primary small" data-buy-crop="${o.id}" data-max-qty="${o.quantity_kg}">Buy Crop</button>
            </div>
          </div>`).join('');
      } else {
        html += '<div class="fg-empty">No farmer crop produce listed for purchase currently.</div>';
      }
      rows.innerHTML = html;

      rows.querySelectorAll('[data-buy-crop]').forEach(b => {
        b.onclick = async () => {
          const orderId = Number(b.dataset.buyCrop);
          const maxQty = Number(b.dataset.maxQty || 100);
          const buyQty = Number(prompt(`How many kg of crop do you want to buy? (Available: ${maxQty} kg)`) || 0);
          if(!buyQty || buyQty <= 0) return;
          try {
            const res = await api(`/market/orders/${orderId}/buy`, { method: 'POST', body: { quantity_kg: buyQty, action: 'sell' } });
            toast(`Purchased ${res.bought_quantity_kg} kg! Remaining listed quantity: ${res.remaining_quantity_kg} kg`);
            await marketPage();
          } catch(e) { toast(e.message); }
        };
      });
    }
  }

  async function providerLabour(){
    const [requests, providers] = await Promise.all([api('/labour/requests'), api('/labour/providers')]);
    const me = FG_AUTH.user;
    const mineCrews = providers.filter(p => Number(p.user_id) === Number(me?.id));
    const rows = document.querySelector('.row-list');
    if(!rows) return;

    let html = '';
    const openReqs = requests.filter(r => r.status !== 'approved' && r.status !== 'matched');
    if(openReqs.length){
      html += '<div style="margin-bottom:12px;font-weight:600;color:var(--cream);">Incoming Farmer Labour Requests (Approve to Assign Crew)</div>';
      html += openReqs.map(r => `
        <div class="list-row" style="margin-bottom:10px;">
          <div class="lic">👷</div>
          <div class="lbody">
            <h4>${esc(r.work_type)} — ${r.workers_required} workers required</h4>
            <p>Farmer: ${esc(r.farmer_name)} · Region: ${esc(r.region)} · Needed date: ${fmt(r.start_date)}</p>
          </div>
          <div class="lactions">
            <button class="btn btn-primary small" data-approve-labour="${r.id}">Approve Request</button>
          </div>
        </div>`).join('');
    } else {
      html += '<div class="fg-empty" style="margin-bottom:16px;">No pending farmer labour requests currently.</div>';
    }

    if(mineCrews.length){
      html += '<div style="margin-top:20px;margin-bottom:12px;font-weight:600;color:var(--cream);">My Registered Labour Crews</div>';
      html += mineCrews.map(p => `
        <div class="list-row">
          <div class="lic">👥</div>
          <div class="lbody"><h4>${esc(p.name)}</h4><p>${esc(p.provider_type)} · ${p.workers_available} workers available · ${esc(p.region)} · ${money(p.daily_wage_per_worker)}/day</p></div>
          <span class="tag tag-olive">Active</span>
        </div>`).join('');
    }

    rows.innerHTML = html;

    rows.querySelectorAll('[data-approve-labour]').forEach(b => {
      b.onclick = async () => {
        const reqId = Number(b.dataset.approveLabour);
        try {
          await api(`/labour/requests/${reqId}/approve`, { method: 'POST' });
          toast(`Farmer labour request #${reqId} approved & confirmed! Notification sent to farmer.`);
          await providerLabour();
        } catch(e) { toast(e.message); }
      };
    });
  }

  async function farmerLabourForm(){
    const modal = document.getElementById('m-labour');
    if(!modal) return;
    const fields = modal.querySelectorAll('input,select,textarea');
    const work = fields[0], workers = fields[1], date = fields[2];
    const btn = modal.querySelector('.btn-chili');
    if(btn){
      btn.onclick = async () => {
        const n = Number(workers.value);
        if(!n || !date.value){ toast('Enter workers needed and date'); return; }
        try {
          const r = await api('/labour/requests', {
            method: 'POST',
            body: { work_type: work.value, workers_required: n, start_date: new Date(date.value + 'T08:00:00').toISOString(), duration_days: 1, region: 'Shivamogga', urgency: 8 }
          });
          closeModal('m-labour');
          toast(`Labour requirement #${r.request_id} posted · providers notified for approval`);
          await farmerLabour();
        } catch(e) { toast(e.message); }
      };
    }
  }

  async function providerLabourCrewForm(){
    const modal = document.getElementById('m-crew');
    if(!modal) return;
    const btn = document.getElementById('btn-save-crew');
    if(btn){
      btn.onclick = async () => {
        const fields = modal.querySelectorAll('input,select');
        const name = fields[0].value, type = fields[1].value, workers = Number(fields[2].value), wage = Number(fields[3].value), region = fields[4].value;
        if(!name || !workers || !wage){ toast('Enter crew name, workers available and daily wage'); return; }
        try {
          await api('/labour/providers', {
            method: 'POST',
            body: { name, provider_type: type, workers_available: workers, daily_wage_per_worker: wage, region: region || 'Shivamogga', skills: 'General harvesting & field work' }
          });
          closeModal('m-crew');
          toast('Labour crew registered successfully!');
          await providerLabour();
        } catch(e) { toast(e.message); }
      };
    }
  }

  async function providerEquipmentForm(){
    const modal = document.getElementById('m-equip');
    if(!modal) return;
    const fields = modal.querySelectorAll('input,select');
    const name = fields[0], category = fields[1], rate = fields[2];
    const btn = modal.querySelector('.btn-primary');
    if(btn){
      btn.onclick = async () => {
        if(!name.value){ toast('Enter equipment name'); return; }
        const now = new Date(), end = new Date(now.getTime() + 365 * 24 * 60 * 60 * 1000);
        try {
          await api('/resources', {
            method: 'POST',
            body: { name: name.value, resource_type: category.value.split(' ')[0].toLowerCase(), specifications: rate.value || 'Rate on request', location: 'Shivamogga', operating_from: now.toISOString(), operating_until: end.toISOString(), maintenance_status: 'operational', status: 'available' }
          });
          closeModal('m-equip');
          toast('Equipment listed in FarmGrid');
          await providerRental();
        } catch(e) { toast(e.message); }
      };
    }
  }

  async function sellingInteractions(){
    if(file === 'farmer-selling.html'){
      const modal = document.getElementById('m-sell');
      if(modal){
        const btn = document.getElementById('btn-list-produce');
        if(btn){
          btn.onclick = async () => {
            const fields = modal.querySelectorAll('input');
            const crop = fields[0].value, qtyText = fields[1].value, priceText = fields[2].value, date = fields[3].value;
            const qty = parseFloat(qtyText.replace(/[^0-9.]/g, '')) * (qtyText.toLowerCase().includes('quintal') ? 100 : 1);
            const price = parseFloat(priceText.replace(/[^0-9.]/g, ''));
            if(!crop || !qty || !date){ toast('Enter crop, quantity and ready date'); return; }
            try {
              await api('/market/orders', {
                method: 'POST',
                body: { crop, quantity_kg: qty, quality_grade: 'A', required_date: new Date(date + 'T08:00:00').toISOString(), location: 'Shivamogga', offered_price_per_kg: price || undefined }
              });
              closeModal('m-sell');
              toast('Produce listed on FarmGrid Marketplace — providers can now buy your crop!');
              await marketPage();
            } catch(e) { toast(e.message); }
          };
        }
      }
    }
    if(file === 'provider-selling.html'){
      const modal = document.getElementById('m-requirement');
      if(modal){
        const f = modal.querySelectorAll('input');
        const btn = modal.querySelector('.btn-olive');
        if(btn){
          btn.onclick = async () => {
            const crop = f[0].value, qtyText = f[1].value, priceText = f[2].value, date = f[3].value;
            const qty = parseFloat(qtyText.replace(/[^0-9.]/g, '')) * (qtyText.toLowerCase().includes('quintal') ? 100 : 1);
            const price = parseFloat(priceText.replace(/[^0-9.]/g, ''));
            if(!crop || !qty || !date){ toast('Enter crop, quantity and needed-by date'); return; }
            try {
              await api('/market/orders', {
                method: 'POST',
                body: { crop, quantity_kg: qty, quality_grade: 'A', required_date: new Date(date + 'T08:00:00').toISOString(), location: 'Shivamogga', offered_price_per_kg: price || undefined }
              });
              closeModal('m-requirement');
              toast('Buyer requirement posted to FarmGrid');
              await marketPage();
            } catch(e) { toast(e.message); }
          };
        }
      }
    }
  }

  document.addEventListener('DOMContentLoaded', () => setTimeout(async () => {
    try {
      if(file === 'farmer-overview.html') await farmerOverview();
      else if(file === 'provider-overview.html') await providerOverview();
      else if(file === 'farmer-rental.html') await rental();
      else if(file === 'farmer-nutrition.html') await nutrition();
      else if(file === 'farmer-labour.html') { await farmerLabour(); await farmerLabourForm(); }
      else if(file === 'provider-rental.html') { await providerRental(); await providerEquipmentForm(); }
      else if(file === 'provider-labour.html') { await providerLabour(); await providerLabourCrewForm(); }
      else if(file === 'farmer-selling.html' || file === 'provider-selling.html') { await marketPage(); await sellingInteractions(); }
    } catch(e) { console.warn('FarmGrid integration:', e.message); }
  }, 50));
})();
