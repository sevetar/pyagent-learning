"""
测试 AutoDispatcher Agent 的工具调用功能
"""
import asyncio
from flowfix.agent import get_auto_dispatcher


async def test_dispatch_with_tools():
    """测试 agent 自主调用工具进行派单决策"""

    dispatcher = get_auto_dispatcher()

    # 测试场景：变频器故障，提供设备ID
    print("=" * 80)
    print("测试场景：变频器频繁报警故障")
    print("=" * 80)

    result = await dispatcher.dispatch(
        ticket_id=12345,
        device_type="变频器",
        fault_type="频繁报警",
        symptom="设备运行过程中频繁出现过载报警，每隔10分钟报警一次",
        priority="HIGH",
        device_id=1001,  # 提供设备ID，agent应该会调用 get_device_fault_history
    )

    print("\n派单结果：")
    print(f"  维修员ID: {result.repairman_id}")
    print(f"  维修员姓名: {result.repairman_name}")
    print(f"  选择理由: {result.reason}")
    print(f"  置信度: {result.confidence}")
    print("=" * 80)


async def test_dispatch_without_device_id():
    """测试没有设备ID的场景"""

    dispatcher = get_auto_dispatcher()

    print("\n" + "=" * 80)
    print("测试场景：电机异响，无设备ID")
    print("=" * 80)

    result = await dispatcher.dispatch(
        ticket_id=12346,
        device_type="电机",
        fault_type="异响",
        symptom="电机启动后有明显的异响，疑似轴承磨损",
        priority="MEDIUM",
        device_id=None,  # 不提供设备ID，agent应该会调用 query_similar_cases
    )

    print("\n派单结果：")
    print(f"  维修员ID: {result.repairman_id}")
    print(f"  维修员姓名: {result.repairman_name}")
    print(f"  选择理由: {result.reason}")
    print(f"  置信度: {result.confidence}")
    print("=" * 80)


async def main():
    """主测试函数"""
    print("\n开始测试 AutoDispatcher Agent 工具调用功能\n")

    try:
        # 测试1：有设备ID的场景
        await test_dispatch_with_tools()

        # 测试2：无设备ID的场景
        await test_dispatch_without_device_id()

        print("\n✅ 测试完成！")
        print("\n观察要点：")
        print("1. Agent 是否自主调用了工具（get_device_fault_history, query_similar_cases, check_repairman_realtime_load）")
        print("2. Agent 是否进行了多步推理（观察 verbose 输出）")
        print("3. 最终派单决策是否综合了工具返回的信息")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
