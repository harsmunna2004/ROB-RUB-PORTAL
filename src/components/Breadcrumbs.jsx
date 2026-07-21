import { Link } from 'react-router-dom'
export default function Breadcrumbs({ items }) { return <nav className="breadcrumbs" aria-label="Breadcrumb">{items.map((item, i) => <span key={`${item.label}-${i}`}>{i > 0 && ' / '}{item.to ? <Link to={item.to}>{item.label}</Link> : item.label}</span>)}</nav> }
