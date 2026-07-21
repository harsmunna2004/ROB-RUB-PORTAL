import { useEffect, useMemo, useRef, useState } from 'react'
import './SearchableSelect.css'

export default function SearchableSelect({label,value,options,onChange,placeholder,disabled=false,loading=false}){
  const [open,setOpen]=useState(false),[search,setSearch]=useState(''),[active,setActive]=useState(0)
  const root=useRef(null), input=useRef(null)
  const filtered=useMemo(()=>options.filter(option=>option.toLocaleLowerCase().includes(search.trim().toLocaleLowerCase())),[options,search])
  useEffect(()=>{function outside(event){if(!root.current?.contains(event.target))setOpen(false)}document.addEventListener('mousedown',outside);return()=>document.removeEventListener('mousedown',outside)},[])
  useEffect(()=>{if(open){setActive(0);setTimeout(()=>input.current?.focus(),0)}else setSearch('')},[open])
  function choose(option){onChange(option);setOpen(false)}
  function keys(event){if(event.key==='Escape'){setOpen(false);return}if(event.key==='ArrowDown'){event.preventDefault();if(!open)return setOpen(true);setActive(index=>Math.min(index+1,filtered.length-1))}if(event.key==='ArrowUp'){event.preventDefault();setActive(index=>Math.max(index-1,0))}if(event.key==='Enter'&&open&&filtered[active]){event.preventDefault();choose(filtered[active])}}
  return <div className={`searchable-select ${disabled?'disabled':''}`} ref={root} onKeyDown={keys}><span className="select-label">{label}</span><button type="button" className="select-trigger" disabled={disabled||loading} aria-label={`${label}: ${value||placeholder}`} aria-haspopup="listbox" aria-expanded={open} onClick={()=>setOpen(current=>!current)}><span className={value?'selected-value':'select-placeholder'}>{loading?'Loading…':value||placeholder}</span><span className={`select-chevron ${open?'open':''}`}>⌄</span></button>{open&&<div className="select-menu" role="listbox" aria-label={`${label} options`}><div className="select-search-wrap"><input ref={input} className="select-search" value={search} onChange={event=>setSearch(event.target.value)} placeholder={`Search ${label}`} aria-label={`Search ${label}`}/></div>{filtered.map((option,index)=><button type="button" role="option" aria-selected={option===value} className={`select-option ${index===active?'active':''} ${option===value?'selected':''}`} key={option} onMouseEnter={()=>setActive(index)} onClick={()=>choose(option)}><span>{option}</span>{option===value&&<span aria-hidden="true">✓</span>}</button>)}{!filtered.length&&<p className="select-empty">No matching options</p>}</div>}</div>
}
