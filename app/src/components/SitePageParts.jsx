import { useState } from 'react';
import { Link } from 'react-router-dom';
import CdnImage from './CdnImage';
export function SiteFooter(){return <footer className="s-footer"><span>DeepPhilosophy · @txdsyl_</span><div><Link to="/about">关于本站</Link><Link to="/privacy">隐私政策</Link><Link to="/terms">用户协议</Link></div></footer>;}
export function RoomCover({book,hero=false}){const [failed,setFailed]=useState(false);return book?.cover?.startsWith('/covers/')&&!failed?<CdnImage src={book.cover} alt={`${book.title}封面`} className="s-cover" imageWidth={hero?480:240} loading={hero?'eager':'lazy'} decoding="async" onError={()=>setFailed(true)} />:<div className="s-book-placeholder"><span>{book?.title||'阅读记录'}</span><small>{book?.author||''}</small></div>;}
