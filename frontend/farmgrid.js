/* =======================================================================
   FarmGrid Coordination Engine
   Rule-based priority scoring, conflict detection, time-slot scheduling
   with buffers, disruption/reallocation, and offline-first request queue.
   All data below is synthetic seed data for demo purposes (per hackathon
   brief: "Machine learning is not mandatory... use synthetic seed data").
   ======================================================================= */

(function(){

  var DAY = 24*60*60*1000;
  function today(){ return new Date('2026-09-11T09:00:00'); } // fixed "now" for a stable demo
  function daysFromNow(n){ var d = new Date(today().getTime()+n*DAY); return d.toISOString().slice(0,10); }
  function hoursAgo(h){ return new Date(today().getTime()-h*60*60*1000); }

  /* ---------------- Seed resources (rental units) ---------------- */
  window.FG_RESOURCES = [
    {id:'R1', name:'Mahindra 575 DI Tractor', category:'Tractor', owner:'Suresh & Nagaraj Agri', distanceKm:3.1, rate:'₹1,800/day', status:'ok'},
    {id:'R2', name:'Rotavator — 6ft', category:'Tiller', owner:'Manjunath Traders', distanceKm:4.5, rate:'₹700/day', status:'ok'},
    {id:'R3', name:'Boom Sprayer Drone', category:'Sprayer', owner:'AgriDrone Co-op', distanceKm:6.8, rate:'₹1,200/acre', status:'ok'},
    {id:'R4', name:'Combine Harvester', category:'Harvester', owner:'Suresh & Nagaraj Agri', distanceKm:9.2, rate:'₹3,500/day', status:'ok'},
    {id:'R4B', name:'Combine Harvester (Backup Unit)', category:'Harvester', owner:'Ganesh Farm Equip', distanceKm:11.4, rate:'₹3,650/day', status:'ok'},
    {id:'R5', name:'Seed Drill — 9 row', category:'Seed Drill', owner:'Ganesh Farm Equip', distanceKm:5.0, rate:'₹600/day', status:'ok'},
    {id:'R6', name:'Power Tiller', category:'Tiller', owner:'Manjunath Traders', distanceKm:2.4, rate:'₹550/day', status:'ok'}
  ];

  /* ---------------- Seed requests (three farmers competing for the
     Combine Harvester — demonstrates conflict + priority scoring) ---- */
  window.FG_REQUESTS = [
    {id:'Q1', farmer:'Ravi Gowda', resourceId:'R4', start:daysFromNow(2), end:daysFromNow(2), durationHrs:8,
      cropStage:'ripening', urgency:'Paddy fully ripe; heavy rain forecast in 3 days could flatten the crop.',
      submittedAt:hoursAgo(6), weatherRisk:'high', constraintsOk:true, status:'pending'},
    {id:'Q2', farmer:'Manjunath H.S.', resourceId:'R4', start:daysFromNow(2), end:daysFromNow(2), durationHrs:5,
      cropStage:'ripening', urgency:'Maize harvest window closing before local grain market rate drop.',
      submittedAt:hoursAgo(30), weatherRisk:'medium', constraintsOk:true, status:'pending'},
    {id:'Q3', farmer:'Lakshmi Devi', resourceId:'R4', start:daysFromNow(3), end:daysFromNow(3), durationHrs:6,
      cropStage:'vegetative', urgency:'Exploring options, can shift dates if needed.',
      submittedAt:hoursAgo(2), weatherRisk:'low', constraintsOk:false, status:'pending'}
  ];

  window.FG_OFFLINE_QUEUE = [];
  window.FG_OFFLINE = false;
  window.FG_ACTIVITY = [];
  var qCounter = 100;

  /* ---------------- Priority scoring (0-100, six explainable factors,
     weights match the benchmark model in the FarmGrid brief) --------- */
  function daysUntil(dateStr){
    var d = new Date(dateStr+'T00:00:00');
    return Math.max(0, Math.round((d.getTime()-today().getTime())/DAY));
  }
  function urgencyPts(req){
    var d = daysUntil(req.end);
    if(d<=1) return 25; if(d<=2) return 21; if(d<=4) return 16; if(d<=7) return 10; return 5;
  }
  function weatherPts(req){ return {high:25, medium:15, low:5}[req.weatherRisk] || 5; }
  function cropStagePts(req){ return {ripening:20, flowering:14, vegetative:8, planting:4}[req.cropStage] || 8; }
  function queueWaitPts(req){
    var hrs = (today().getTime()-new Date(req.submittedAt).getTime())/(60*60*1000);
    return Math.max(1, Math.min(15, Math.round(hrs/4)));
  }
  function distancePts(req){
    var res = FG_RESOURCES.filter(function(r){return r.id===req.resourceId;})[0];
    var km = res ? res.distanceKm : 8;
    if(km<=3) return 10; if(km<=6) return 8; if(km<=10) return 6; if(km<=15) return 4; return 2;
  }
  function constraintPts(req){ return req.constraintsOk ? 5 : 2; }

  function scoreRequest(req){
    var u=urgencyPts(req), w=weatherPts(req), c=cropStagePts(req), q=queueWaitPts(req), d=distancePts(req), r=constraintPts(req);
    var total = u+w+c+q+d+r;
    var hrs = Math.round((today().getTime()-new Date(req.submittedAt).getTime())/(60*60*1000));
    return {
      total: total,
      factors: [
        {label:'Urgency / deadline proximity', pts:u, max:25, note: daysUntil(req.end)+' day(s) until required end of window'},
        {label:'Weather risk exposure', pts:w, max:25, note: req.weatherRisk+' forecast risk to standing crop'},
        {label:'Crop readiness / stage', pts:c, max:20, note: req.cropStage+' stage'},
        {label:'Queue waiting time', pts:q, max:15, note: hrs+' hr(s) since request was submitted'},
        {label:'Distance & logistics', pts:d, max:10, note: (FG_RESOURCES.filter(function(r){return r.id===req.resourceId;})[0]||{}).distanceKm+' km transit to farm'},
        {label:'Resource constraints match', pts:r, max:5, note: req.constraintsOk ? 'Attachments/operator confirmed compatible' : 'Partial match — needs adapter/operator check'}
      ]
    };
  }
  window.FG_score = scoreRequest;

  function scoreTier(total){ if(total>=70) return 'high'; if(total>=45) return 'med'; return 'low'; }
  window.FG_scoreTier = scoreTier;

  function bufferMins(distanceKm){ return Math.round(distanceKm*3)+15; }

  /* ---------------- Conflict detection: same resource + overlapping
     date window ---------------------------------------------------- */
  function overlaps(a,b){ return a.start<=b.end && b.start<=a.end; }
  function conflictsFor(resourceId){
    return FG_REQUESTS.filter(function(r){ return r.resourceId===resourceId && r.status!=='reassigned' && r.status!=='cancelled'; });
  }
  function groupByResource(){
    var groups = {};
    FG_REQUESTS.forEach(function(req){
      if(req.status==='cancelled') return;
      (groups[req.resourceId] = groups[req.resourceId] || []).push(req);
    });
    return groups;
  }
  window.FG_groupByResource = groupByResource;

  function hasOverlapConflict(resourceId, group){
    var list = group || conflictsFor(resourceId);
    for(var i=0;i<list.length;i++){
      for(var j=i+1;j<list.length;j++){
        if(overlaps(list[i], list[j])) return true;
      }
    }
    return false;
  }
  window.FG_hasOverlapConflict = hasOverlapConflict;

  /* ---------------- Resolve a resource's queue: highest score wins the
     slot; others queued or flagged for reallocation ------------------ */
  function resolveResource(resourceId){
    var group = (groupByResource()[resourceId] || []).slice();
    if(!group.length) return [];
    group.forEach(function(r){ r._score = scoreRequest(r); });
    group.sort(function(a,b){ return b._score.total - a._score.total; });
    var res = FG_RESOURCES.filter(function(r){return r.id===resourceId;})[0];
    group.forEach(function(r, idx){
      if(res.status==='breakdown'){ r.status='disrupted'; return; }
      if(idx===0){ r.status='assigned'; }
      else if(overlaps(r, group[0])){ r.status='queued'; }
      else { r.status='assigned'; } // no actual date overlap, can proceed independently
    });
    return group;
  }
  window.FG_resolveResource = resolveResource;

  function resolveAll(){
    Object.keys(groupByResource()).forEach(function(rid){ resolveResource(rid); });
  }
  window.FG_resolveAll = resolveAll;
  resolveAll();

  /* ---------------- Disruption + reallocation -------------------- */
  function logActivity(msg){
    window.FG_ACTIVITY.unshift({msg:msg, at:new Date(today().getTime())});
  }
  window.FG_logActivity = logActivity;

  function simulateDisruption(resourceId){
    var res = FG_RESOURCES.filter(function(r){return r.id===resourceId;})[0];
    if(!res) return;
    res.status = 'breakdown';
    var affected = (groupByResource()[resourceId]||[]).slice();
    affected.forEach(function(r){ r._score = scoreRequest(r); });
    affected.sort(function(a,b){ return b._score.total - a._score.total; });

    var alt = FG_RESOURCES.filter(function(r){ return r.category===res.category && r.id!==res.id && r.status==='ok'; })[0];

    logActivity('⚠ Breakdown reported on <b>'+res.name+'</b>. Recalculating '+affected.length+' affected request(s).');

    if(alt && affected[0]){
      var top = affected[0];
      top.resourceId = alt.id;
      top.status = 'assigned';
      logActivity('Reassigned <b>'+top.farmer+'</b> (highest priority, score '+top._score.total+'/100) to <b>'+alt.name+'</b> — '+bufferMins(alt.distanceKm)+' min transit buffer applied. Original slot on '+res.name+' released.');
      affected.slice(1).forEach(function(r){
        r.status = 'queued';
        logActivity('<b>'+r.farmer+'</b> (score '+scoreRequest(r).total+'/100) moved to queue — will be offered '+res.name+' once maintenance clears, or next available unit.');
      });
    } else if(affected[0]) {
      affected.forEach(function(r){ r.status='queued'; });
      logActivity('No alternate unit of category "'+res.category+'" is currently free — all '+affected.length+' request(s) held in priority queue until '+res.name+' is back in service.');
    } else {
      logActivity('No pending requests were affected by this breakdown.');
    }
    resolveAll();
  }
  window.FG_simulateDisruption = simulateDisruption;

  function triggerRainAlert(){
    var bumped = 0;
    FG_REQUESTS.forEach(function(r){
      if((r.status==='pending' || r.status==='queued' || r.status==='assigned') && r.weatherRisk!=='high'){
        r.weatherRisk = 'high'; bumped++;
      }
    });
    resolveAll();
    logActivity('🌧 Rain alert issued for the district. Weather-risk factor recalculated upward for '+bumped+' open request(s); schedules re-ranked accordingly.');
  }
  window.FG_triggerRainAlert = triggerRainAlert;

  /* ---------------- Submitting a new request (+ offline queue) ---- */
  function submitRequest(data){
    qCounter++;
    var req = {
      id:'Q'+qCounter, farmer:data.farmer||'You', resourceId:data.resourceId,
      start:data.start, end:data.end, durationHrs:Number(data.durationHrs)||4,
      cropStage:data.cropStage, urgency:data.urgency||'', submittedAt:new Date(today().getTime()),
      weatherRisk:data.weatherRisk||'medium', constraintsOk: data.constraintsOk!==false, status:'pending'
    };
    if(window.FG_OFFLINE){
      window.FG_OFFLINE_QUEUE.push(req);
      return {queued:true, req:req};
    }
    FG_REQUESTS.push(req);
    resolveResource(req.resourceId);
    var conflict = hasOverlapConflict(req.resourceId);
    logActivity('New request from <b>'+req.farmer+'</b> for '+(FG_RESOURCES.filter(function(r){return r.id===req.resourceId;})[0]||{}).name+' — scored '+scoreRequest(req).total+'/100.'+(conflict?' Overlaps with existing requests on this unit.':''));
    return {queued:false, req:req, conflict:conflict};
  }
  window.FG_submitRequest = submitRequest;

  function syncOfflineQueue(){
    var n = window.FG_OFFLINE_QUEUE.length;
    window.FG_OFFLINE_QUEUE.forEach(function(req){
      FG_REQUESTS.push(req);
      resolveResource(req.resourceId);
    });
    window.FG_OFFLINE_QUEUE = [];
    if(n>0) logActivity('Back online — synced '+n+' locally-queued request(s) with the coordination engine.');
    return n;
  }
  window.FG_syncOfflineQueue = syncOfflineQueue;

})();
