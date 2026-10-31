"""Server-owned credentials; model choice is isolated to each request."""
import os
from contextvars import ContextVar
from dataclasses import dataclass, field

current_provider = ContextVar('phiagent_model_provider', default='deepseek')
PROVIDERS = {'deepseek':'DeepSeek', 'openai':'ChatGPT'}


@dataclass(frozen=True)
class ModelConfig:
    provider: str
    model: str
    api_key: str = field(repr=False)
    base_url: str


def config(provider=None, main=False):
    from routes import agent_llm as legacy
    from agent_release import MANIFEST
    provider = current_provider.get() if provider is None else provider
    if provider not in PROVIDERS: raise ValueError('Unknown model provider')
    if provider == 'openai':
        return ModelConfig(provider,MANIFEST.get('openai_model_default','gpt-6.1-terra'),
                           os.getenv('OPENAI_API_KEY',''),'https://api.openai.com/v1')
    return ModelConfig(provider,(os.getenv('DEEP_MAIN_MODEL') if main else None) or legacy.MODEL,
                       legacy.API_KEY,legacy.API_URL)


def public_metadata():
    c=config(main=True)
    return {'model_provider':c.provider,'model_label':PROVIDERS[c.provider],'model':c.model,
            'model_api':'responses' if c.provider=='openai' else 'chat_completions'}


def catalog(user=None):
    items=[]
    for provider,label in PROVIDERS.items():
        c=config(provider,main=True)
        reason=('not_configured' if not c.api_key else 'login_required' if provider=='openai' and not user
                else 'runtime_unsupported' if provider=='openai' and os.getenv('DEEP_AGENT_RUNTIME','bare')!='bare' else None)
        items.append({'id':provider,'label':label,'model':c.model,'available':reason is None,'reason':reason})
    return {'default':'deepseek','models':items}


def openai_model():
    from langchain_openai import ChatOpenAI
    import httpx
    c=config('openai')
    if not c.api_key: raise ValueError('ChatGPT is not configured')
    return ChatOpenAI(model=c.model,api_key=c.api_key,base_url=c.base_url,
        use_responses_api=True,output_version='responses/v1',reasoning={'effort':'medium'},
        include=['reasoning.encrypted_content'],store=False,max_retries=1,timeout=None,
        default_headers={'Accept-Encoding':'identity'},
        http_client=httpx.Client(timeout=None),http_async_client=httpx.AsyncClient(timeout=None),http_socket_options=())


def visible_text(content):
    """Only public text/refusals, never reasoning or tool arguments."""
    if isinstance(content,str): return content
    if not isinstance(content,list): return ''
    return ''.join(b.get('text','') if b.get('type') in ('text','output_text') and isinstance(b.get('text'),str)
                   else b.get('refusal','') if b.get('type')=='refusal' and isinstance(b.get('refusal'),str) else ''
                   for b in content if isinstance(b,dict))


def _response_body(messages,max_tokens,json_mode=False,tools=None):
    c=config('openai')
    body={'model':c.model,'input':messages,'reasoning':{'effort':'low'},'store':False,
          'max_output_tokens':max(2048,max_tokens)}
    if json_mode:body['text']={'format':{'type':'json_object'}}
    if tools:
        body['tools']=[{'type':'function',**t['function'],'strict':False} if t.get('type')=='function' and 'function' in t else t for t in tools]
    return body


def _completion(response):
    calls=[{'id':o.call_id,'type':'function','function':{'name':o.name,'arguments':o.arguments}}
           for o in response.output if o.type=='function_call']
    return {'model':response.model,'usage':response.usage.model_dump() if response.usage else None,
            'choices':[{'finish_reason':'length' if response.status!='completed' else 'tool_calls' if calls else 'stop',
                        'message':{'content':response.output_text,'tool_calls':calls}}]}


def auxiliary_chat(messages,max_tokens=2000,tools=None):
    from openai import OpenAI
    c=config('openai')
    with OpenAI(api_key=c.api_key,base_url=c.base_url,max_retries=1,timeout=90) as client:
        return _completion(client.responses.create(**_response_body(messages,max_tokens,tools=tools)))


async def auxiliary_json(messages):
    from openai import AsyncOpenAI
    c=config('openai')
    async with AsyncOpenAI(api_key=c.api_key,base_url=c.base_url,max_retries=1,timeout=20) as client:
        return _completion(await client.responses.create(**_response_body(messages,2048,json_mode=True)))


def error_event(exc):
    status=getattr(exc,'status_code',None);code=getattr(exc,'code',None)
    text=('ChatGPT API 额度不足，请检查 OpenAI API 余额。' if code=='insufficient_quota'
          else 'ChatGPT 请求过于频繁，请稍后重试。' if status==429
          else 'ChatGPT 服务认证失败，请联系管理员检查配置。' if status==401
          else 'ChatGPT 模型当前不可用，请检查服务访问权限。' if status in (403,404)
          else 'ChatGPT 暂时未完成回复，请重试。')
    return {'type':'error','code':'openai_'+('insufficient_quota' if code=='insufficient_quota' else 'provider_error'),
            'content':text,'runtime_profile':'bare'}
