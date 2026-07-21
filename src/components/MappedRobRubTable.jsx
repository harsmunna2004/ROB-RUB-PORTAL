import './MappedRobRubTable.css'

const empty=value=>value||'—'
export default function MappedRobRubTable({records=[],canDelete=false,deletingId='',onDelete}){
  if(!records.length)return null
  return <section className="mapped-details"><h2>Mapped ROBs/RUBs</h2><p className="mapped-details-note">Saved ROB/RUB records for this project.</p><div className="table-scroll"><table><thead><tr><th>Proposal ID</th><th>Proposal Date</th><th>Name of Work</th><th>Division/Railway</th><th>State</th><th>Road Authority</th><th>Category</th><th>Name of Road</th><th>Date Mapped</th>{canDelete&&<th>Action</th>}</tr></thead><tbody>{records.map(record=><tr key={record.proposal_id}><td><strong>{record.proposal_id}</strong></td><td>{empty(record.proposal_date)}</td><td>{empty(record.name_of_work)}</td><td>{empty(record.division_railway)}</td><td>{empty(record.state)}</td><td>{empty(record.associated_road_authority)}</td><td>{empty(record.category_of_road)}</td><td>{empty(record.name_of_road)}</td><td>{record.date_mapped?new Date(record.date_mapped).toLocaleString():'—'}</td>{canDelete&&<td><button type="button" className="delete-mapping" aria-label={`Delete mapping ${record.proposal_id}`} disabled={deletingId===record.proposal_id} onClick={()=>onDelete(record.proposal_id)}>{deletingId===record.proposal_id?'Deleting…':'Delete'}</button></td>}</tr>)}</tbody></table></div></section>
}
