"""Run: python -m exercises.migration"""
import asyncio
from exercises.advanced import unique_books, chunk_text

async def delayed(name):
    await asyncio.sleep(0.01)
    return name

async def main():
    source = [{'id': 'a', 'title': '自由'}, {'id': 'a', 'title': '另一个标题'}]
    print('去重：', unique_books(source))
    print('文本窗口：', chunk_text('自由与责任需要分别讨论', size=5, overlap=1))
    print('并发结果：', await asyncio.gather(delayed('A'), delayed('B')))

if __name__ == '__main__':
    asyncio.run(main())
