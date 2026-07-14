'use client';

import { AsyncPanel } from '../components/AsyncPanel';
import { Metric } from '../components/Metric';

type Dashboard = {
  organization: { name: string };
  facilities: number;
  assets: number;
  active_missions: number;
  critical_findings: number;
  coverage_percent: number;
  work_order_backlog: number;
  device_status: { name: string; status: string; software_version: string }[];
  model_status: { name: string; version: string; status: string }[];
  risk_trend: number[];
};

const fallback: Dashboard = {
  organization: { name: 'OpenInspect Demo Organization' }, facilities: 2, assets: 4, active_missions: 2,
  critical_findings: 0, coverage_percent: 91.7, work_order_backlog: 1,
  device_status: [{ name: 'Edge Node A-17', status: 'online', software_version: '0.1.0' }],
  model_status: [
    { name: 'Structural Classical CV', version: '0.1.0', status: 'candidate' },
    { name: 'Underwater Pipeline CV', version: '0.1.0', status: 'candidate' },
  ],
  risk_trend: [42, 40, 38, 35, 33, 31],
};

export default function Home() {
  return (
    <AsyncPanel<Dashboard> path="/dashboard" fallback={fallback}>
      {(d) => <div className="workspace">
        <section className="hero-strip">
          <div>
            <span className="kicker">{d.organization.name}</span>
            <h2>Inspection evidence, coverage and maintenance decisions in one controlled chain.</h2>
            <p>Structural surfaces, underwater pipelines, sonar-linked missions and offline edge devices.</p>
          </div>
          <div className="instrument"><span>RISK INDEX</span><strong>{d.risk_trend.at(-1)}</strong><small>↓ 11 points</small></div>
        </section>
        <section className="metric-grid">
          <Metric label="Facilities" value={d.facilities} note="multi-site registry" />
          <Metric label="Assets" value={d.assets} note="hierarchical components" />
          <Metric label="Active missions" value={d.active_missions} note="planned + processed" />
          <Metric label="Critical findings" value={d.critical_findings} note="human review required" />
          <Metric label="Coverage" value={`${d.coverage_percent.toFixed(1)}%`} note="trajectory-linked" />
          <Metric label="Work backlog" value={d.work_order_backlog} note="open work orders" />
        </section>
        <section className="split-grid">
          <div className="panel">
            <div className="panel-head"><div><span className="eyebrow">MISSION CONTROL</span><h3>Facility integrity map</h3></div><span className="tag">2 sites</span></div>
            <div className="map-surface">
              <div className="route-line" />
              <div className="map-node node-a"><span>Ras Laffan Demo</span></div>
              <div className="map-node node-b"><span>Bridge Lab</span></div>
              <div className="coverage-band band-1" /><div className="coverage-band band-2" />
            </div>
          </div>
          <div className="panel">
            <div className="panel-head"><div><span className="eyebrow">SYSTEM HEALTH</span><h3>Models and edge devices</h3></div></div>
            <div className="list">
              {d.device_status.map((x) => <div className="list-row" key={x.name}><div><strong>{x.name}</strong><span>Edge / {x.software_version}</span></div><span className={`state ${x.status}`}>{x.status}</span></div>)}
              {d.model_status.map((x) => <div className="list-row" key={`${x.name}-${x.version}`}><div><strong>{x.name}</strong><span>Model / {x.version}</span></div><span className="state candidate">{x.status}</span></div>)}
            </div>
          </div>
        </section>
      </div>}
    </AsyncPanel>
  );
}
