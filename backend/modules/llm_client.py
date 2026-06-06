"""
DeepSeek API 客户端 —— 通过 OpenAI 兼容接口调用 DeepSeek 大模型
"""
import time
from openai import OpenAI

from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL


class DeepSeekClient:
    """DeepSeek API 客户端，支持对话生成与重试机制"""

    def __init__(self, api_key: str | None = None):
        """
        初始化 DeepSeek 客户端

        Args:
            api_key: DeepSeek API 密钥，不传则从 config 读取
        """
        self.api_key = api_key or DEEPSEEK_API_KEY
        self.model = DEEPSEEK_MODEL

        if self.api_key == "your-api-key-here":
            raise ValueError(
                "请先设置 DEEPSEEK_API_KEY！\n"
                "方式1: 在 config.py 中修改 DEEPSEEK_API_KEY 的值\n"
                "方式2: 设置环境变量 export DEEPSEEK_API_KEY=sk-xxx"
            )

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=DEEPSEEK_BASE_URL,
        )

    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        max_retries: int = 3,
    ) -> str:
        """
        调用 DeepSeek Chat API 进行对话

        Args:
            messages: 对话消息列表 [{"role": "user", "content": "..."}]
            temperature: 生成随机性（0-1）
            max_tokens: 最大输出长度
            max_retries: API 失败最大重试次数

        Returns:
            DeepSeek 生成的回答文本
        """
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=False,
                )
                return response.choices[0].message.content

            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # 指数退避：1s, 2s, 4s
                    print(f"  ⚠️ API调用失败 (尝试 {attempt+1}/{max_retries}): {e}")
                    print(f"  🔄 {wait_time}秒后重试...")
                    time.sleep(wait_time)
                else:
                    raise RuntimeError(
                        f"DeepSeek API 调用失败（已重试{max_retries}次）: {e}"
                    )

    def test_connection(self) -> bool:
        """
        测试 API 连接是否正常

        Returns:
            True 表示连接成功
        """
        try:
            response = self.chat(
                messages=[{"role": "user", "content": "你好，请用一句话介绍你自己。"}],
                max_tokens=50,
            )
            print(f"  ✅ DeepSeek API 连接成功！")
            print(f"  回复: {response}")
            return True
        except Exception as e:
            print(f"  ❌ DeepSeek API 连接失败: {e}")
            return False
