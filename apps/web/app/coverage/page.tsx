'use client';
import { AsyncPanel } from '../../components/AsyncPanel';

type Segment={start_m:number;end_m:number;visibility:number;covered:boolean;reason:string};
type Mission={id:string;name:string;mission_type:string;coverage_percent:number;summary_json:{coverage?:{segments:Segment[];coverage_percent:number;missing_segments:number;low_confidence_segments:number};distance_m?:number}};
const fallback:Mission[]=[{id:'demo-pipeline',name:'Subsea Pipeline Pass 01',mission_type:'pipeline',coverage_percent:83.3,summary_json:{coverage:{coverage_percent:83.3,missing_segments:0,low_confidence_segments:2,segments:[
  {start_m:0,end_m:5,visibility:.72,covered:true,reason:'covered'},
  {start_m:5,end_m:10,visibility:.69,covered:true,reason:'covered'},
  {start_m:10,end_m:15,visibility:.64,covered:true,reason:'covered'},
  {start_m:15,end_m:20,visibility:.37,covered:false,reason:'low-visibility'},
  {start_m:20,end_m:25,visibility:.74,covered:true,reason:'covered'},
  {start_m:25,end_m:30,visibility:.78,covered:true,reason:'covered'},
  {start_m:30,end_m:35,visibility:.35,covered:false,reason:'low-visibility'},
  {start_m:35,end_m:40,visibility:.81,covered:true,reason:'covered'},
  {start_m:40,end_m:45,visibility:.79,covered:true,reason:'covered'},
  {start_m:45,end_m:50,visibility:.76,covered:true,reason:'covered'},
  {start_m:50,end_m:55,visibility:.73,covered:true,reason:'covered'},
  {start_m:55,end_m:60,visibility:.70,covered:true,reason:'covered'},
]},distance_m:60}}];

export default function Coverage(){return <AsyncPanel<Mission[]> path="/missions" fallback={fallback}>{(missions)=>{
  const mission=missions.find(m=>m.mission_type==='pipeline') ?? fallback[0];
  const coverage=mission.summary_json.coverage ?? fallback[0].summary_json.coverage!;
  const segments=coverage.segments; const distance=mission.summary_json.distance_m ?? segments.at(-1)?.end_m ?? 0;
  return <div className="workspace"><section className="split-grid"><div className="panel"><div className="panel-head"><div><span className="eyebrow">CALCULATED LINEAR COVERAGE</span><h3>{mission.name}</h3></div><span className="tag">{coverage.coverage_percent.toFixed(1)}%</span></div>
    <div className="pipeline-map"><div className="pipe-line"/>{segments.map((s,i)=><div key={`${s.start_m}-${s.end_m}`} className={`segment ${s.reason==='no-observation'?'missing':s.reason==='low-visibility'?'low':''}`} style={{left:`${distance ? (s.start_m/distance)*88+4 : 4}%`}}><span>{s.start_m.toFixed(0)}m</span></div>)}</div>
    <div className="legend"><span><i className="covered"/>Covered</span><span><i className="low"/>Low visibility</span><span><i className="missing"/>Missing</span></div></div>
    <div className="panel"><div className="panel-head"><div><span className="eyebrow">REINSPECTION</span><h3>Calculated exception segments</h3></div><span className="tag">{coverage.low_confidence_segments+coverage.missing_segments} flagged</span></div><div className="data-table"><div className="table-row table-head"><span>Segment</span><span>Status</span><span>Visibility</span><span>Action</span></div>{segments.filter(s=>!s.covered).map(s=><div className="table-row" key={s.start_m}><span>{s.start_m.toFixed(0)}–{s.end_m.toFixed(0)} m</span><span><b className={`severity ${s.reason==='no-observation'?'critical':'moderate'}`}>{s.reason}</b></span><span>{s.visibility.toFixed(2)}</span><span>{s.reason==='no-observation'?'Mandatory reinspection':'Repeat with improved visibility'}</span></div>)}</div></div></section></div>;
}}</AsyncPanel>}
