---
title: "After Dark: A Year of Road Crashes, Mapped by Twilight Phase"
seo_title: "Road Crashes Are 1.6× Deadlier After Dark — Interactive Crash Map"
description: "An interactive map of 8,293 road crashes in 2024, each classified by the calculated position of the sun. Darkness is 31% of crashes but 42% of the deaths — a crash after dark is 1.6× more likely to be fatal."
tags:
  - transportation-safety
  - optimization
  - controls
  - dark-sky
date: 2026-07-13
cta: "take-action"
---

A road is not equally dangerous at every hour. The same intersection, the same speed limit, the same driver — the odds of a crash turning fatal climb as the sun goes down. Darkness is the one condition streetlights exist to erase, and it is the condition under which the road quietly gets deadlier.

Below is one country's entire year of reported crashes — 2024 — with every record placed on the map and colored by the calculated position of the sun at the moment it happened. Filter by twilight phase, by whether streetlights would have been operating, by severity, by month. The pattern is not subtle.

<link rel="stylesheet" href="/vendor/leaflet/leaflet.css">

<style>
.crashmap{position:relative;left:50%;transform:translateX(-50%);width:min(1080px,94vw);margin:2.5rem 0}
.crashmap .cm-frame{position:relative;isolation:isolate;z-index:0;height:min(640px,78vh);border-radius:12px;overflow:hidden;border:1px solid var(--border-dark);box-shadow:0 10px 40px rgba(0,0,0,.12)}
.crashmap .cm-map{position:absolute;inset:0;background:#e8eef3}
.crashmap .cm-panel{position:absolute;z-index:1000;top:12px;left:12px;width:min(300px,calc(100% - 24px));max-height:calc(100% - 24px);overflow:auto;background:rgba(255,255,255,.96);backdrop-filter:blur(4px);border-radius:10px;box-shadow:0 3px 16px rgba(0,0,0,.22);padding:14px;box-sizing:border-box;font-family:var(--font-body);color:#172033;font-size:13px;line-height:1.5}
.crashmap .cm-panel .cm-title{font-weight:600;font-size:15px;margin-bottom:4px;color:#172033}
.crashmap .cm-panel .cm-note{font-size:11.5px;line-height:1.45;background:#fff4ce;padding:8px;border-radius:6px;margin:8px 0;color:#5a4b1a}
.crashmap .cm-panel label{display:block;font-size:12.5px;font-weight:500;margin:8px 0 0;color:#172033}
.crashmap .cm-panel select{width:100%;padding:6px;margin-top:3px;font-size:13px;border:1px solid #cbd5e0;border-radius:6px;background:#fff;font-family:inherit;color:#172033}
.crashmap .cm-legend{margin-top:10px;font-size:12px;line-height:1.9}
.crashmap .cm-legend .cm-dot{width:10px;height:10px;border-radius:50%;display:inline-block;margin-right:6px;vertical-align:middle;border:1px solid rgba(0,0,0,.15)}
.crashmap .cm-count{font-weight:600;margin-top:10px;color:#172033}
.crashmap .cm-cap{font-size:.85rem;color:var(--text-subtle);margin:.75rem 4px 0;line-height:1.5}
.crashmap .leaflet-container{font-family:var(--font-body)}
.crashmap .leaflet-popup-content{font-size:12.5px;line-height:1.5}
@media(max-width:640px){.crashmap .cm-frame{height:72vh}.crashmap .cm-panel{width:calc(100% - 24px);max-height:44%}}
</style>

<div class="crashmap"><div class="cm-frame"><div class="cm-map" id="cm-map"></div><div class="cm-panel"><div class="cm-title">Explore the year</div><div class="cm-note"><strong>Approximation:</strong> the public file omits the day of month, so every record uses the 15th of its reported month and the midpoint of its 15-minute time bin. March and October (daylight-saving transitions) carry extra timing uncertainty.</div><label>Twilight phase<select id="cm-phase"><option value="All">All phases</option></select></label><label>Calculated streetlight status<select id="cm-slstatus"><option value="All">All</option><option value="ON">On — dark hours</option><option value="OFF">Off — day / early twilight</option></select></label><label>Severity<select id="cm-severity"><option value="All">All severities</option><option value="Fatal">Fatal</option><option value="Serious">Serious</option><option value="Minor">Minor</option></select></label><label>Crash type<select id="cm-atype"><option value="All">All types</option></select></label><label>Month<select id="cm-month"><option value="All">All months</option></select></label><div class="cm-legend"><div><i class="cm-dot" style="background:#f4d03f"></i>Daylight</div><div><i class="cm-dot" style="background:#f39c12"></i>Civil twilight</div><div><i class="cm-dot" style="background:#9b59b6"></i>Nautical twilight</div><div><i class="cm-dot" style="background:#34495e"></i>Astronomical twilight</div><div><i class="cm-dot" style="background:#111827"></i>Night</div></div><div class="cm-count" id="cm-count">Loading…</div></div></div><p class="cm-cap">8,293 reported crashes, one country, calendar year 2024. Each dot is one crash, colored by the calculated position of the sun. Drag to pan, use the +/− buttons or double-click to zoom, and click any dot for detail.</p></div>

<script src="/vendor/leaflet/leaflet.js"></script>
<script>
(function(){
  var el=document.getElementById('cm-map');
  if(!el||!window.L)return;
  var MONTHS=['','January','February','March','April','May','June','July','August','September','October','November','December'];
  var colors={'Daylight':'#f4d03f','Civil twilight':'#f39c12','Nautical twilight':'#9b59b6','Astronomical twilight':'#34495e','Night':'#111827'};
  var map=L.map(el,{preferCanvas:true,scrollWheelZoom:false}).setView([31.6,34.9],8);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'&copy; OpenStreetMap contributors'}).addTo(map);
  var renderer=L.canvas({padding:.5});
  var data=[],layer=L.layerGroup().addTo(map);
  var count=document.getElementById('cm-count');
  function v(id){return document.getElementById(id).value;}
  function fill(id,vals){var e=document.getElementById(id);Array.from(new Set(vals)).sort(function(a,b){return String(a).localeCompare(String(b),undefined,{numeric:true});}).forEach(function(x){var o=document.createElement('option');o.value=x;o.textContent=x;e.appendChild(o);});}
  function fillMonths(id,vals){var e=document.getElementById(id);Array.from(new Set(vals)).sort(function(a,b){return a-b;}).forEach(function(x){var o=document.createElement('option');o.value=x;o.textContent=MONTHS[x]||x;e.appendChild(o);});}
  function render(){
    layer.clearLayers();
    var p=v('cm-phase'),sl=v('cm-slstatus'),s=v('cm-severity'),a=v('cm-atype'),m=v('cm-month');
    var f=data.filter(function(d){return (p==='All'||d.twilight_phase===p)&&(sl==='All'||d.calculated_streetlight_status===sl)&&(s==='All'||d.severity===s)&&(a==='All'||d.accident_type===a)&&(m==='All'||String(d.month)===m);});
    f.forEach(function(d){
      var mk=L.circleMarker([d.lat,d.lon],{renderer:renderer,radius:d.severity==='Fatal'?5:d.severity==='Serious'?4:2.6,color:colors[d.twilight_phase]||'#888',weight:1,fillOpacity:.7});
      mk.bindPopup('<strong>'+d.severity+' crash</strong><br>Calculated phase: '+d.twilight_phase+'<br>Streetlights: <strong>'+d.calculated_streetlight_status+'</strong><br>Solar elevation: '+d.solar_elevation_deg+'&deg;<br>Approx. time: 2024-'+String(d.month).padStart(2,'0')+'-15 '+d.assumed_local_time+(d.dst_transition_month?'<br><strong>DST transition month</strong>':'')+'<br>Type: '+d.accident_type+'<br>Police-reported lighting: '+d.lighting_police);
      mk.addTo(layer);
    });
    count.textContent=f.length.toLocaleString()+' crashes shown';
  }
  count.textContent='Loading crash data…';
  fetch('/data/israel-crashes-2024.json').then(function(r){return r.json();}).then(function(d){
    data=d;
    fill('cm-phase',data.map(function(x){return x.twilight_phase;}));
    fill('cm-atype',data.map(function(x){return x.accident_type;}));
    fillMonths('cm-month',data.map(function(x){return x.month;}));
    ['cm-phase','cm-slstatus','cm-severity','cm-atype','cm-month'].forEach(function(id){document.getElementById(id).addEventListener('change',render);});
    render();
  }).catch(function(){count.textContent='Could not load crash data.';});
})();
</script>

## What you're looking at

Every reported crash in the dataset carries a location and a time. From those, the sun's elevation at the moment of each crash was calculated independently — no reliance on the officer's lighting judgment — and each record was sorted into daylight, one of three twilight bands, or full night. A streetlight is treated as operating whenever the sun sits more than six degrees below the horizon, the standard civil-twilight threshold at which roadway lighting is expected to be on.

The split is stark. Crashes during those dark, streetlights-operating hours make up **30.7% of all crashes but 41.6% of the fatal ones**. Put plainly: a crash in the dataset is **1.6× more likely to be fatal after dark** — a 6.5% fatality rate during streetlight hours versus 4.1% during daylight and early twilight.

And the deadliest slice is not the dead of night. It is the transition. Fatality rate peaks in the twilight bands — the dusk-and-dawn handoff when eyes are still adapting, when glare is worst, and when lighting is ramping between "off" and "doing the whole job." It is the same signature our [transportation-safety analysis](/insights/transportation-safety/) found in U.S. federal crash data: fatal crashes spike at the darkness transition, the exact window a lighting system is supposed to own.

## Read the caveats first

This is honest, imperfect data, and the honesty matters more than the decimals. The public file omits the day of the month, so every record is assumed to fall on the 15th; times arrive in 15-minute bins, so the midpoint of each bin is used; March and October straddle daylight-saving changes and carry extra uncertainty. Police-reported lighting fields were kept for comparison only and were never used to classify phase. This is one year, one country, and a correlation — not a controlled experiment.

But notice what the approximations can and cannot do. Assuming the 15th instead of the 9th, or the midpoint of a quarter-hour instead of the exact minute, blurs whether a borderline crash lands in civil versus nautical twilight. It does not move a noon crash to midnight. The direction of the pattern is robust even when the individual pins are fuzzy. Treat the map as a strong signal and the third decimal place as indicative.

## The one variable a city can switch

Of every factor stacked into a fatal night crash — speed, alcohol, fatigue, road geometry, a pedestrian in dark clothing — darkness is the only one a community can flip a switch on. Cities installed streetlights for exactly this reason: to buy back the visibility the sunset took away.

Yet in almost every city, those lights are static. They are designed once, at installation, to a single worst-case assumption, and then run flat every night — the same output at 2 a.m. on an empty residential street as at the 6 p.m. rush on a crowded arterial, indifferent to the hours and the locations where this map shows the risk actually concentrating. The infrastructure meant to erase the darkness penalty is set-and-forget, while the penalty itself moves by the hour and by the block.

That gap is the whole opportunity. A lighting system that knows where and when the road turns deadly can put light where it earns its keep — [adapting each luminaire](/insights/adaptive-street-lighting/) to the real geometry of risk instead of a flat nightly guess. The map above is a picture of a system quietly deciding outcomes it was never tuned to influence. Right light, right place, right time is how you tune it.

---

<div class="footnotes">

1. <span id="fn1"></span>Road-crash records: one country (Israel), calendar year 2024, public-use casualty-crash microdata — original coordinates in the Israeli Transverse Mercator grid (EPSG:2039), time recorded as quarter-hour codes. Coordinates were reprojected to WGS 84; twilight phase and solar elevation were computed independently from location and approximate local time (Asia/Jerusalem). Day-of-month and sub-15-minute timing were not present in the file and were approximated as described above. Police-reported lighting fields were retained for comparison only and were not used to classify phase. 8,293 records mapped. <a href="#fnref1">↩︎</a>

</div>
