'use client';

import { useEffect, useState } from 'react';
import { API_URL } from '../../lib/api';

type Finding = {
  id: string; finding_type: string; provenance: string; severity: string; confidence: number;
  status: string; measurement_json: Record<string, number|string>; notes: string; model_version: string;
};

const fallback: Finding[] = [{
  id: 'demo-finding', finding_type: 'concrete_crack', provenance: 'project_owned_demo', severity: 'moderate',
  confidence: .82, status: 'human_confirmed', measurement_json: {pixel_length: 212, mean_width_px: 3.8},
  notes: 'Project-owned demo finding for local screenshot and review workflow validation.', model_version: 'classical-cv-0.1',
}];

export default function Review() {
  const [items, setItems] = useState<Finding[]>(fallback);
  const [notice, setNotice] = useState('');
  const load = () => fetch(`${API_URL}/findings`).then(r => r.ok ? r.json() : Promise.reject(new Error(String(r.status)))).then(setItems).catch(() => setNotice('Using bundled project-owned demo state.'));
  useEffect(() => { void load(); }, []);
  const x = items[0];

  async function decide(decision: 'accept'|'reject'|'request_reinspection') {
    if (!x || x.id === 'offline') return;
    const response = await fetch(`${API_URL}/findings/${x.id}/reviews`, {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({decision, notes: `Decision recorded from evidence workspace: ${decision}`}),
    });
    if (!response.ok) throw new Error(await response.text());
    setNotice(`Review persisted: ${decision.replaceAll('_', ' ')}.`); await load();
  }

  async function createWorkOrder() {
    if (!x || x.id === 'offline') return;
    const response = await fetch(`${API_URL}/work-orders`, {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({finding_id: x.id, title: `Inspect ${x.finding_type.replaceAll('_',' ')}`, priority: x.severity.includes('high') ? 'high' : 'medium', recommendation: 'Qualified inspector to validate condition and define repair scope.'}),
    });
    if (!response.ok) throw new Error(await response.text());
    setNotice('Work order persisted and linked to this finding.');
  }

  const disabled = !x || x.id.startsWith('demo-');
  return <div className="workspace">
    {notice && <div className="notice">{notice}</div>}
    <section className="review-grid">
      <div className="panel evidence-panel">
        <div className="panel-head"><div><span className="eyebrow">EVIDENCE REVIEW</span><h3>{x?.finding_type.replaceAll('_',' ') ?? 'No finding'}</h3></div><span className={`severity ${x?.severity.includes('high')?'high':'moderate'}`}>{x?.severity}</span></div>
        <div className="evidence-stage">
          {x && !x.id.startsWith('demo-') ? <img className="evidence-image" src={`${API_URL}/findings/${x.id}/evidence`} alt="Generated inspection evidence overlay" /> : <div className="surface-texture"><span className="frame-label">PROJECT-OWNED DEMO SURFACE</span></div>}
        </div>
        <div className="evidence-caption"><span>Provenance: {x?.provenance}</span><span>Status: {x?.status}</span><span>Model: {x?.model_version}</span></div>
      </div>
      <aside className="panel inspector-panel">
        <span className="eyebrow">INSPECTOR CONTROLS</span><h3>Finding decision</h3>
        <div className="confidence-ring"><strong>{Math.round((x?.confidence ?? 0)*100)}%</strong><span>model confidence</span></div>
        <dl><div><dt>Provenance</dt><dd>{x?.provenance}</dd></div><div><dt>Status</dt><dd>{x?.status}</dd></div>{Object.entries(x?.measurement_json ?? {}).map(([k,v])=><div key={k}><dt>{k.replaceAll('_',' ')}</dt><dd>{String(v)}</dd></div>)}</dl>
        <div className="action-grid">
          <button disabled={disabled} className="accept" onClick={() => decide('accept')}>Accept</button>
          <button disabled={disabled} onClick={() => decide('reject')}>Reject</button>
          <button disabled={disabled} className="wide" onClick={() => decide('request_reinspection')}>Request reinspection</button>
          <button disabled={disabled} className="wide primary" onClick={createWorkOrder}>Create work order</button>
        </div>
      </aside>
    </section>
  </div>;
}
