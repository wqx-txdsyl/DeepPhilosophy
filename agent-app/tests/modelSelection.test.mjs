import assert from 'node:assert/strict';
import {LocalConversationStore} from '../src/data/conversationStore.js';
import {createGeneralStream,reduceGeneralEvent} from '../src/data/generalStream.js';

const values=new Map(), storage={getItem:k=>values.get(k),setItem:(k,v)=>values.set(k,v)};
let store=new LocalConversationStore(storage);store.createConversation({conversation_id:'model-fixture'});
for(const [id,label,model]of [['deepseek','DeepSeek','deepseek-flash'],['openai','ChatGPT','gpt-6.1-terra']]){
 const state=reduceGeneralEvent(createGeneralStream(),{type:'done',content:'合成公开答复',complete:true,main_model_invoked:true,
  release:{release_version:'0.1.8',model_provider:id,model_label:label,model}});
 store.appendMessage('model-fixture',{...state,message_id:id,role:'assistant'});
}
const confirmation=reduceGeneralEvent(createGeneralStream(),{type:'done',content:'请说明讨论目标。',complete:true,
 main_model_invoked:false,response_origin:'input_clarification',release:{model_provider:'openai',model_label:'ChatGPT',model:'gpt-6.1-terra'}});
store.appendMessage('model-fixture',{...confirmation,message_id:'confirmation',role:'assistant'});
store=new LocalConversationStore(storage);const messages=store.getConversation('model-fixture').messages;
assert.equal(messages[0].agent_release.model_provider,'deepseek');assert.equal(messages[1].agent_release.model,'gpt-6.1-terra');
assert.equal(messages[2].main_model_invoked,false);assert.equal(messages[2].response_origin,'input_clarification');
assert.notEqual(messages[0].agent_release.model_provider,messages[1].agent_release.model_provider);
console.log('Historical reply models and no-model notices survive storage round trips.');
