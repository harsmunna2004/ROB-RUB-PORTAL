export default function StatusBadge({ status }) { return <span className={`status-badge ${status}`}>{status === 'certified' ? 'Certified' : 'Pending'}</span> }
