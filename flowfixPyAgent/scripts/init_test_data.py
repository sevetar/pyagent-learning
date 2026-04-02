"""
初始化测试数据脚本
创建MySQL表、PostgreSQL/pgvector表，并插入测试数据
"""
import sys
sys.path.insert(0, "src")

import pymysql
import psycopg2
from flowfix.config import get_settings
from flowfix.db import init_mysql_tables, init_vector_tables, get_mysql_session
from flowfix.db.models import Ticket, TicketProcess, TicketLog, Repairman
from flowfix.db.vector_db import get_pgvector_connection
from flowfix.rag import get_rag_ingester
from datetime import datetime

settings = get_settings()


def create_mysql_database():
    """创建MySQL数据库"""
    print("正在创建MySQL数据库...")
    conn = pymysql.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_user,
        password=settings.mysql_password,
    )
    try:
        with conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS {settings.mysql_database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.commit()
        print(f"MySQL数据库 '{settings.mysql_database}' 创建完成")
    finally:
        conn.close()


def create_mysql_tables():
    """创建MySQL表"""
    print("正在创建MySQL表...")
    init_mysql_tables()
    print("MySQL表创建完成")


def create_postgres_tables():
    """创建PostgreSQL/pgvector表"""
    print("正在创建PostgreSQL/pgvector表...")
    # 启用pgvector扩展
    with get_pgvector_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        conn.commit()
    init_vector_tables()
    print("PostgreSQL表创建完成")


def insert_test_data():
    """插入测试数据"""
    print("正在插入测试数据...")

    with get_mysql_session() as session:
        # 插入维修员
        repairmen = [
            Repairman(
                id=1,
                name="张三",
                skill_tags=["变频器", "电机", "PLC"],
                current_load=2,
                avg处理时长=45,
                is_available="true"
            ),
            Repairman(
                id=2,
                name="李四",
                skill_tags=["空调", "制冷", "压缩机"],
                current_load=1,
                avg处理时长=60,
                is_available="true"
            ),
            Repairman(
                id=3,
                name="王五",
                skill_tags=["变频器", "电源", "UPS"],
                current_load=3,
                avg处理时长=30,
                is_available="true"
            ),
        ]

        for r in repairmen:
            existing = session.query(Repairman).filter(Repairman.id == r.id).first()
            if not existing:
                session.add(r)

        # 插入工单
        tickets = [
            Ticket(
                id=1001,
                user_id=1,
                device_id=501,
                device_name="变频器A",
                title="变频器报警E001",
                symptom="设备开机后显示E001报警代码，无法启动运行",
                status="DONE",
                priority="HIGH",
                assigned_to=1
            ),
            Ticket(
                id=1002,
                user_id=2,
                device_id=502,
                device_name="空调机组B",
                title="空调不制冷",
                symptom="空调开机后不制冷，显示故障代码F3",
                status="DONE",
                priority="MEDIUM",
                assigned_to=2
            ),
            Ticket(
                id=1003,
                user_id=1,
                device_id=503,
                device_name="PLC控制器C",
                title="PLC通讯故障",
                symptom="PLC与上位机通讯中断，检查网线连接正常",
                status="DONE",
                priority="HIGH",
                assigned_to=1
            ),
        ]

        for t in tickets:
            existing = session.query(Ticket).filter(Ticket.id == t.id).first()
            if not existing:
                session.add(t)

        # 插入处理记录
        processes = [
            TicketProcess(
                id=2001,
                ticket_id=1001,
                operator_id=1,
                operator_role="REPAIRMAN",
                action="REPAIR",
                cause="主板电容老化导致电压不稳",
                solution="更换主板电容，清洗电路板，重新校准参数",
                result="SUCCESS",
                remark="已完全修复"
            ),
            TicketProcess(
                id=2002,
                ticket_id=1002,
                operator_id=2,
                operator_role="REPAIRMAN",
                action="REPAIR",
                cause="冷凝器散热不良导致压缩机过载保护",
                solution="清洗冷凝器散热片，补充制冷剂，调整保护阈值",
                result="SUCCESS",
                remark="夏季高负荷常见问题"
            ),
            TicketProcess(
                id=2003,
                ticket_id=1003,
                operator_id=1,
                operator_role="REPAIRMAN",
                action="REPAIR",
                cause="PLC固件版本不兼容导致通讯协议握手失败",
                solution="升级PLC固件至最新版本，重新配置通讯参数",
                result="SUCCESS",
                remark="需定期检查固件更新"
            ),
        ]

        for p in processes:
            existing = session.query(TicketProcess).filter(TicketProcess.id == p.id).first()
            if not existing:
                session.add(p)

        # 插入流转日志
        logs = [
            TicketLog(
                ticket_id=1001,
                from_status=None,
                to_status="CREATED",
                operator_id=1,
                event_type="CREATE",
                remark="用户提交工单"
            ),
            TicketLog(
                ticket_id=1001,
                from_status="CREATED",
                to_status="ASSIGNED",
                operator_id=1,
                event_type="ASSIGN",
                remark="分配给张三"
            ),
            TicketLog(
                ticket_id=1001,
                from_status="ASSIGNED",
                to_status="DONE",
                operator_id=1,
                event_type="FINISH",
                remark="维修完成"
            ),
        ]

        for l in logs:
            session.add(l)

        session.commit()
        print("测试数据插入完成")


def ingest_to_vector():
    """将测试数据入库到向量数据库"""
    print("正在将工单数据入库到向量数据库...")

    ingester = get_rag_ingester()

    for ticket_id in [1001, 1002, 1003]:
        print(f"正在入库工单 {ticket_id}...")
        result = ingester.ingest_ticket(ticket_id)
        print(f"工单 {ticket_id} 入库结果: {result}")

    print("向量数据入库完成")


def verify_data():
    """验证数据"""
    print("\n" + "=" * 50)
    print("验证数据...")
    print("=" * 50)

    # 验证MySQL数据
    with get_mysql_session() as session:
        ticket_count = session.query(Ticket).count()
        process_count = session.query(TicketProcess).count()
        repairman_count = session.query(Repairman).count()

        print(f"MySQL数据:")
        print(f"  - 工单数: {ticket_count}")
        print(f"  - 处理记录数: {process_count}")
        print(f"  - 维修员数: {repairman_count}")

    # 验证向量数据
    with get_pgvector_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM fault_knowledge")
            vector_count = cur.fetchone()[0]
            print(f"\nPostgreSQL/pgvector数据:")
            print(f"  - 向量记录数: {vector_count}")

            # 显示部分向量数据
            cur.execute("SELECT ticket_id, chunk_type, content FROM fault_knowledge LIMIT 5")
            rows = cur.fetchall()
            print(f"\n向量数据示例:")
            for row in rows:
                print(f"  - 工单{row[0]}, 类型:{row[1]}, 内容:{row[2][:30]}...")

    print("\n验证完成!")


def main():
    print("=" * 50)
    print("FlowFix AI Agent 初始化测试数据")
    print("=" * 50)

    # 0. 创建MySQL数据库
    create_mysql_database()

    # 1. 创建表
    create_mysql_tables()
    create_postgres_tables()

    # 2. 插入测试数据
    insert_test_data()

    # 3. 入库到向量数据库
    ingest_to_vector()

    # 4. 验证数据
    verify_data()

    print("=" * 50)
    print("初始化完成！")
    print("=" * 50)


if __name__ == "__main__":
    main()
