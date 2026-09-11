/* =======================================================================
   Nutrition & Protection advisors
   - Soil-quality based fertilizer recommender
   - Weather + crop-age based pesticide recommender
   Weather values are auto-filled from fetchWeather(), a stand-in for a
   real backend call to the Google Weather API (kept server-side so the
   API key is never exposed to the browser). Swap the mock body below
   for a fetch('/api/weather?lat=..&lon=..') call once that backend
   endpoint exists.
   ======================================================================= */

function fetchWeather(cb){
  // TODO(backend): replace with a real call, e.g.
  //   fetch('/api/weather?lat='+lat+'&lon='+lon).then(r=>r.json()).then(cb)
  // which your server resolves via the Google Weather API using a
  // server-side API key. Mocked here with plausible Shivamogga-district
  // values for demo purposes.
  setTimeout(function(){
    cb({
      temp: Math.round(24 + Math.random()*10),      // °C
      humidity: Math.round(50 + Math.random()*35),   // %
      rainfallMm: Math.round(Math.random()*Math.random()*60) // mm, next 24h
    });
  }, 850);
}

/* ---------------- Fertilizer recommender (soil colour + crop + stage) */
function recommendFertilizer(input){
  var soil = input.soilColour, age = Number(input.cropAge), temp = Number(input.temperature);
  var reasons = [];
  var product, dosage;

  if(age <= 20){
    product = 'Urea + DAP starter dose';
    dosage = 'Split N: 1/3 basal + rest top-dressed over next 3 weeks';
    reasons.push('Crop is in an early/vegetative stage (' + age + ' days) — needs a nitrogen push to build canopy.');
  } else if(age <= 50){
    product = 'NPK 19:19:19 (balanced feed)';
    dosage = 'One balanced dose now, re-check at flowering';
    reasons.push('Crop is entering the flowering stage (' + age + ' days) — a balanced N-P-K feed supports bud and flower set.');
  } else {
    product = 'DAP + Potash top-up';
    dosage = 'Reduce nitrogen, favour potash for grain/fruit fill';
    reasons.push('Crop is past 50 days — nitrogen should taper off while potash supports grain/fruit fill.');
  }

  if(soil==='Red' || soil==='Laterite'){
    reasons.push(soil+' soils are typically low in phosphorus and micronutrients — adding Zinc Sulphate alongside is worth it.');
    dosage += ' + Zinc Sulphate micronutrient pack';
  } else if(soil==='Sandy'){
    reasons.push('Sandy soil drains fast and nutrients leach quickly — split the dose into smaller, more frequent applications and mix in Vermicompost to hold moisture and nutrients.');
    dosage += ' + Vermicompost as an organic base';
  } else if(soil==='Black'){
    reasons.push('Black (regur) soil retains moisture and potash well already — you can trim the potash portion slightly.');
  } else if(soil==='Alluvial'){
    reasons.push('Alluvial soil is naturally fertile and balanced — the standard dose should perform well without extra correction.');
  }

  if(temp>=33){
    reasons.push('Current temperature is high ('+temp+'°C) — apply in the cooler part of the day and irrigate lightly right after to avoid root burn.');
  }

  return {product: product, dosage: dosage, reasons: reasons};
}

/* ---------------- Pesticide recommender (temp, rain, humidity, crop age) */
function recommendPesticide(input){
  var temp=Number(input.temperature), rain=Number(input.rainfallMm), humidity=Number(input.humidity), age=Number(input.cropAge);
  var reasons = [];
  var product;

  var fungalRisk = humidity>=75 && temp>=20 && temp<=30;
  var suckingPestRisk = temp>=30 && rain<10;
  var heavyRainSoon = rain>=40;
  var tenderCrop = age<15;

  if(heavyRainSoon){
    product = 'Hold spray — if urgent, use Neem-based Bio Pesticide (rain-tolerant, low wash-off risk)';
    reasons.push('Heavy rain expected (~'+rain+'mm) — most chemical sprays wash off before absorption. Better to wait for a dry window or use a rain-tolerant organic option.');
  } else if(tenderCrop){
    product = 'Neem-based Bio Pesticide';
    reasons.push('Crop is only '+age+' days old — young tissue is more sensitive to harsh chemical pesticides, so an organic option is safer.');
  } else if(fungalRisk){
    product = 'Mancozeb 75% WP (fungicide)';
    reasons.push('Humidity is high ('+humidity+'%) with a temperature range ('+temp+'°C) that favours fungal blight — a protective fungicide is the priority.');
  } else if(suckingPestRisk){
    product = 'Imidacloprid 17.8% SL';
    reasons.push('Hot ('+temp+'°C), dry conditions (~'+rain+'mm rain) typically drive up sucking-pest pressure (aphids, whitefly, jassids).');
  } else {
    product = 'Neem-based Bio Pesticide (preventive, broad-spectrum)';
    reasons.push('Conditions are moderate right now — a broad-spectrum organic preventive is enough; re-check after the next weather shift.');
  }

  if(humidity>=75 && !fungalRisk && !heavyRainSoon){
    reasons.push('Humidity is elevated ('+humidity+'%) — keep an eye on fungal symptoms even though it isn\'t the top driver today.');
  }

  return {product: product, reasons: reasons};
}
