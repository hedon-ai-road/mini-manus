from pydantic import BaseModel, Field
import uuid

class File(BaseModel):
    """文件信息领域模型，用于记录 Manus/Human 上传 or 生成的文件"""
    id: str = Field(default_factory=lambda : str(uuid.uuid4())) # 文件 ID
    filename: str = "" # 文件名字
    filepath: str = "" # 文件路径
    key: str = "" # 对象存储路径
    extension: str = "" # 文件扩展名
    mime_type: str = "" # mime-type 类型
    size: int = 0 # 文件大小，单位为字节