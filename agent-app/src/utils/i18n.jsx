import { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { useAuth } from '../auth';

/**
 * i18n — 双语（中文/English）
 * 语言来源: 登录用户 profile.language > localStorage
 * 切换: 存 localStorage + 登录时同步 profile
 */

const UI = {
  zh: {
    sidebarTitle: '智能体广场', agentNote: '哲学家智能体基于其著作语料与人格数据构建',
    login: '登录 / 注册', logout: '登出', userCenter: '用户中心',
    placeholder: '问一个哲学问题…', send: '↑', stop: '■',
    startThinking: '开始思考', reasoningSummary: '✦ 推理摘要',
    thoughts: '思考过程', explore: '可继续探索', citations: '引用来源',
    thinkingStatus: '开始思考', settings: '设置', back: '← 返回',
    attach: '上传附件（md 直读 / 文档转 md / 图片识图）', drawioEdit: '✏️ draw.io 编辑', drawioReEdit: '✏️ 重新编辑',
    warning: '⚠ 该回答涉及敏感内容，请以批判性思考对待（哲学讨论语境）。',
    secGeneral: '通用', secAccount: '账户', secPersonal: '个性化', secData: '数据',
    appearance: '外观', theme: '主题', language: '语言', answerLang: '回答与思考语言',
    notification: '浏览器通知', notifDesc: '回答完成时收到浏览器通知', account: '账户',
    username: '用户名', session: '会话', sessionDesc: '对话历史自动同步（登录后跨设备）',
    updatePassword: '更新密码', deleteAccount: '删除账户', personal: '个性化（Agent 据此定制回答）',
    nickname: '昵称', occupation: '职业', about: '关于你', customInstr: '自定义指令',
    save: '保存', dataMgmt: '数据管理', chatHistory: '对话历史', chatHistoryDesc: '登录后自动保存，支持跨设备同步',
    clearHistory: '清除全部对话历史', settings: '设置',
    calling: '正在调用', tryAsk: '试着问：', stopGenerating: '停止生成',
    uploadFail: '上传失败', reqFail: '请求失败', bodyText: '正文', philoAgent: '哲学家智能体',
    citeFail: '无法定位出处', citeOpen: '阅读原文', attachmentNote: '附件',
    saved: '已保存', saveFail: '保存失败', oldPwdPrompt: '输入当前密码',
    newPwdPrompt: '输入新密码（≥8 字符）', pwdShort: '新密码至少 8 字符', pwdUpdated: '密码已更新', pwdFail: '修改失败',
    clearConfirm: '确定清除全部对话历史？此操作不可撤销。', historyCleared: '历史已清除',
    deleteConfirm: '确定删除账户及全部数据？此操作不可撤销！', deleteFail: '删除失败',
    notifUnsupported: '浏览器不支持通知', notifEnabled: '通知已开启', notifDenied: '通知被拒绝',
    nicknamePh: '你的昵称', occupationPh: '如: 哲学学生 / 研究者',
    aboutPh: '兴趣、背景、关注的问题…（Agent 会参考）',
    customInstrPh: '如: 简洁直接；回答引用原典时标注出处；默认用中文',
    themeLight: '浅色', themeDark: '深色', themeAuto: '自动',
    attachDataTitle: '附件与图表', attachDataDesc: '上传的附件随对话发送，不单独存储',
    regLogin: '注册并登录', busy: '处理中…', needUserPwd: '请输入用户名和密码',
    userExists: '用户名已存在', wrongCreds: '用户名或密码错误', unknownErr: '请求失败，请稍后重试',
    regAutoLoginFail: '注册成功，自动登录失败，请手动登录',
    signIn: '登录', register: '注册', usernamePh: '用户名（≥2 字符）', passwordPh: '密码（≥8 字符）',
    drawioTitle: 'draw.io 图表编辑器', drawioDone: '完成编辑',
  },
  en: {
    sidebarTitle: 'Agent Plaza', agentNote: 'Philosopher agents built from their corpus & persona data',
    login: 'Sign in / Register', logout: 'Sign out', userCenter: 'User Center',
    placeholder: 'Ask a philosophy question…', send: '↑', stop: '■',
    startThinking: 'Thinking…', reasoningSummary: '✦ Reasoning Summary',
    thoughts: 'Thoughts', explore: 'Explore further', citations: 'Sources',
    thinkingStatus: 'Thinking…', settings: 'Settings', back: '← Back',
    attach: 'Upload attachment (md read / docs via markitdown / image vision)',
    drawioEdit: '✏️ Edit in draw.io', drawioReEdit: '✏️ Re-edit',
    warning: '⚠ This response touches sensitive content — approach it critically (philosophical context).',
    secGeneral: 'General', secAccount: 'Account', secPersonal: 'Personalization', secData: 'Data',
    appearance: 'Appearance', theme: 'Theme', language: 'Language', answerLang: 'Answer & Thinking Language',
    notification: 'Browser Notifications', notifDesc: 'Receive browser notifications when answers complete',
    account: 'Account', username: 'Username', session: 'Session', sessionDesc: 'Chat history syncs automatically (across devices)',
    updatePassword: 'Update Password', deleteAccount: 'Delete Account',
    personal: 'Personalization (agent customizes answers)', nickname: 'Nickname', occupation: 'Occupation',
    about: 'About you', customInstr: 'Custom Instructions', save: 'Save',
    dataMgmt: 'Data Management', chatHistory: 'Chat History', chatHistoryDesc: 'Saved automatically when signed in, synced across devices',
    clearHistory: 'Clear all chat history', settings: 'Settings',
    calling: 'Calling', tryAsk: 'Try asking:', stopGenerating: 'Stop generating',
    uploadFail: 'Upload failed', reqFail: 'Request failed', bodyText: 'Main text', philoAgent: 'Philosopher Agent',
    citeFail: 'Source not found', citeOpen: 'Read source', attachmentNote: 'Attachment',
    saved: 'Saved', saveFail: 'Save failed', oldPwdPrompt: 'Enter current password',
    newPwdPrompt: 'Enter new password (≥8 chars)', pwdShort: 'Password must be at least 8 chars',
    pwdUpdated: 'Password updated', pwdFail: 'Update failed',
    clearConfirm: 'Clear all chat history? This cannot be undone.', historyCleared: 'History cleared',
    deleteConfirm: 'Delete account and all data? This cannot be undone!', deleteFail: 'Delete failed',
    notifUnsupported: 'Notifications not supported', notifEnabled: 'Notifications enabled', notifDenied: 'Notifications denied',
    nicknamePh: 'Your nickname', occupationPh: 'e.g. Philosophy student / Researcher',
    aboutPh: 'Interests, background, questions… (the agent will reference)',
    customInstrPh: 'e.g. Be concise; cite sources for quotes; default to English',
    themeLight: 'Light', themeDark: 'Dark', themeAuto: 'Auto',
    attachDataTitle: 'Attachments & Diagrams', attachDataDesc: 'Attachments are sent with the conversation; not stored separately',
    regLogin: 'Register & sign in', busy: 'Processing…', needUserPwd: 'Enter username and password',
    userExists: 'Username already taken', wrongCreds: 'Wrong username or password', unknownErr: 'Request failed, try again later',
    regAutoLoginFail: 'Registered, auto sign-in failed—sign in manually',
    signIn: 'Sign in', register: 'Register', usernamePh: 'Username (≥2 chars)', passwordPh: 'Password (≥8 chars)',
    drawioTitle: 'draw.io Diagram Editor', drawioDone: 'Done editing',
  },
};

// 智能体名（双语）
export const AGENT_NAMES = {
  general: { zh: '深哲', en: 'DeepPhilosophy' },
  nietzsche: { zh: '尼采', en: 'Nietzsche' },
};
export const AGENT_SUBS = {
  general: { zh: '通用哲学智能体 · 基于 403 本原典', en: 'General philosophy agent · 403 classics' },
  nietzsche: { zh: '查拉图斯特拉的作者 · 以尼采人格与你交谈', en: 'Author of Zarathustra · speak as Nietzsche' },
};

// 工具名（双语）
export const TOOL_LABELS = {
  search_books: { zh: '检索原典', en: 'Search Texts' },
  get_chapter: { zh: '读取章节', en: 'Read Chapter' },
  get_book_detail: { zh: '查书详情', en: 'Book Detail' },
  list_books: { zh: '筛选书目', en: 'List Books' },
  query_graph: { zh: '查询星丛', en: 'Query Constellation' },
  get_philosopher: { zh: '查哲人资料', en: 'Philosopher Info' },
  get_school: { zh: '查询流派', en: 'School Info' },
  compare_views: { zh: '观点对比', en: 'Compare Views' },
  write_essay: { zh: '撰写作文', en: 'Write Essay' },
  phti_test: { zh: '人格测试', en: 'Personality Test' },
  philosopher_debate: { zh: '哲学辩论', en: 'Philosopher Debate' },
  thought_experiment: { zh: '思想实验', en: 'Thought Experiment' },
  advisor_council: { zh: '智者内阁', en: 'Advisor Council' },
  paper_review: { zh: '论文评审', en: 'Paper Review' },
  generate_image: { zh: '概念生图', en: 'Generate Image' },
  websearch: { zh: '上网搜索', en: 'Web Search' },
  query_database: { zh: '数据库查询', en: 'Database Query' },
  role_play: { zh: '扮演', en: 'Role Play' },
  concept_trace: { zh: '概念溯源', en: 'Concept Trace' },
  conceptual_map: { zh: '概念脑图', en: 'Concept Map' },
  essay_outline: { zh: '论文大纲', en: 'Essay Outline' },
  life_coach: { zh: '人生疏导', en: 'Life Coach' },
  dialectic: { zh: '矛盾分析', en: 'Dialectic' },
  history_timeline: { zh: '时间线', en: 'Timeline' },
  confrontation: { zh: '原文对质', en: 'Confrontation' },
  school_arena: { zh: '流派竞技场', en: 'School Arena' },
  agent_council: { zh: '智能体协作', en: 'Agent Council' },
  philosopher_memory: { zh: '记忆', en: 'Memory' },
  philosopher_period: { zh: '时期切换', en: 'Period' },
  philosopher_style: { zh: '风格', en: 'Style' },
  philosopher_quote: { zh: '引文查证', en: 'Quote' },
  philosopher_graph: { zh: '思想网络', en: 'Thought Network' },
  philosopher_corpus: { zh: '语料回响', en: 'Corpus' },
  philosopher_concepts: { zh: '概念锚定', en: 'Concepts' },
  philosopher_user: { zh: '用户模型', en: 'User Model' },
  socratic_tutor: { zh: '苏格拉底追问', en: 'Socratic Tutor' },
  analyze_argument: { zh: '论证分析', en: 'Argument Analysis' },
  profile: { zh: '哲学画像', en: 'Profile' },
};

export const LANGS = [
  ['zh', '中文'], ['en', 'English'],
];

const LangContext = createContext(null);

export function LangProvider({ children }) {
  const { profile, authFetch } = useAuth();
  const [lang, setLangState] = useState(() => localStorage.getItem('phiagent_lang') || 'zh');

  const setLang = useCallback((l) => {
    localStorage.setItem('phiagent_lang', l);
    setLangState(l);
    if (profile) {
      // 登录用户同步到 profile（供后端语言注入）
      authFetch('/api/auth/profile', {
        method: 'PUT', body: JSON.stringify({ language: l }),
      }).catch(() => {});
    }
  }, [profile, authFetch]);

  // 登录后同步 profile.language（切换/登录/刷新时生效）
  useEffect(() => {
    if (profile?.language && profile.language !== lang) {
      localStorage.setItem('phiagent_lang', profile.language);
      setLangState(profile.language);
    }
  }, [profile?.language]);   // eslint-disable-line react-hooks/exhaustive-deps

  const t = useCallback((key) => (UI[lang] || UI.zh)[key] || UI.zh[key] || key, [lang]);
  const agentName = useCallback((key) => (AGENT_NAMES[key] || {})[lang] || key, [lang]);
  const agentSub = useCallback((key) => (AGENT_SUBS[key] || {})[lang] || '', [lang]);
  const toolLabel = useCallback((key) => (TOOL_LABELS[key] || {})[lang] || key, [lang]);

  return (
    <LangContext.Provider value={{ lang, setLang, t, agentName, agentSub, toolLabel }}>
      {children}
    </LangContext.Provider>
  );
}

export const useLang = () => useContext(LangContext);
