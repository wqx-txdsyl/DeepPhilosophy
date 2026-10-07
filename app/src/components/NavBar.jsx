import { Link, useLocation } from 'react-router-dom';
import Icon from './Icon';
import './NavBar.css';
const TABS=[{key:'books',icon:'nav-books',text:'书籍',path:'/books'},{key:'authors',icon:'nav-authors',text:'哲人',path:'/authors'},{key:'genealogy',icon:'nav-genealogy',text:'谱系',path:'/genealogy'},{key:'more',icon:'icon-sparkles',text:'更多',path:'/more'}];
function activeSection(path){
  if(/^\/(books?|reader)(\/|$)/.test(path))return 'books';
  if(/^\/authors?(\/|$)/.test(path))return 'authors';
  if(/^\/(genealogy|school|world-philosophies|western-philosophies|eastern-philosophies)(\/|$)/.test(path))return 'genealogy';
  if(/^\/more(\/|$)/.test(path))return 'more';
  return null;
}
export default function NavBar({variant='sticky',darkMode,onToggleDarkMode,loggedIn,username,userAvatar}){
  const {pathname}=useLocation();if(variant==='hidden')return null;
  const floating=variant==='floating',active=activeSection(pathname),inRoom=pathname.startsWith('/profile');
  return <nav className={`${floating?'navbar-floating':'app-header'} site-nav`} aria-label="主导航">
    <Link className="app-title site-nav-brand" to="/" aria-label="DeepPhilosophy 首页">DeepPhilosophy</Link>
    <div className="site-nav-links">{TABS.map(tab=><Link key={tab.key} className={`nav-btn${active===tab.key?' active':''}`} to={tab.path} aria-current={active===tab.key?'page':undefined}><Icon name={tab.icon} size={16}/><span>{tab.text}</span></Link>)}</div>
    <div className="site-nav-tools">{!floating&&<><button className="settings-btn" onClick={onToggleDarkMode} aria-label={darkMode?'切换到亮色模式':'切换到暗色模式'}><Icon name={darkMode?'theme-light':'theme-dark'} size={18}/></button></>}
      <Link className={`site-room-link${inRoom?' is-active':''}`} to="/profile" aria-current={inRoom?'page':undefined} aria-label={floating&&loggedIn&&username?`我的书房：${username}`:'我的书房'}>{floating&&userAvatar?<img className="site-nav-avatar" src={userAvatar} alt=""/>:<Icon name="btn-user" size={17}/>}<span>我的书房</span></Link>
    </div>
  </nav>;
}
