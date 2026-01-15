"""
自定义 SQLAlchemy 类型
提供时区安全的 DateTime 类型，解决 SQLite 不支持时区的问题
"""
from datetime import datetime, timezone
from sqlalchemy import DateTime, TypeDecorator


class UTCDateTime(TypeDecorator):
    """
    存储为 UTC 的 DateTime 类型。
    
    写入时：将任何时区的时间转换为 UTC 后存储（naive datetime 被视为 UTC）
    读取时：返回带 UTC 时区信息的 aware datetime
    
    这确保了：
    1. 数据库中存储的始终是 UTC 时间
    2. 应用层拿到的始终是带时区的 datetime 对象
    3. 前端收到的 ISO 字符串包含 +00:00 后缀
    """
    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """写入数据库前的处理"""
        if value is None:
            return None
        
        if value.tzinfo is None:
            # naive datetime，假设为 UTC
            return value
        else:
            # aware datetime，转换为 UTC 后去掉时区信息存储
            return value.astimezone(timezone.utc).replace(tzinfo=None)

    def process_result_value(self, value, dialect):
        """从数据库读取后的处理"""
        if value is None:
            return None
        
        # SQLite 返回的是 naive datetime，我们标记为 UTC
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value


def utc_now():
    """返回当前 UTC 时间 aware object，用于 SQLAlchemy default/onupdate"""
    return datetime.now(timezone.utc)
