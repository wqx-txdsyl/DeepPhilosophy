import { memorySections } from './memoryProfile.js';
const str = value => typeof value === 'string' ? value : '';
const arr = value => Array.isArray(value) ? value : [];
const clip = value => str(value).length>450 ? str(value).slice(0,450)+'…' : str(value);
const LABELS = {about:'个人资料',nickname:'称呼',occupation:'职业或学习阶段',custom_instructions:'回答偏好',
  summary:'摘要',analysis:'分析',conclusion:'结论',arguments:'理由',objections:'异议',response:'回应',answer:'回答',
  recommendations:'建议',questions:'问题',suggestions:'继续探索',steps:'步骤',outline:'提纲',content:'内容',text:'正文',
  description:'说明',claims:'主张',evidence:'依据',concepts:'概念',entities:'对象',relations:'关联',edges:'关联',
  comparison:'对照',views:'立场',debate:'讨论',period:'时期',identity:'人物定位',signature:'表达特征',
  dimensions:'特点',speech_markers:'表达习惯',results:'结果',items:'条目',books:'书目',title:'标题',name:'名称',
  author:'作者',year:'年份',chapters:'章节',total:'总数',count:'数量',status:'状态',success:'结果',found:'是否找到'};
export const toolFieldLabel = (key,zh) => zh ? (LABELS[key] || key.replaceAll('_',' ')) : key.replaceAll('_',' ');
const INTERNAL = /^(?:_.*|id|book_id|chapter_idx|source_id|evidence_id|memory_id|conversation_id|message_id|model|usage|trace|debug|provider_errors|cache_key|cached|offline_mode|note|error|token|api_key|password|authorization|secret)$/i;

export function extraToolView(name,data,view,zh,item,safeUrl) {
  const say=(a,b)=>zh?a:b;
  const doc=(title,body)=>{if(str(body).trim())view.documents.push({title,text:body});};
  if(name==='recall_account_memory') {
    const settings=data.user_settings||{};
    const p=Object.entries(settings).filter(([,v])=>str(v).trim()).map(([k,v])=>`## ${toolFieldLabel(k,zh)}\n${v}`).join('\n\n');
    doc(say('你填写的个性化资料','Your personalization'),p);
    doc(say(data.memory_profile_user_edited?'你更正的记忆摘要':'对话记忆摘要',data.memory_profile_user_edited?'Your edited memory summary':'Conversation memory summary'),data.memory_profile);
    view.items=arr(data.memories).map(m=>({title:say('你明确保存的信息','Explicitly saved information'),excerpt:str(m.text)}));
    view.headline=view.documents.length||view.items.length?say('已读取账号记忆','Account memory loaded'):say('还没有保存的记忆','No saved memory yet');
    if(str(data.memory_profile).trim())view.meta.push(say(`${memorySections(data.memory_profile).length} 个摘要主题`,`${memorySections(data.memory_profile).length} summary topics`));
    if(view.items.length)view.meta.push(say(`${view.items.length} 条明确记忆`,`${view.items.length} explicit memories`));
    return true;
  }
  if(name==='remember_account_memory') {
    view.headline=data.memory?.memory_id?say('已保存这条记忆','Memory saved'):say('未确认保存结果','Save not confirmed');
    doc('',data.memory?.text);return true;
  }
  if(name==='forget_account_memory') {
    view.headline=data.deleted===true?say('已删除这条记忆','Memory deleted'):data.deleted===false?say('未找到对应记忆','No matching memory'):say('删除结果尚未确认','Deletion not confirmed');return true;
  }
  if(name==='search_account_history') {
    view.items=arr(data.results).map(r=>({title:str(r.title)||say('历史对话','Past conversation'),
      url:r.conversation_id?`/agent/c/${encodeURIComponent(r.conversation_id)}`:null,
      meta:r.role==='user'?say('你的提问','Your question'):say('回答','Answer'),excerpt:clip(r.excerpt)}));
    view.headline=view.items.length?say(`找到 ${view.items.length} 条相关对话`,`Found ${view.items.length} related messages`):say('没有找到相关对话','No related conversations found');return true;
  }
  if(name==='read_account_conversation') {
    view.headline=str(data.title)||say('已读取历史对话','Conversation loaded');
    view.items=arr(data.messages).map(m=>({title:m.role==='user'?say('你','You'):say('回答','Answer'),excerpt:str(m.content)}));
    view.meta.push(say(`${view.items.length} 条消息`,`${view.items.length} messages`));return true;
  }
  if(name==='philosopher_memory') {
    view.headline=say('哲学家生平与思想线索','Biographical and intellectual context');
    view.items=arr(data.memories).map(m=>({title:str(m.event)||str(m.title),meta:[m.year,m.period].filter(Boolean).join(' · '),excerpt:str(m.significance||m.text)}));
    if(!view.items.length)view.headline=say('没有找到相关生平条目','No related biographical entries');return true;
  }
  if(['philosopher_quote','philosopher_corpus'].includes(name)) {
    view.items=arr(data.quotes||data.echoes).map(item);
    view.headline=view.items.length?say(`找到 ${view.items.length} 段著作材料`,`Found ${view.items.length} work passages`):say('本次未找到相关著作片段','No related passage found');
    view.note=say('当前返回的是检索片段；可继续读取上下文。','These are search passages; read the surrounding context next.');return true;
  }
  if(name==='philosopher_concepts') {
    view.headline=say('概念释义','Concept explanations');view.items=arr(data.concepts).map(c=>({title:str(c.term),excerpt:str(c.canon||c.definition)}));return true;
  }
  if(name==='philosopher_user') {
    view.headline=say('讲解参考：常见误解','Teaching reference: common misconceptions');
    view.items=arr(data.likely_misconceptions).map(m=>({title:str(m.claim),excerpt:str(m.fact)}));
    view.note=say('这些是资料库中的常见误解，不是对当前用户身份或能力的判断。','These are general misconceptions, not conclusions about this user.');return true;
  }
  if(name==='get_book_detail') {
    view.headline=str(data.title||data.book_title)||say('书籍信息','Book details');
    view.meta.push(...[str(data.author),str(data.publisher)].filter(Boolean));
    doc(say('简介','About'),data.description||data.summary);
    view.items=arr(data.chapters||data.toc).map(item);
    if(Number.isInteger(data.readable_chapter_count))view.meta.push(say(`${data.readable_chapter_count} 个可读章节`,`${data.readable_chapter_count} readable chapters`));
    if(data.has_more)view.note=say('当前只显示部分目录，后面还有章节。','Only part of the contents is shown; more chapters follow.');
    return true;
  }
  if(name==='list_books') {
    view.items=arr(Array.isArray(data)?data:data.books||data.results).map(item);
    view.headline=say(`返回 ${view.items.length} 本书`,`Returned ${view.items.length} books`);return true;
  }
  if(name==='generate_image') {
    const url=/^\/agent_images\/[\w.-]+$/.test(data.image_url||'')?data.image_url:safeUrl(data.image_url);
    view.headline=url?say('图片已生成','Image generated'):say('未取得图片地址','No image address returned');
    if(url)view.items=[{title:say('查看生成图片','View generated image'),url,excerpt:str(data.prompt)}];
    if(data.size)view.meta.push(String(data.size));
    return true;
  }
  return false;
}

// A readable fallback for future tools: meaningful fields become prose/cards,
// while the exact original return remains available separately.
export function genericToolView(data,view,zh,item) {
  if(Array.isArray(data)) {view.headline=zh?`返回 ${data.length} 条内容`:`Returned ${data.length} items`;return;}
  if(str(data.summary).length>160) {
    view.documents.push({title:zh?'摘要':'Summary',text:data.summary});
    view.headline=zh?'工具已返回结果':'Tool result returned';
  }
  for(const [key,value] of Object.entries(data)) {
    if(INTERNAL.test(key) || ['summary','message','note'].includes(key))continue;
    const label=toolFieldLabel(key,zh);
    if(typeof value==='string' && value.trim())view.documents.push({title:label,text:value});
    else if(typeof value==='number'||typeof value==='boolean')view.meta.push(`${label}：${value}`);
    else if(Array.isArray(value)) {
      if(value.length && !['results','books','items'].includes(key))view.items.push(...value.map(v=>typeof v==='object'&&v!==null?item(v):({title:label,excerpt:String(v)})));
    } else if(value && typeof value==='object') {
      const content=Object.entries(value).filter(([k,v])=>!INTERNAL.test(k)&&['string','number','boolean'].includes(typeof v)).map(([k,v])=>`${toolFieldLabel(k,zh)}：${v}`).join('\n');
      if(content)view.documents.push({title:label,text:content});
    }
  }
  if(view.headline===(zh?'工具已返回结果':'Tool result returned'))view.headline=zh?`已返回 ${view.documents.length+view.items.length+view.meta.length} 项内容`:`Returned ${view.documents.length+view.items.length+view.meta.length} details`;
}
