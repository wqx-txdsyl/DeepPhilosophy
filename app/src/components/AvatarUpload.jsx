/**
 * 用户头像 —— 默认用某人图标，支持上传+裁剪正方形照片
 * 头像 base64 存入 localStorage.dp_avatar，云端同步
 */
import { useState, useRef, useEffect, useCallback } from 'react';
import Icon from './Icon';

const STORAGE_KEY = 'dp_avatar';

function AvatarUpload({ size = 80, onSave }) {
  const [avatar, setAvatar] = useState(() => localStorage.getItem(STORAGE_KEY) || '');
  const [showMenu, setShowMenu] = useState(false);
  const [showEditor, setShowEditor] = useState(false);
  const [srcImg, setSrcImg] = useState(null);
  const [scale, setScale] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [dragging, setDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const canvasRef = useRef(null);
  const fileRef = useRef(null);
  const imgRef = useRef(null);

  // 裁剪区域固定正方形，取 min(w,h)
  const CROP_SIZE = 300;

  const getCropParams = useCallback(() => {
    if (!imgRef.current) return { sx: 0, sy: 0, sw: 100, sh: 100 };
    const img = imgRef.current;
    const iw = img.naturalWidth, ih = img.naturalHeight;
    const minDim = Math.min(iw, ih);
    const sx = (iw - minDim) / 2 + offset.x * (iw / CROP_SIZE);
    const sy = (ih - minDim) / 2 + offset.y * (ih / CROP_SIZE);
    const sw = minDim / scale;
    const sh = minDim / scale;
    return { sx, sy, sw, sh };
  }, [scale, offset]);

  const renderCrop = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || !imgRef.current) return;
    const { sx, sy, sw, sh } = getCropParams();
    canvas.width = 200; canvas.height = 200;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, 200, 200);
    ctx.drawImage(imgRef.current, sx, sy, sw, sh, 0, 0, 200, 200);
  }, [getCropParams]);

  useEffect(() => {
    if (showEditor && imgRef.current) {
      imgRef.current.onload = () => renderCrop();
      if (imgRef.current.complete) renderCrop();
    }
  }, [showEditor, scale, offset, renderCrop]);

  const handleFile = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      setSrcImg(ev.target.result);
      setScale(1); setOffset({ x: 0, y: 0 });
      setShowEditor(true);
    };
    reader.readAsDataURL(file);
    e.target.value = '';
  };

  const handleSave = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const dataUrl = canvas.toDataURL('image/jpeg', 0.85);
    setAvatar(dataUrl);
    localStorage.setItem(STORAGE_KEY, dataUrl);
    setShowEditor(false);
    if (onSave) onSave(dataUrl);
  };

  const handleWheel = (e) => {
    e.preventDefault();
    setScale(s => Math.max(0.5, Math.min(3, s - e.deltaY * 0.001)));
  };

  const handleMouseDown = (e) => {
    setDragging(true);
    setDragStart({ x: e.clientX - offset.x, y: e.clientY - offset.y });
  };
  const handleMouseMove = (e) => {
    if (!dragging) return;
    setOffset({
      x: Math.max(-CROP_SIZE/2, Math.min(CROP_SIZE/2, e.clientX - dragStart.x)),
      y: Math.max(-CROP_SIZE/2, Math.min(CROP_SIZE/2, e.clientY - dragStart.y)),
    });
  };
  const handleMouseUp = () => setDragging(false);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', position: 'relative' }}>
      {/* Avatar display */}
      <div
        onClick={() => setShowMenu(!showMenu)}
        style={{
          width: size, height: size, borderRadius: '50%', overflow: 'hidden',
          cursor: 'pointer', border: '2px solid var(--border)',
          background: 'var(--card-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center',
          transition: 'border-color 0.2s', flexShrink: 0,
        }}
        onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--ochre)'}
        onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
        title="点击更换头像"
      >
        {avatar ? (
          <img src={avatar} alt="头像" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
        ) : (
          <Icon name="btn-user" size={size * 0.5} />
        )}
      </div>
      {/* Click menu */}
      {showMenu && (
        <div style={{
          position: 'absolute', top: size + 8,
          background: 'var(--card-bg)', border: '1px solid var(--border)',
          borderRadius: 8, boxShadow: '0 4px 16px rgba(0,0,0,0.12)',
          zIndex: 100, overflow: 'hidden', minWidth: 140,
        }}>
          <div onClick={(e) => { e.stopPropagation(); setShowMenu(false); fileRef.current?.click(); }}
            style={{ padding: '10px 16px', cursor: 'pointer', fontSize: 13,
              color: 'var(--text)', borderBottom: '1px solid var(--border)',
              transition: 'background 0.15s',
            }}
            onMouseEnter={e => e.currentTarget.style.background = 'var(--secondary)'}
            onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
            📷 替换头像
          </div>
          <div onClick={(e) => { e.stopPropagation(); setShowMenu(false); }}
            style={{ padding: '10px 16px', cursor: 'pointer', fontSize: 13, color: 'var(--text-dim)',
              transition: 'background 0.15s',
            }}
            onMouseEnter={e => e.currentTarget.style.background = 'var(--secondary)'}
            onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
            ✕ 取消
          </div>
        </div>
      )}
      <input ref={fileRef} type="file" accept="image/*" style={{ display: 'none' }} onChange={handleFile} />

      {/* Crop editor modal */}
      {showEditor && srcImg && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 9999,
          background: 'rgba(0,0,0,0.85)', display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center',
        }}>
          <div style={{ color: '#fff', marginBottom: 12, fontSize: 13 }}>
            拖拽移动 · 滚轮缩放 · 裁剪正方形头像
          </div>
          <div style={{
            width: CROP_SIZE, height: CROP_SIZE, overflow: 'hidden', position: 'relative',
            border: '2px dashed rgba(255,255,255,0.6)', borderRadius: 4, cursor: 'grab',
          }}
            onWheel={handleWheel}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
          >
            <img ref={imgRef} src={srcImg} alt="裁剪" draggable={false}
              style={{
                width: CROP_SIZE * scale, height: 'auto',
                transform: `translate(${offset.x}px, ${offset.y}px)`,
                pointerEvents: 'none', userSelect: 'none',
              }} />
          </div>
          <canvas ref={canvasRef} style={{ display: 'none' }} />
          <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
            <button className="btn btn-secondary" onClick={() => setShowEditor(false)}
              style={{ padding: '8px 20px', fontSize: 13, color: '#fff', borderColor: 'rgba(255,255,255,0.3)' }}>
              取消
            </button>
            <button className="btn btn-primary" onClick={handleSave}
              style={{ padding: '8px 20px', fontSize: 13, color: '#fff', borderColor: 'var(--ochre)' }}>
              确认裁剪
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default AvatarUpload;
