"""
RAG功能集成测试
验证向量检索和问答功能
"""
import sys
sys.path.insert(0, "src")

from flowfix.rag import get_rag_retriever, get_rag_ingester
from flowfix.db import get_mysql_session, Ticket, TicketProcess
from flowfix.agent.dispatcher import get_intelligent_router, RoutingDecision
from flowfix.agent.repair_dispatcher import get_auto_dispatcher


async def test_vector_search():
    """测试向量检索"""
    print("\n" + "=" * 50)
    print("测试1: 向量检索")
    print("=" * 50)

    retriever = get_rag_retriever()

    # 测试查询 - 查找与"报警代码无法启动"相关的问题
    query = "设备开机后报警E001，无法启动运行"
    print(f"\n查询: {query}")

    results = await retriever.search(query, top_k=3)

    print(f"\n检索到 {len(results)} 条结果:")
    for i, r in enumerate(results):
        print(f"\n--- 结果 {i+1} ---")
        print(f"工单ID: {r['ticket_id']}")
        print(f"设备: {r['device_name']}")
        print(f"类型: {r['chunk_type']}")
        print(f"内容: {r['content'][:50]}...")
        print(f"相似度: {r['similarity']:.4f}")

    # 测试构建上下文
    context = retriever.build_context(results, max_chunks=3)
    print(f"\n构建的上下文:\n{context[:200]}...")

    return len(results) > 0


async def test_routing_decision():
    """测试智能分流"""
    print("\n" + "=" * 50)
    print("测试2: 智能分流决策")
    print("=" * 50)

    dispatcher = get_intelligent_router()

    test_queries = [
        ("空调不制冷了", "简单咨询"),
        ("设备报警E001，无法启动，怎么处理？", "需要建议"),
        ("变频器坏了，整个生产线都停了", "紧急工单"),
    ]

    for query, desc in test_queries:
        print(f"\n查询 [{desc}]: {query}")
        result = await dispatcher.decide(query)
        print(f"决策: {result['decision']}")
        print(f"置信度: {result.get('confidence', 'N/A')}")
        print(f"原因: {result.get('reasoning', 'N/A')[:50] if result.get('reasoning') else 'N/A'}...")


async def test_repair_dispatch():
    """测试维修员派单"""
    print("\n" + "=" * 50)
    print("测试3: 维修员自动派单")
    print("=" * 50)

    dispatcher = get_auto_dispatcher()

    # 测试派单场景
    print(f"\n工单信息: 变频器A, 报警E001, HIGH")
    result = await dispatcher.dispatch(
        ticket_id=1001,
        device_type="变频器",
        fault_type="报警E001",
        symptom="设备开机后显示E001报警代码，无法启动",
        priority="HIGH"
    )

    print(f"\n派单结果:")
    print(f"  推荐维修员ID: {result.repairman_id}")
    print(f"  维修员名称: {result.repairman_name}")
    print(f"  派单原因: {result.reason}")


def verify_data():
    """验证数据库数据"""
    print("\n" + "=" * 50)
    print("数据验证")
    print("=" * 50)

    # MySQL数据
    with get_mysql_session() as session:
        tickets = session.query(Ticket).all()
        print(f"\nMySQL工单数: {len(tickets)}")
        for t in tickets:
            print(f"  - 工单{t.id}: {t.title} ({t.status})")

    # 向量数据
    from flowfix.db import get_pgvector_connection
    with get_pgvector_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM fault_knowledge")
            count = cur.fetchone()[0]
            print(f"\nPostgreSQL向量记录数: {count}")


def main():
    print("=" * 50)
    print("FlowFix RAG 功能集成测试")
    print("=" * 50)

    # 验证数据
    verify_data()

    # 测试向量检索
    import asyncio
    search_ok = asyncio.run(test_vector_search())
    if search_ok:
        print("\n[OK] 向量检索测试通过")
    else:
        print("\n[FAIL] 向量检索测试失败")

    # 测试智能分流
    import asyncio
    asyncio.run(test_routing_decision())
    print("\n[OK] 智能分流测试完成")

    # 测试维修员派单
    import asyncio
    asyncio.run(test_repair_dispatch())
    print("\n[OK] 自动派单测试完成")

    print("\n" + "=" * 50)
    print("所有测试完成!")
    print("=" * 50)


if __name__ == "__main__":
    main()
