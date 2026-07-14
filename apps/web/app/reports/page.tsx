'use client';
import { AsyncPanel } from '../../components/AsyncPanel';
import { API_URL } from '../../lib/api';

type Report={id:string;mission_id:string;report_type:string;checksum:string;status:string;created_at:string;download_url:string};
const fallback:Report[]=[
  {id:'demo-mission-report',mission_id:'demo-structural',report_type:'mission',checksum:'demo7e4c2d8f8a2b91f4b7a9e05f0a8d6c3b2a1f4e8d9c0b7a6e5d4c3b2a1908',status:'generated',created_at:'2026-07-14T09:00:00Z',download_url:'#'},
  {id:'demo-coverage-report',mission_id:'demo-pipeline',report_type:'coverage',checksum:'demo3b8f1a4d9c7e2b5a0f6d8c1e4b7a9f2c5d8e1a4b7c0d3e6f9a2b5c8d1e4f7a',status:'generated',created_at:'2026-07-14T09:05:00Z',download_url:'#'},
];
export default function Reports(){return <AsyncPanel<Report[]> path="/reports" fallback={fallback}>{(items)=><div className="workspace"><div className="panel"><div className="panel-head"><div><span className="eyebrow">AUDIT-READY OUTPUT</span><h3>Generated reports</h3></div><span className="tag">{items.length} persisted</span></div>{items.length===0?<div className="empty-state"><h3>No reports loaded</h3><p>Run <code>make demo</code> and start the API to display query-driven reports.</p></div>:<div className="report-grid">{items.map((x,i)=><article className="report-card" key={x.id}><span className="report-index">{String(i+1).padStart(2,'0')}</span><h3>{x.report_type.replaceAll('_',' ')} report</h3><p>Generated from persisted mission, finding, evidence, model and audit records.</p><div><span>SHA-256</span><strong>{x.checksum.slice(0,12)}…{x.checksum.slice(-8)}</strong></div><a className="report-button" href={`${API_URL}${x.download_url}`} target="_blank" rel="noreferrer">Open report</a></article>)}</div>}</div></div>}</AsyncPanel>}
