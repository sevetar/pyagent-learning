"""
测试模块
"""
import pytest


@pytest.fixture
def sample_ticket_data():
    return {
        "id": 1001,
        "user_id": 1,
        "device_id": 501,
        "device_name": "变频器A",
        "title": "变频器报警E001",
        "symptom": "设备开机后显示E001报警代码，无法启动",
        "status": "DONE",
        "priority": "HIGH",
    }


@pytest.fixture
def sample_process_data():
    return {
        "ticket_id": 1001,
        "operator_id": 10,
        "operator_role": "REPAIRMAN",
        "action": "REPAIR",
        "cause": "主板电容老化导致电压不稳",
        "solution": "更换主板电容，清洗电路板，重新校准参数",
        "result": "SUCCESS",
    }


def test_chunk_splitting(sample_ticket_data, sample_process_data):
    """测试chunk拆分逻辑"""
    from flowfix.rag.ingestion import RagIngester, ChunkType

    ingester = RagIngester()
    chunks = ingester.split_ticket_to_chunks(sample_ticket_data, sample_process_data)

    assert len(chunks) == 3
    assert any(c["chunk_type"] == ChunkType.SYMPTOM for c in chunks)
    assert any(c["chunk_type"] == ChunkType.CAUSE for c in chunks)
    assert any(c["chunk_type"] == ChunkType.SOLUTION for c in chunks)


def test_routing_decision_values():
    """测试路由决策枚举"""
    from flowfix.agent.dispatcher import RoutingDecision

    assert RoutingDecision.AUTO.value == "AUTO"
    assert RoutingDecision.ASSIST.value == "ASSIST"
    assert RoutingDecision.MANUAL.value == "MANUAL"
