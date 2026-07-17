/**
 * 用户协议页面
 */
import { useNavigate } from 'react-router-dom';

export default function TermsPage() {
  const navigate = useNavigate();
  return (
    <div className="page-container" style={{ maxWidth: 800, margin: '0 auto', padding: '40px 24px', lineHeight: 1.9 }}>
      <button className="btn btn-secondary" onClick={() => navigate(-1)} style={{ marginBottom: 24 }}>← 返回</button>
      <h1 style={{ fontFamily: 'var(--font-serif)', fontSize: 28, marginBottom: 24 }}>用户协议</h1>
      <p style={{ color: 'var(--text-dim)', marginBottom: 16 }}>最后更新：2026年7月</p>

      <h2 style={{ fontSize: 18, marginTop: 24 }}>1. 服务说明</h2>
      <p>DeepPhilosophy 是一个哲学知识平台，提供书籍浏览、AI 问答、哲学游戏等功能。服务免费提供，不保证持续可用性。</p>

      <h2 style={{ fontSize: 18, marginTop: 24 }}>2. 用户责任</h2>
      <p>您同意：不滥用 AI 问答功能生成违法内容；不上传侵权或恶意文件；不尝试攻击或逆向工程本平台。</p>

      <h2 style={{ fontSize: 18, marginTop: 24 }}>3. 知识产权</h2>
      <p>平台上的哲学著作版权归属原作者或出版社。书籍文件仅用于学术研究和学习目的。平台代码为开源项目。</p>

      <h2 style={{ fontSize: 18, marginTop: 24 }}>4. 免责声明</h2>
      <p>AI 回答内容由大语言模型生成，不代表平台立场。语音识别结果可能存在误差。平台不对因服务中断或数据丢失造成的损失承担责任。</p>

      <h2 style={{ fontSize: 18, marginTop: 24 }}>5. 协议变更</h2>
      <p>我们可能随时更新本协议。重大变更将通过网站公告通知。</p>
    </div>
  );
}
