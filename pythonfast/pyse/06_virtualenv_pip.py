"""
虚拟环境 & 包管理
==================
Python项目隔离依赖的神器，类似Maven/Gradle但更轻量

核心概念：
- venv: Python内置虚拟环境
- pip: 包管理器（类似Maven中央仓库）
- requirements.txt: 依赖清单
"""

# ========== 1. 虚拟环境 ==========
"""
# 创建虚拟环境（类似Java的maven wrapper）
python -m venv myenv

# 激活（Windows）
myenv\Scripts\activate

# 激活（Mac/Linux）
source myenv/bin/activate

# 退出
deactivate
"""

# ========== 2. pip常用命令 ==========
"""
# 安装包
pip install requests
pip install requests==2.28.0  # 指定版本
pip install "requests>=2.0"   # 最小版本

# 卸载
pip uninstall requests

# 查看已安装
pip list
pip freeze

# 导出依赖
pip freeze > requirements.txt

# 从requirements安装
pip install -r requirements.txt

# 常用镜像（国内加速）
pip install requests -i https://pypi.tuna.tsinghua.edu.cn/simple
"""

# ========== 3. 常用第三方库 ==========
"""
# Web请求
requests      # 类似Java的OkHttp/HttpClient

# Web框架
flask         # 轻量级，类似Servlet
fastapi       # 现代高性能API框架

# 数据处理
pandas        # 类似Java的Apache Commons CSV + 更多功能
numpy         # 数值计算，类似Java的ND4J

# AI/ML
openai        # OpenAI API
langchain     # LLM应用框架
langchain-core
langchain-openai
anthropic     # Claude API

# 异步
asyncio       # 内置异步编程
aiohttp       # 异步HTTP

# 工具
python-dotenv # 环境变量
pydantic      # 数据验证
"""

# ========== 4. 项目结构示例 ==========
"""
myproject/
├── venv/              # 虚拟环境
├── src/               # 源代码
│   ├── __init__.py   # 包标识
│   └── main.py
├── tests/             # 测试
├── requirements.txt   # 依赖
└── README.md
"""

# ========== 5. __init__.py 作用 ==========
"""
# 目录有__init__.py才是Python包
# 可以为空，也可以在其中写初始化代码
"""

# ========== 6. 相对导入 vs 绝对导入 ==========
# 绝对导入（推荐）
from package.module import function

# 相对导入（包内使用）
from .module import function
from ..package.module import function

# ========== 7. if __name__ == "__main__" ==========
"""
类似Java的public static void main(String[] args)
只有直接运行脚本时为True，被import时不执行
"""

def main():
    print("主程序逻辑")


if __name__ == "__main__":
    # 这段代码只在直接运行时执行
    # import时不会执行
    main()
    print("作为主程序运行")

# 演示：保存为demo.py
# python demo.py  -> 输出两行
# import demo    -> 只输出"作为主程序运行"

print("\n=== 环境配置完成 ===")
print("安装第一个包试试: pip install requests")
