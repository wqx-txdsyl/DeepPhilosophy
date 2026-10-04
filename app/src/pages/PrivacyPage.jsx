import { Link } from 'react-router-dom';
import PolicyLayout, { FeedbackLink } from '../components/PolicyLayout';
export default function PrivacyPage(){
 const sections=[
  {id:'privacy-scope',title:'适用范围',content:<p>本政策说明 DeepPhilosophy 主站在浏览、注册登录、阅读与批注同步过程中如何处理信息。浏览书籍、哲人和思想谱系无需注册；未登录时，阅读记录与批注保存在当前浏览器中。</p>},
  {id:'privacy-data',title:'处理哪些信息',content:<ul><li><strong>账户信息：</strong>用户名、密码哈希，以及你自愿设置的头像，用于登录认证和账户展示。服务器不保存可直接读取的密码文本。</li><li><strong>阅读记录：</strong>书籍标识、阅读章节、进度及最近阅读时间，用于继续阅读；登录后会尝试同步到当前账户。</li><li><strong>阅读批注：</strong>你输入和保存的笔记。笔记先在本机保留，登录后通过保存操作尝试同步；同步失败的草稿会保留在本机。</li><li><strong>必要的请求信息：</strong>提供网页、图片、鉴权与网络安全服务时，相关基础设施可能处理 IP 地址、请求时间和请求路径等网络信息。</li></ul>},
  {id:'privacy-local',title:'浏览器本地存储',content:<><p>本站使用浏览器本地存储保存登录令牌、阅读记录、批注、头像缓存，以及主题和显示偏好。访客与不同账户的本机阅读缓存分开保存。</p><p><strong>退出登录不会自动删除已保存的本机阅读缓存。</strong>在共用设备上使用后，可以通过浏览器的网站数据设置清除本站数据。清除浏览器数据会移除本机记录、登录状态和未同步草稿，但不会自动删除已经保存到云端的记录。</p></>},
  {id:'privacy-cloud',title:'云端同步与服务提供商',content:<><p>账户、阅读进度和批注通过 HTTPS 传输。阅读记录和私人批注不作为公开页面内容展示。请妥善保管登录信息，不要将密码或登录令牌交给他人。</p><ul><li><strong>Cloudflare：</strong>网站托管、账户认证、数据库与同步接口。</li><li><strong>阿里云 OSS：</strong>书籍正文、图片、封面及网站静态资源分发。</li><li><strong>jsDelivr：</strong>章节内容的备用分发。</li><li><strong>GitHub：</strong>项目代码与反馈入口。主动访问项目或提交反馈时，相关信息由 GitHub 按其规则处理。</li></ul><p>网络服务提供商按其服务规则处理必要请求信息。本站不会以“退出登录”或“清除缓存”代替云端数据删除。</p></>},
  {id:'privacy-controls',title:'查看、更正与删除',content:<><p>你可以在 <Link to="/profile">我的书房</Link> 查看阅读记录、编辑批注，在账户设置中修改用户名、头像和密码。书房的“清空阅读记录”会在登录且请求成功时同时清空相应云端阅读记录。</p><p>批注可以编辑为空并保存；登录后保存成功会更新云端对应内容。账户及其他数据的查阅、复制、更正或删除请求，可先通过 <FeedbackLink/> 联系维护者，确认身份核验与处理方式。</p><p>云端信息在提供账户和同步服务所需期间保存；你可以提出停止使用或删除请求。依法需要继续保存的信息，按适用要求处理。本机信息则保留至你清除网站数据或相关缓存。</p></>},
  {id:'privacy-contact',title:'联系与政策更新',content:<><p>维护者：@txdsyl_。隐私问题请通过 <FeedbackLink/> 提出。公开反馈中不要附上密码、登录令牌或完整的私人批注；涉及账户核验时，先说明请求类型，再确认合适的处理方式。</p><p>功能或数据处理方式变化时，我们会更新本页及更新时间；需要另行告知或取得同意的事项，会按适用要求处理。</p></>},
 ];
 return <PolicyLayout title="隐私政策" english="Privacy & your data" current="privacy" intro="说明你的账户、阅读记录和批注保存在哪里，以及如何管理它们。" sections={sections}/>;
}
