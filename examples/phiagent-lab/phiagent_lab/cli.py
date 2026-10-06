import asyncio
from phiagent_lab.engine import build_graph, initial_state
from phiagent_lab.model import build_model

async def main():
    graph = build_graph(build_model())
    history = []
    while True:
        question = input("你（输入 /quit 退出）：").strip()
        if question == "/quit":
            return
        if not question:
            continue
        result = await graph.ainvoke(initial_state(question, history[-12:]))
        print("PhiAgent Lab：", result["answer"])
        history += [{"role": "user", "content": question},
                    {"role": "assistant", "content": result["answer"]}]

if __name__ == "__main__":
    asyncio.run(main())
