import json
from pathlib import Path
from typing import List, Optional

from ..config import EnforcementConfig
from ..detection.hotspot import HotspotResult
from ..attribution.source_matcher import AttributionResult
from ..enforcement.recommender import EnforcementRecommendation
from ..data.geo_utils import GeoUtils

cfg = EnforcementConfig()

SEVERITY_COLORS = {
    "Very High": "#ef4444",
    "High": "#f97316",
    "Moderate": "#eab308",
    "Low": "#22c55e",
}
SEVERITY_COLORS_HTML = {
    "Very High": "255, 68, 68",
    "High": "249, 115, 22",
    "Moderate": "234, 179, 8",
    "Low": "34, 197, 94",
}


class IndiaMapGenerator:
    @staticmethod
    def generate_map(
        hotspots: List[HotspotResult],
        attributions: List[AttributionResult],
        recommendations: List[EnforcementRecommendation],
        save_path: Optional[Path] = None,
    ) -> str:
        geojson = GeoUtils.generate_india_geojson()
        geojson_str = json.dumps(geojson)

        hotspot_markers = []
        for i, hs in enumerate(hotspots):
            attr = next((a for a in attributions if a.hotspot_id == hs.id), None)
            rec = next((r for r in recommendations if r.hotspot_id == hs.id), None)
            cause = attr.most_probable_cause.replace("_", " ").title() if attr else "Unknown"
            conf = f"{attr.confidence * 100:.1f}%" if attr else "N/A"
            color = SEVERITY_COLORS_HTML.get(hs.severity_label, "100, 100, 100")
            pop_exposed = rec.population_exposed if rec else 0
            rec_text = rec.recommendation if rec else "Investigate"
            authority = rec.responsible_authority if rec else "CPCB"
            alternatives = ""
            if attr:
                alt = dict(sorted(attr.alternative_causes.items(), key=lambda x: x[1], reverse=True)[:3])
                alternatives = "<br>".join([f"&nbsp;&nbsp;{k.replace('_',' ').title()}: {v:.1f}%" for k, v in alt.items()])
            evidence = "<br>".join(attr.supporting_evidence[:4]) if attr else "N/A"

            marker = {
                "lat": hs.lat, "lon": hs.lon,
                "name": hs.location_name,
                "state": hs.state,
                "severity": hs.severity_label,
                "severity_score": f"{hs.severity_score:.2f}",
                "color": color,
                "size": max(12, hs.severity_score * 30),
                "cause": cause,
                "confidence": conf,
                "dominant_pollutant": hs.dominant_pollutant,
                "aqi": hs.aqi_data.get("aqi", "N/A"),
                "pm25": f"{hs.aqi_data.get('pm25', 'N/A')}",
                "population": f"{pop_exposed:,}",
                "recommendation": rec_text,
                "authority": authority,
                "evidence": evidence,
                "alternatives": alternatives,
            }
            hotspot_markers.append(marker)

        markers_json = json.dumps(hotspot_markers)
        now = __import__("datetime").datetime.now().strftime("%B %d, %Y %H:%M")

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Vayu-Drishti — Enforcement Intelligence Dashboard</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; background: #050510; color: #e0e0e0; overflow: hidden; }}
  #app {{ display: flex; height: 100vh; }}
  #map {{ flex: 1; height: 100vh; background: #050510; }}
  #panel {{ width: 420px; background: #0a0a1a; border-left: 1px solid #1a1a3a; overflow-y: auto; padding: 0; display: flex; flex-direction: column; }}
  .panel-header {{ background: linear-gradient(135deg, #0f0f2a, #1a0a2e); padding: 20px 24px; border-bottom: 1px solid #1a1a3a; }}
  .panel-header h1 {{ font-size: 18px; font-weight: 700; color: #fff; letter-spacing: 0.5px; }}
  .panel-header h1 span {{ color: #3b82f6; }}
  .panel-header .subtitle {{ font-size: 11px; color: #6b7280; margin-top: 4px; }}
  .panel-stats {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; padding: 16px 24px; background: #0d0d20; border-bottom: 1px solid #1a1a3a; }}
  .stat-card {{ background: #111128; border-radius: 8px; padding: 12px; border: 1px solid #1a1a3a; }}
  .stat-card .value {{ font-size: 24px; font-weight: 700; color: #fff; }}
  .stat-card .label {{ font-size: 10px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 2px; }}
  .stat-card .value.red {{ color: #ef4444; }}
  .stat-card .value.orange {{ color: #f97316; }}
  .stat-card .value.yellow {{ color: #eab308; }}
  .stat-card .value.green {{ color: #22c55e; }}
  .panel-section {{ padding: 16px 24px; border-bottom: 1px solid #1a1a3a; }}
  .panel-section h3 {{ font-size: 12px; color: #6b7280; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px; }}
  .hotspot-list {{ padding: 0; }}
  .hotspot-item {{ display: flex; align-items: center; gap: 12px; padding: 10px 24px; cursor: pointer; border-left: 3px solid transparent; transition: all 0.2s; }}
  .hotspot-item:hover {{ background: #111128; }}
  .hotspot-item.active {{ background: #111128; border-left-color: #3b82f6; }}
  .hotspot-marker-dot {{ width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }}
  .hotspot-info {{ flex: 1; min-width: 0; }}
  .hotspot-info .name {{ font-size: 13px; font-weight: 600; color: #fff; }}
  .hotspot-info .detail {{ font-size: 10px; color: #6b7280; }}
  .hotspot-info .cause {{ font-size: 10px; color: #3b82f6; }}
  .hotspot-priority {{ font-size: 11px; font-weight: 700; color: #6b7280; width: 24px; text-align: center; }}
  .detail-panel {{ padding: 20px 24px; flex: 1; overflow-y: auto; display: none; }}
  .detail-panel.show {{ display: block; }}
  .detail-panel h2 {{ font-size: 16px; font-weight: 700; color: #fff; margin-bottom: 4px; }}
  .detail-panel .location-sub {{ font-size: 12px; color: #6b7280; margin-bottom: 16px; }}
  .detail-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 16px; }}
  .detail-item {{ background: #111128; border-radius: 8px; padding: 12px; border: 1px solid #1a1a3a; }}
  .detail-item .lbl {{ font-size: 9px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px; }}
  .detail-item .val {{ font-size: 14px; font-weight: 600; color: #fff; margin-top: 2px; }}
  .detail-item .val.conf {{ color: #3b82f6; }}
  .evidence-box {{ background: #111128; border-radius: 8px; padding: 12px; border: 1px solid #1a1a3a; margin-bottom: 12px; }}
  .evidence-box .title {{ font-size: 10px; color: #6b7280; text-transform: uppercase; margin-bottom: 6px; }}
  .evidence-box ul {{ list-style: none; padding: 0; }}
  .evidence-box li {{ font-size: 11px; color: #c0c0c0; padding: 3px 0; padding-left: 12px; position: relative; }}
  .evidence-box li::before {{ content: "›"; position: absolute; left: 0; color: #3b82f6; font-weight: bold; }}
  .alternatives-box {{ margin-top: 8px; }}
  .alt-bar {{ display: flex; align-items: center; gap: 8px; margin: 4px 0; }}
  .alt-bar .alt-label {{ font-size: 10px; color: #a0a0a0; width: 80px; }}
  .alt-bar .alt-track {{ flex: 1; height: 6px; background: #1a1a3a; border-radius: 3px; overflow: hidden; }}
  .alt-bar .alt-fill {{ height: 100%; border-radius: 3px; background: #3b82f6; }}
  .alt-bar .alt-pct {{ font-size: 10px; color: #6b7280; width: 40px; text-align: right; }}
  .rec-box {{ background: linear-gradient(135deg, #0f1a3a, #1a0a2e); border-radius: 8px; padding: 12px; border: 1px solid #1a3a5a; margin-top: 12px; }}
  .rec-box .rec-title {{ font-size: 10px; color: #3b82f6; text-transform: uppercase; margin-bottom: 4px; }}
  .rec-box .rec-text {{ font-size: 12px; color: #c0d0f0; }}
  .rec-box .rec-auth {{ font-size: 10px; color: #6b7280; margin-top: 4px; }}
  .leaflet-container {{ background: #050510 !important; }}
  .leaflet-control-attribution {{ display: none !important; }}
  .leaflet-popup-content-wrapper {{ background: #111128 !important; color: #e0e0e0 !important; border: 1px solid #1a1a3a !important; border-radius: 8px !important; }}
  .leaflet-popup-tip {{ background: #111128 !important; border: 1px solid #1a1a3a !important; }}
  .leaflet-popup-close-button {{ color: #6b7280 !important; }}
  ::-webkit-scrollbar {{ width: 4px; }} ::-webkit-scrollbar-track {{ background: #0a0a1a; }} ::-webkit-scrollbar-thumb {{ background: #1a1a3a; border-radius: 2px; }}
  .glow-pulse {{ animation: pulse 2s infinite; }}
  @@keyframes pulse {{ 0% {{ opacity: 0.6; }} 50% {{ opacity: 1; }} 100% {{ opacity: 0.6; }} }}
  .severity-badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 9px; font-weight: 600; text-transform: uppercase; }}
  .severity-badge.vh {{ background: rgba(239,68,68,0.2); color: #ef4444; border: 1px solid rgba(239,68,68,0.3); }}
  .severity-badge.h {{ background: rgba(249,115,22,0.2); color: #f97316; border: 1px solid rgba(249,115,22,0.3); }}
  .severity-badge.m {{ background: rgba(234,179,8,0.2); color: #eab308; border: 1px solid rgba(234,179,8,0.3); }}
  .severity-badge.l {{ background: rgba(34,197,94,0.2); color: #22c55e; border: 1px solid rgba(34,197,94,0.3); }}
</style>
</head>
<body>
<div id="app">
  <div id="map"></div>
  <div id="panel">
    <div class="panel-header">
      <h1>VAYU-DRISHTI <span>Enforcement Intelligence</span></h1>
      <div class="subtitle">Real-time pollution hotspot detection & prioritisation | {now}</div>
    </div>
    <div class="panel-stats" id="statsPanel">
      <div class="stat-card"><div class="value red" id="totalCount">0</div><div class="label">Total Hotspots</div></div>
      <div class="stat-card"><div class="value orange" id="criticalCount">0</div><div class="label">Critical (Top 5)</div></div>
      <div class="stat-card"><div class="value yellow" id="highCount">0</div><div class="label">High Priority (6-15)</div></div>
      <div class="stat-card"><div class="value green" id="lowCount">0</div><div class="label">Monitoring</div></div>
    </div>
    <div class="panel-section" style="padding: 8px 0 0 0; flex: 1; display: flex; flex-direction: column;">
      <div style="padding: 8px 24px 4px;"><h3>Prioritised Hotspots</h3></div>
      <div class="hotspot-list" id="hotspotList"></div>
    </div>
    <div class="detail-panel" id="detailPanel">
      <h2 id="detailName">Select a hotspot</h2>
      <div class="location-sub" id="detailLocation">Click on a map marker or hotspot in the list</div>
      <div class="detail-grid">
        <div class="detail-item"><div class="lbl">Severity</div><div class="val" id="detailSeverity">—</div></div>
        <div class="detail-item"><div class="lbl">Confidence</div><div class="val conf" id="detailConfidence">—</div></div>
        <div class="detail-item"><div class="lbl">Dominant Pollutant</div><div class="val" id="detailPollutant">—</div></div>
        <div class="detail-item"><div class="lbl">AQI / PM2.5</div><div class="val" id="detailAQI">—</div></div>
        <div class="detail-item"><div class="lbl">Population Exposed</div><div class="val" id="detailPopulation">—</div></div>
        <div class="detail-item"><div class="lbl">Source</div><div class="val" id="detailCause">—</div></div>
      </div>
      <div class="evidence-box"><div class="title">Supporting Evidence</div><ul id="detailEvidence"></ul></div>
      <div class="evidence-box"><div class="title">Alternative Sources</div><div id="detailAlternatives"></div></div>
      <div class="rec-box">
        <div class="rec-title">Recommended Action</div>
        <div class="rec-text" id="detailRecommendation">—</div>
        <div class="rec-auth" id="detailAuthority">—</div>
      </div>
    </div>
  </div>
</div>
<script>
const hotspots = {markers_json};
const geojsonData = {geojson_str};

const map = L.map('map', {{
    center: [22.5, 80.0],
    zoom: 5,
    zoomControl: true,
    attributionControl: false,
}});

L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
    maxZoom: 19,
}}).addTo(map);

L.geoJSON(geojsonData, {{
    style: {{
        color: '#1a1a3a',
        weight: 1.2,
        fillColor: '#0a0a1a',
        fillOpacity: 0.3,
    }},
}}).addTo(map);

function severityColor(sev) {{
    return {{'Very High': '#ef4444', 'High': '#f97316', 'Moderate': '#eab308', 'Low': '#22c55e'}}[sev] || '#6366f1';
}}
function severityBadge(sev) {{
    const cls = {{'Very High': 'vh', 'High': 'h', 'Moderate': 'm', 'Low': 'l'}}[sev] || 'l';
    return `<span class="severity-badge ${{cls}}">${{sev}}</span>`;
}}

let markers = [];
let selectedIdx = -1;

function flyTo(idx) {{
    const h = hotspots[idx];
    if (!h) return;
    map.flyTo([h.lat, h.lon], 8, {{duration: 0.8}});
    selectHotspot(idx);
}}

function selectHotspot(idx) {{
    selectedIdx = idx;
    const h = hotspots[idx];
    document.querySelectorAll('.hotspot-item').forEach((el, i) => {{
        el.classList.toggle('active', i === idx);
    }});
    const dp = document.getElementById('detailPanel');
    dp.classList.add('show');
    document.getElementById('detailName').textContent = h.name;
    document.getElementById('detailLocation').textContent = `${{h.state}} | ${{h.lat.toFixed(4)}}°N, ${{h.lon.toFixed(4)}}°E`;
    document.getElementById('detailSeverity').innerHTML = severityBadge(h.severity);
    document.getElementById('detailConfidence').textContent = h.confidence;
    document.getElementById('detailPollutant').textContent = h.dominant_pollutant;
    document.getElementById('detailAQI').textContent = `AQI ${{h.aqi}} | PM2.5 ${{h.pm25}}`;
    document.getElementById('detailPopulation').textContent = h.population;
    document.getElementById('detailCause').textContent = h.cause;
    document.getElementById('detailRecommendation').textContent = h.recommendation;
    document.getElementById('detailAuthority').textContent = `Responsible: ${{h.authority}}`;
    const evList = document.getElementById('detailEvidence');
    evList.innerHTML = h.evidence.split('<br>').map(e => `<li>${{e}}</li>`).join('');
    const altDiv = document.getElementById('detailAlternatives');
    altDiv.innerHTML = h.alternatives ? h.alternatives.split('<br>').map(line => {{
        const parts = line.replace(/&nbsp;/g,'').trim().split(':');
        if (parts.length === 2) {{
            const name = parts[0].trim();
            const pct = parseFloat(parts[1]);
            return `<div class="alt-bar"><span class="alt-label">${{name}}</span><div class="alt-track"><div class="alt-fill" style="width:${{pct}}%"></div></div><span class="alt-pct">${{pct}}%</span></div>`;
        }}
        return '';
    }}).join('') : '<div style="font-size:11px;color:#6b7280">No alternative sources identified</div>';
}}

hotspots.forEach((h, i) => {{
    const size = Math.max(10, Math.min(h.size, 40));
    const color = severityColor(h.severity);
    const marker = L.circleMarker([h.lat, h.lon], {{
        radius: size,
        fillColor: color,
        color: color,
        weight: 2,
        opacity: 0.8,
        fillOpacity: 0.3,
    }}).addTo(map);
    marker.on('click', () => flyTo(i));
    markers.push(marker);
}});

const listEl = document.getElementById('hotspotList');
hotspots.forEach((h, i) => {{
    const div = document.createElement('div');
    div.className = 'hotspot-item';
    div.innerHTML = `
      <div class="hotspot-priority">#${{i + 1}}</div>
      <div class="hotspot-marker-dot" style="background:${{severityColor(h.severity)}}"></div>
      <div class="hotspot-info">
        <div class="name">${{h.name}}</div>
        <div class="detail">${{h.state}} | AQI ${{h.aqi}} | ${{h.severity}}</div>
        <div class="cause">${{h.cause}} (${{h.confidence}})</div>
      </div>
    `;
    div.addEventListener('click', () => flyTo(i));
    listEl.appendChild(div);
}});

document.getElementById('totalCount').textContent = hotspots.length;
document.getElementById('criticalCount').textContent = Math.min(5, hotspots.length);
document.getElementById('highCount').textContent = Math.max(0, Math.min(10, hotspots.length - 5));
document.getElementById('lowCount').textContent = Math.max(0, hotspots.length - 15);

if (hotspots.length > 0) flyTo(0);
</script>
</body>
</html>"""
        if save_path:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_text(html, encoding="utf-8")
        return html
