from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, Generic
from pydantic import BaseModel, Field

# 工具输入基类
class BaseToolInput(BaseModel):
    pass

# 工具输出基类
class BaseToolOutput(BaseModel):
    pass

# 工具参数和返回值类型变量
T = TypeVar('T', bound=BaseToolInput)
U = TypeVar('U', bound=BaseToolOutput)

class BaseTool(ABC, Generic[T, U]):
    """工具基类"""
    name: str
    description: str
    input_schema: Type[T]
    output_schema: Type[U]
    
    def __init__(self, name: str = None, description: str = None):
        """
        初始化工具
        
        Args:
            name: 工具名称（可选）
            description: 工具描述（可选）
        """
        if name:
            self.name = name
        if description:
            self.description = description
    
    @abstractmethod
    async def _run(self, input_data: T) -> U:
        """
        工具核心执行逻辑，子类必须实现此方法
        
        Args:
            input_data: 工具输入数据
            
        Returns:
            工具执行结果
        """
        pass
    
    async def run(self, input_data: Union[Dict[str, Any], T]) -> U:
        """
        运行工具
        
        Args:
            input_data: 可以是字典或已构造的输入对象
            
        Returns:
            工具执行结果
        """
        # 如果输入是字典，转换为输入模型实例
        if isinstance(input_data, dict):
            input_obj = self.input_schema(**input_data)
        else:
            input_obj = input_data
            
        # 执行工具核心逻辑
        return await self._run(input_obj)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将工具转为字典格式，用于API接口展示
        
        Returns:
            工具描述信息的字典
        """
        schema = self.input_schema.model_json_schema()
        required = schema.get("required", [])
        properties = schema.get("properties", {})
        
        # 构建参数列表
        parameters = []
        for name, prop in properties.items():
            param = {
                "name": name,
                "description": prop.get("description", ""),
                "type": prop.get("type", "string"),
                "required": name in required
            }
            parameters.append(param)
        
        return {
            "name": self.name,
            "description": self.description,
            "parameters": parameters
        } 