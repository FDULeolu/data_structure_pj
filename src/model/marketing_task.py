# 用来表示任务状态
TASK_STATUS_PENDING = "PENDING"
TASK_STATUS_READY = "READY"
TASK_STATUS_COMPLETED = "COMPLETED"


# -------------- 营销任务类 --------------

class MarketingTask:
    """用来表示一个营销任务"""
    __slots__ = ('_task_id', '_name', '_urgency', '_influence', '_priority', '_status')
    
    def __init__(self, task_id: str, urgency: float, influence: float, name: str = None):
        """
        初始化一个营销任务
        
        输入:
            task_id (str): 表示任务标识符（必须是一个唯一的，不能重复）
            urgency (float): 任务紧急度
            influence (float): 任务影响力
            name (str): 任务名称
        """
        if not isinstance(task_id, str) or not task_id.strip():
            raise ValueError("task_id必须是一个非空的字符串")
        if not isinstance(urgency, (int, float)) or urgency <= 0:
            raise ValueError("urgency必须是一个正数")
        if not isinstance(influence, (int, float)) or influence <= 0:
            raise ValueError("influence必须是一个正数")

        self._task_id = task_id
        self._name = name if name else task_id       # 如果没有提供name，就用task_id作为name
        self._priority = 0.0
        self.urgency = float(urgency)
        self.influence = float(influence)
        # 由于设置了urgency和influence的setter，这里会自动计算priority
        self._status = TASK_STATUS_PENDING           # 新任务默认为pending状态
    
    # 利用property来控制对属性的访问和操作
    @property
    def task_id(self) -> str:
        return self._task_id
    
    @property
    def name(self) -> str:
        return self._name
    
    @name.setter
    def name(self, new_name: str):
        if not isinstance(new_name, str) or not new_name.strip():
            raise ValueError("任务名称必须是一个非空的字符串")
        self._name = new_name
    
    @property
    def urgency(self) -> float:
        return self._urgency

    @urgency.setter
    def urgency(self, value: float):
        if not isinstance(value, (int, float)) or value <= 0:
            raise ValueError("urgency必须是一个正数")
        self._urgency = float(value)
        # 每次 urgency 或 influence 更新时，重新计算优先级
        self._recalculate_priority()

    @property
    def influence(self) -> float:
        return self._influence

    @influence.setter
    def influence(self, value: float):
        if not isinstance(value, (int, float)) or value <= 0:
            raise ValueError("influence 必须是一个正数")
        self._influence = float(value)
        self._recalculate_priority()
    
    def _recalculate_priority(self):
        """根据当前的urgency和influence更新优先级"""
        if hasattr(self, '_urgency') and hasattr(self, '_influence'):
            self._priority = self._urgency * self._influence
        else:
            self._priority = 0.0

    @property
    def priority(self) -> float:
        return self._priority
    
    @property
    def status(self) -> str:
        return self._status
    

    def _set_status(self, new_status: str):
        allowed_statuses = {TASK_STATUS_PENDING, TASK_STATUS_READY, TASK_STATUS_COMPLETED}
        if new_status not in allowed_statuses:
            raise ValueError(f"无效的任务状态: {new_status}")
        self._status = new_status
    
    def _update_details(self, urgency: float = None, influence: float = None):
        """
        更新任务的紧急程度或者影响力，并更新优先级，如果某个参数为None，则不更新该属性
        如果更新成功，则返回True，如果没有更新，则返回False
        """
        updated = False
        if urgency is not None:
            old_urgency_val = self._urgency 
            self.urgency = urgency 
            if self._urgency != old_urgency_val: 
                 updated = True
        
        if influence is not None:
            old_influence_val = self._influence 
            self.influence = influence 
            if self._influence != old_influence_val: 
                updated = True
        
        return updated
    
    def __repr__(self):
        return (f"MarketingTask(id='{self.task_id}', name='{self.name}', "
                f"urgency={self.urgency:.2f}, influence={self.influence:.2f}, "
                f"priority={self.priority:.2f}, status='{self.status}')")
    
    def __str__(self):
        return self.__repr__()
    
    def __hash__(self):
        return hash(self.task_id)

    def __eq__(self, other):
        if isinstance(other, MarketingTask):
            return self.task_id == other.task_id
        return False
    