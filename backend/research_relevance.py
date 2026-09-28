"""Conservative query matching; eligibility is not expert curation or authority."""
import re

VERSION='lexical-candidate-3'
STOP={'the','and','of','in','on','for','a','an','to','with','from','by','as'}


def assess(query,record):
    title=str(record.get('title') or '')
    if re.fullmatch(r'(?:table of )?contents|contributors|index|copyright|front matter|back matter',title.strip(),re.I):
        return {'version':VERSION,'eligible':False,'reason':'NON_CONTENT_RECORD'}
    terms=list(dict.fromkeys(t.casefold() for t in re.findall(r'\w+',query) if len(t)>=2 and t.casefold() not in STOP))
    heading=' '.join([title,' '.join(a.get('name','') for a in record.get('authors') or [] if isinstance(a,dict)), ' '.join(record.get('aliases') or [])]).casefold()
    abstract=record.get('abstract') or {};abstract=abstract.get('text','') if isinstance(abstract,dict) else ''
    abstract=str(abstract or '').casefold()
    def present(term):
        if re.fullmatch(r'[a-z0-9_]+',term):
            return bool(re.search(r'(?<!\w)'+re.escape(term)+r's?(?!\w)',heading))
        return term in heading
    matched=sum(present(t) for t in terms)
    phrase=re.sub(r'\s+',' ',query.casefold()).strip()
    # Discovery is candidate retrieval, not proof that a paper answers every
    # facet of a long question. Keep two-term queries strict (e.g. free will),
    # but do not require a title to repeat an entire research question.
    needed=min(len(terms),2)
    eligible=bool(terms) and (matched>=needed or (len(phrase)>=6 and phrase in re.sub(r'\s+',' ',abstract)))
    return {'version':VERSION,'eligible':eligible,'reason':'LEXICAL_CANDIDATE' if eligible else 'RELEVANCE_UNVERIFIED','matched_heading_terms':matched,'query_terms':len(terms),
            'coverage': matched / len(terms) if terms else 0, 'required_heading_terms': needed}
