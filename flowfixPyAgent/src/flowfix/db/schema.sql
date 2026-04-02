-- FlowFix 数据库初始化脚本
-- 1. MySQL 表结构

-- 工单主表
CREATE TABLE IF NOT EXISTS ticket (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '工单ID',
    user_id BIGINT NOT NULL COMMENT '用户ID',
    device_id BIGINT COMMENT '设备ID',
    device_name VARCHAR(100) COMMENT '设备名称',
    title VARCHAR(255) COMMENT '工单标题',
    symptom TEXT COMMENT '故障现象（用户描述）',
    status VARCHAR(50) NOT NULL COMMENT '状态（CREATED / APPROVED / ASSIGNED / PROCESSING / DONE / CLOSED）',
    priority VARCHAR(20) DEFAULT 'MEDIUM' COMMENT '优先级（LOW / MEDIUM / HIGH）',
    assigned_to BIGINT COMMENT '当前处理人（维修员ID）',
    version INT DEFAULT 0 COMMENT '乐观锁版本号',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_device_id (device_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工单主表';

-- 工单处理记录表
CREATE TABLE IF NOT EXISTS ticket_process (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '处理记录ID',
    ticket_id BIGINT NOT NULL COMMENT '工单ID',
    operator_id BIGINT NOT NULL COMMENT '操作人ID',
    operator_role VARCHAR(50) COMMENT '角色（USER / ADMIN / REPAIRMAN）',
    action VARCHAR(50) NOT NULL COMMENT '操作类型（CREATE / APPROVE / ASSIGN / REPAIR / CLOSE）',
    cause TEXT COMMENT '故障原因（维修员填写）',
    solution TEXT COMMENT '维修方案',
    result VARCHAR(50) COMMENT '处理结果（SUCCESS / FAIL）',
    remark TEXT COMMENT '备注信息',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ticket_id (ticket_id),
    INDEX idx_operator_id (operator_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工单处理记录表';

-- 工单流转日志表
CREATE TABLE IF NOT EXISTS ticket_log (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '日志ID',
    ticket_id BIGINT NOT NULL COMMENT '工单ID',
    from_status VARCHAR(50) COMMENT '变更前状态',
    to_status VARCHAR(50) NOT NULL COMMENT '变更后状态',
    operator_id BIGINT COMMENT '操作人ID',
    event_type VARCHAR(50) COMMENT '事件类型（APPROVE / ASSIGN / FINISH / REJECT）',
    remark TEXT COMMENT '备注',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ticket_id (ticket_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工单流转日志表';

-- 维修员表
CREATE TABLE IF NOT EXISTS repairman (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '维修员ID',
    name VARCHAR(100) NOT NULL COMMENT '姓名',
    skill_tags JSON COMMENT '技能标签',
    current_load INT DEFAULT 0 COMMENT '当前负载',
    avg处理时长 INT DEFAULT 0 COMMENT '平均处理时长（分钟）',
    is_available VARCHAR(10) DEFAULT 'true' COMMENT '是否可用',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='维修员表';


-- 2. PostgreSQL/pgvector 表结构
-- 需要先安装 pgvector 扩展: CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS fault_knowledge (
    id BIGSERIAL PRIMARY KEY,
    ticket_id BIGINT,
    device_name TEXT,
    chunk_type VARCHAR(20),
    content TEXT,
    embedding VECTOR(1536),
    metadata JSONB,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 向量索引
CREATE INDEX IF NOT EXISTS idx_fault_knowledge_embedding
ON fault_knowledge USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- 工单ID索引
CREATE INDEX IF NOT EXISTS idx_fault_knowledge_ticket_id
ON fault_knowledge (ticket_id);

-- 唯一约束（用于幂等）
ALTER TABLE fault_knowledge ADD CONSTRAINT uk_ticket_chunk
UNIQUE (ticket_id, chunk_type);
