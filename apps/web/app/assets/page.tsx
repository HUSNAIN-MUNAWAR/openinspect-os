'use client';
import { AsyncPanel } from '../../components/AsyncPanel';
type Asset={id:string;name:string;asset_type:string;external_id:string;criticality:string;status:string;metadata_json:Record<string,unknown>};
const fallback:Asset[]=[
{id:'1',name:'Concrete Test Wall A',asset_type:'concrete_structure',external_id:'CWA-001',criticality:'high',status:'active',metadata_json:{}},
{id:'2',name:'Subsea Outfall Pipeline P-14',asset_type:'subsea_pipeline',external_id:'P-14',criticality:'critical',status:'active',metadata_json:{}},
{id:'3',name:'North Bridge Deck',asset_type:'bridge_deck',external_id:'BD-004',criticality:'high',status:'active',metadata_json:{}},
];
export default function Assets(){return <AsyncPanel<Asset[]> path="/assets" fallback={fallback}>{(items)=><div className="workspace"><div className="panel"><div className="panel-head"><div><span className="eyebrow">ASSET REGISTRY</span><h3>Facility hierarchy and inspection state</h3></div><span className="tag">{items.length} assets</span></div><div className="data-table"><div className="table-row table-head"><span>Asset</span><span>Type</span><span>External ID</span><span>Criticality</span><span>Status</span></div>{items.map(x=><div className="table-row" key={x.id}><span><strong>{x.name}</strong></span><span>{x.asset_type.replaceAll('_',' ')}</span><span className="mono">{x.external_id}</span><span><b className={`severity ${x.criticality}`}>{x.criticality}</b></span><span><b className="state online">{x.status}</b></span></div>)}</div></div></div>}</AsyncPanel>}
