"""Mechanical coverage of source text actually returned in this invocation.

It cannot decide whether a philosophical argument or requested section is done.
Different books, chapters and content fingerprints never share a coverage slot.
"""
class ReadingCoverage:
    def __init__(self):
        self.ranges = {}

    def observe(self, result):
        if not isinstance(result,dict) or result.get('error'):
            return result
        if isinstance(result.get('matches'),list):
            return {**result,'matches':[self.observe(item) for item in result['matches']]}
        keys=('excerpt_start','excerpt_end','chapter_text_length')
        if not all(type(result.get(k)) is int for k in keys) or not result.get('chapter_content_sha256'):
            return result
        start,end,length=(result[k] for k in keys)
        if not 0<=start<=end<=length or len(result.get('text',''))!=end-start:
            return result
        key=(result.get('book_id'),result.get('chapter_idx'),result['chapter_content_sha256'])
        spans=sorted(self.ranges.get(key,[])+[(start,end)])
        merged=[]
        for a,b in spans:
            if merged and a<=merged[-1][1]:merged[-1]=(merged[-1][0],max(b,merged[-1][1]))
            else:merged.append((a,b))
        self.ranges[key]=merged
        return {**result,'reading_progress':{
            'scope':'same_book_chapter_and_content_hash',
            'returned_ranges':[list(span) for span in merged],
            'covered_characters':sum(b-a for a,b in merged),
            'whole_chapter_read':merged==[(0,length)],
            'gaps_between_returned_ranges':max(0,len(merged)-1),
            'note':'只合并本次调用链实际返回的文字。whole_chapter_read仅指整章；目标节或论证是否读全须依据实际文本边界，不能仅凭has_more否定目标已读完。'}}
