/**
 * 用户头像 —— 默认某人图标，支持上传+裁剪正方形
 */
import { useState, useRef, useEffect } from 'react';
import Icon from './Icon';

const CROP_SIZE = 300;

function AvatarUpload({ size = 72, onSave }) {
  const [avatar, setAvatar] = useState(() => localStorage.getItem('dp_avatar') || '');
  const [showEditor, setShowEditor] = useState(false);
  const [showMenu, setShowMenu] = useState(false);
  const [srcImg, setSrcImg] = useState(null);
  const [scale, setScale] = useState(1);
  const [offX, setOffX] = useState(0);
  const [offY, setOffY] = useState(0);
  const [dragging, setDragging] = useState(false);
  const dragRef = useRef({ startX: 0, startY: 0, startOffX: 0, startOffY: 0 });
  const fileRef = useRef(null);
  const imgRef = useRef(null);
  const canvasRef = useRef(null);

  const doCrop = () => {
    const img = imgRef.current; const canvas = canvasRef.current;
    if (!img || !canvas) return;
    const iw = img.naturalWidth, ih = img.naturalHeight;
    const minDim = Math.min(iw, ih);
    const sx = (iw - minDim) / 2 - offX * (iw / CROP_SIZE);
    const sy = (ih - minDim) / 2 - offY * (ih / CROP_SIZE);
    const sw = minDim / scale, sh = minDim / scale;
    canvas.width = 200; canvas.height = 200;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(img, sx, sy, sw, sh, 0, 0, 200, 200);
  };

  useEffect(() => { if (showEditor && imgRef.current) doCrop(); }, [showEditor, scale, offX, offY]);

  const handleFile = (e) => {
    const f = e.target.files?.[0]; if (!f) return;
    const r = new FileReader();
    r.onload = (ev) => { setSrcImg(ev.target.result); setScale(1); setOffX(0); setOffY(0); setShowEditor(true); };
    r.readAsDataURL(f);
    e.target.value = '';
  };

  const handleSave = () => {
    const c = canvasRef.current; if (!c) return;
    const dataUrl = c.toDataURL('image/jpeg', 0.85);
    setAvatar(dataUrl);
    localStorage.setItem('dp_avatar', dataUrl);
    setShowEditor(false);
    if (onSave) onSave(dataUrl);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', position: 'relative' }}>
      <div onClick={() => setShowMenu(!showMenu)}
        style={{ width: size, height: size, borderRadius: '50%', overflow: 'hidden', cursor: 'pointer',
          border: '2px solid var(--border)', background: 'var(--card-bg)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}
        onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--ochre)'}
        onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}>
        {avatar ? <img src={avatar} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} /> : <Icon name="btn-user" size={size * 0.5} />}
      </div>
      {showMenu && (
        <div style={{ position: 'absolute', top: size + 8, background: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: 8, boxShadow: '0 4px 16px rgba(0,0,0,0.12)', zIndex: 100, overflow: 'hidden', minWidth: 140 }}>
          <div onClick={e => { e.stopPropagation(); setShowMenu(false); fileRef.current?.click(); }} style={{ padding: '10px 16px', cursor: 'pointer', fontSize: 13, color: 'var(--text)', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 8 }}><Icon name="icon-edit" size={14} /> 替换头像</div>
          {avatar && <div onClick={e => { e.stopPropagation(); setShowMenu(false); setAvatar(''); localStorage.removeItem('dp_avatar'); }} style={{ padding: '10px 16px', cursor: 'pointer', fontSize: 13, color: 'var(--text)', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 8 }}><Icon name="icon-refresh" size={14} /> 恢复默认</div>}
          <div onClick={e => { e.stopPropagation(); setShowMenu(false); }} style={{ padding: '10px 16px', cursor: 'pointer', fontSize: 13, color: 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: 8 }}><Icon name="icon-close" size={14} /> 取消</div>
        </div>
      )}
      <input ref={fileRef} type="file" accept="image/*" style={{ display: 'none' }} onChange={handleFile} />

      {showEditor && srcImg && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 9999, background: 'rgba(0,0,0,0.88)' }}
          onMouseMove={e => {
            if (!dragging) return;
            setOffX(dragRef.current.startOffX + e.clientX - dragRef.current.startX);
            setOffY(dragRef.current.startOffY + e.clientY - dragRef.current.startY);
          }}
          onMouseUp={() => setDragging(false)}
          onMouseLeave={() => setDragging(false)}>
          <div style={{ color: '#fff', textAlign: 'center', paddingTop: 40, fontSize: 13 }}>拖拽移动 · 滚轮缩放 · 圆形裁剪</div>
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 'calc(100vh - 180px)' }}>
            <div style={{ width: CROP_SIZE, height: CROP_SIZE, overflow: 'hidden', position: 'relative', borderRadius: '50%', border: '3px solid rgba(255,255,255,0.5)', boxShadow: '0 0 0 9999px rgba(0,0,0,0.5)' }}
              onWheel={e => { e.preventDefault(); setScale(s => Math.max(0.5, Math.min(3, s - e.deltaY * 0.002))); }}
              onMouseDown={e => {
                setDragging(true);
                dragRef.current = { startX: e.clientX, startY: e.clientY, startOffX: offX, startOffY: offY };
              }}>
              <img ref={imgRef} src={srcImg} alt="" draggable={false}
                style={{ width: CROP_SIZE * scale, minWidth: '100%', position: 'absolute', left: '50%', top: '50%',
                  transform: `translate(calc(-50% + ${offX}px), calc(-50% + ${offY}px))`,
                  pointerEvents: 'none', userSelect: 'none' }} />
            </div>
          </div>
          <canvas ref={canvasRef} style={{ display: 'none' }} />
          <div style={{ display: 'flex', gap: 16, justifyContent: 'center', paddingBottom: 40 }}>
            <button className="btn btn-secondary" onClick={() => setShowEditor(false)}
              style={{ padding: '10px 28px', fontSize: 14, borderColor: 'rgba(255,255,255,0.3)', color: '#fff' }}>取消</button>
            <button className="btn btn-primary" onClick={handleSave}
              style={{ padding: '10px 28px', fontSize: 14, background: 'var(--ochre)', borderColor: 'var(--ochre)', color: '#fff' }}>确认裁剪</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default AvatarUpload;
