'use client';
import { AsyncPanel } from '../../components/AsyncPanel';

type Facility = { id:string; name:string; country:string; latitude:number|null; longitude:number|null; risk_score:number };
const fallback: Facility[] = [
  {id:'1',name:'Ras Laffan Offshore Demo',country:'Qatar',latitude:25.9,longitude:51.5,risk_score:34},
  {id:'2',name:'Bridge Materials Lab',country:'Pakistan',latitude:33.6,longitude:73.0,risk_score:22},
];
export default function Facilities(){return <AsyncPanel<Facility[]> path="/facilities" fallback={fallback}>{(items)=><div className="workspace"><div className="panel"><div className="panel-head"><div><span className="eyebrow">FACILITY COMMAND</span><h3>Operating sites</h3></div><span className="tag">{items.length} registered</span></div><div className="facility-grid">{items.map((x,i)=><article className="facility-card" key={x.id}><div className="facility-code">SITE-{String(i+1).padStart(2,'0')}</div><h3>{x.name}</h3><p>{x.country}</p><div className="mini-map"><div className="crosshair"/></div><div className="card-stats"><span>Risk<strong>{x.risk_score.toFixed(0)}</strong></span><span>Coordinates<strong>{x.latitude?.toFixed(2) ?? '—'} / {x.longitude?.toFixed(2) ?? '—'}</strong></span></div></article>)}</div></div></div>}</AsyncPanel>}
