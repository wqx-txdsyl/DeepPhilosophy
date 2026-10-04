import { Link } from 'react-router-dom';
import PolicyLayout, { FeedbackLink } from '../components/PolicyLayout';
export default function TermsPage(){
 const sections=[
  {id:'terms-service',title:'网站提供什么',content:<p>DeepPhilosophy 提供哲学书籍目录与在线阅读、哲人和流派资料、思想谱系浏览，以及阅读记录和批注功能。部分作品仅收录书目资料，是否可以在线阅读以页面标注为准。目前主站免费提供这些服务。</p>},
  {id:'terms-account',title:'账户与阅读数据',content:<><p>浏览与阅读无需先注册。使用账户同步功能时，请提供可正常使用的用户名并妥善保管密码；不要冒用他人身份或未经授权使用他人的账户。</p><p>阅读进度与批注可能因网络、设备或浏览器存储限制而同步失败。请留意保存状态，并自行保留重要笔记。个人信息处理方式见 <Link to="/privacy">隐私政策</Link>。</p></>},
  {id:'terms-use',title:'合理使用',content:<p>请勿利用本站实施违法活动、侵害他人权利、传播恶意内容、绕过鉴权或攻击服务。自动化访问应避免影响其他用户的正常阅读。提交头像、批注或反馈时，请确保你有权使用相关内容。</p>},
  {id:'terms-copyright',title:'作品与知识产权',content:<><p>哲学著作、译文、图片及其他内容的权利归相应权利人所有。本站收录或提供阅读入口，不表示作品已经进入公有领域，也不构成任意复制、转载或再分发的授权。使用内容需遵守其实际授权范围和适用法律。</p><p>项目代码的使用范围以仓库明确载明的许可为准。若你认为某项内容侵犯你的权利，请通过 <FeedbackLink/> 提供作品名称、页面链接、具体位置及可核对的权利说明，以便核查处理。</p></>},
  {id:'terms-content',title:'内容修订与服务维护',content:<><p>本站资料持续整理和修订。简介、分类和关联内容用于辅助阅读，不替代原著、版本说明或专业研究；如发现错误，欢迎提供出处帮助核对。</p><p>我们会尽力维护服务，但不能保证所有内容始终无误或服务持续不中断。维护、网络故障或内容核查可能导致暂时不可用。各方责任依法确定，本说明不排除适用法律规定的法定义务与用户权利。</p></>},
  {id:'terms-contact',title:'协议更新与联系',content:<><p>服务内容变化时，本协议会相应更新，并在本页标明更新时间。对使用方式有实质影响的变更，会在相关页面提供说明。</p><p>维护者：@txdsyl_。使用问题、内容纠错与权利反馈可通过 <FeedbackLink/> 联系，也可以先阅读 <Link to="/about">关于本站</Link>。</p></>},
 ];
 return <PolicyLayout title="用户协议" english="Terms of use" current="terms" intro="了解本站的服务范围、合理使用方式、内容权利与反馈渠道。" sections={sections}/>;
}
