"""Soul personas retain primary-text tools while sharing the main stream protocol."""
import hashlib
from soul_agents import soul_prompt
from soul_agent_tools import PrimaryTexts


async def stream_soul_agent(question, history, key, language='zh', custom_instructions=None,
                            conversation_id=None, message_id=None):
    from deep_bare_agent import stream_bare_agent
    texts = PrimaryTexts(key)

    class Persona:
        prompt_version = 'soul-shared-1'

        def system_text(self, language, question):
            return soul_prompt(key, language)

        async def tools(self):
            return texts.tools()

        def citations(self, calls, answer, language):
            return used_citations(texts.reads, answer), None

    events = stream_bare_agent(question, history, language=language,
        custom_instructions=custom_instructions, conversation_id=conversation_id,
        message_id=message_id, agent=key, _persona=Persona())
    try:
        async for event in events:
            if event['type'] == 'done':
                event = {**event, 'agent_id':key, 'status':'preview',
                         'primary_passages_read':len(texts.reads)}
            yield event
    finally:
        await events.aclose()


def used_citations(reads, answer):
    """Show only actually read passages whose label or URL occurs in the answer."""
    citations = {}
    for read in reads:
        if read.get('book_id') and (read.get('citation_label', '\x00') in answer
                                   or f'《{read["book_title"]}》' in answer):
            key = (read['book_id'], read['chapter_idx'])
            citations[key] = {'book': read['book_title'], 'chapter': read['chapter_title'],
                              'evidence_id': f'soul-primary-{read["book_id"]}-{read["chapter_idx"]}',
                              'book_id': read['book_id'], 'chapter_idx': read['chapter_idx'],
                              'source_type': read['source_type'], 'access_level': 'PASSAGE_READ',
                              'used': True, 'verified': False, 'excerpt': read['text'][:700]}
        elif read.get('url') and read['url'] in answer:
            citations[read['url']] = {'title': read.get('title'), 'url': read['url'],
                                      'evidence_id': 'soul-web-' + hashlib.sha256(read['url'].encode()).hexdigest()[:16],
                                      'source_type': 'web', 'access_level': 'WEB_PASSAGE_READ',
                                      'source_status': read.get('source_status'),
                                      'used': True, 'verified': False, 'excerpt': read['text'][:700]}
    return list(citations.values())
