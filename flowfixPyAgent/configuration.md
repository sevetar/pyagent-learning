llm配置# OpenAI API 配置（通过灵雅中转）
OPENAI_API_KEY=sk-1cI77PdKVyxVsxLY1NXwJZRMGK6SJtBBvx3mHLse0tSfHQLE
OPENAI_API_BASE=https://api.lingyaai.cn/v1
OPENAI_MODEL=gpt-4o-mini
# 模型参数
MODEL_TEMPERATURE=0.7
MODEL_MAX_TOKENS=2000
MODEL_TIMEOUT=30

# 向量模型
text-embedding-3-small
api和地址都和llm配置一致


mysql配置
      url: jdbc:mysql://localhost:3306/pg_agent
      username: root
      password: 123456

pgvector:
  database: postgres
  host: localhost
  port: 5432
  user: root
  password: 123456
  
