"""项目配置管理"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Settings:
    """应用配置类"""

    # OpenAI API 配置（支持中转接口）
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_API_BASE: str = os.getenv("OPENAI_API_BASE", "https://api.lingyaai.cn/v1")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # 模型参数
    MODEL_TEMPERATURE: float = float(os.getenv("MODEL_TEMPERATURE", "0.7"))
    MODEL_MAX_TOKENS: int = int(os.getenv("MODEL_MAX_TOKENS", "2000"))
    MODEL_TIMEOUT: int = int(os.getenv("MODEL_TIMEOUT", "30"))

    def validate(self) -> bool:
        """验证配置是否完整"""
        if not self.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY 未设置，请在 .env 文件中配置")
        return True


# 创建全局配置实例
settings = Settings()
