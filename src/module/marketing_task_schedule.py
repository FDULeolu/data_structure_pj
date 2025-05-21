import time
import uuid

from src.data_structure.updatable_max_heap import UpdatableMaxHeap
from src.data_structure.dependency_graph import TaskDependencyGraph
from src.model.marketing_task import *



# -------------- 营销任务管理器类 --------------
class TaskManager:
    """
    营销任务管理器，支持添加任务、添加和删除任务与任务之间的依赖
    """
    def __init__(self):
        """
        初始化营销任务管理器
        """
        self._tasks: dict[str, MarketingTask] = {}                           # 存储所有任务对象
        self._task_graph: TaskDependencyGraph = TaskDependencyGraph()        # 储存任务之间的依赖关系
        self._ready_queue: UpdatableMaxHeap = UpdatableMaxHeap()             # 储存就绪任务的优先队列
        self._in_degree: dict[str, int] = {}                                 # 记录Pending任务的前置依赖数量


    def _generate_task_id(self) -> str:
        """
        生成一个基于当前时间戳与UUID的task_id
        格式为: 20250411064800123456-uuid
        """

        # 时间戳
        now_struct = time.localtime() 
        timestamp_prefix = time.strftime("%Y%m%d%H%M%S", now_struct)
        microseconds = f"{int((time.time() % 1) * 1000000):06d}"

        # UUID(32字符的十六进制字符串)
        unique_suffix = uuid.uuid4().hex 

        return f"{timestamp_prefix}{microseconds}-{unique_suffix}"

    def add_task(self, urgency: float, influence: float, name: str = None) -> str:
        """
        往任务管理器中添加一个任务

        输入:
            urgency (float): 任务紧急度
            influence (float): 任务影响力
            name (str): 任务名称, 如果没有指定则利用生成的task_id代替
        
        返回:
            str: 该任务的task_id
        """
        task_id = self._generate_task_id()
        task_name = name if name else task_id
        
        # 创建新任务对象
        try:
            new_task = MarketingTask(task_id, urgency, influence, task_name)
        except ValueError as e:
            return None
        
        # 为系统添加一个新任务
        self._tasks[task_id] = new_task
        self._task_graph.add_task(task_id)
        self._in_degree[task_id] = 0
        new_task._set_status(TASK_STATUS_READY)     # 对于一个新加入的任务，一定没有前置依赖，所以状态为ready
        self._ready_queue.insert(task_id, new_task.priority)

        return task_id
    
    def add_dependency(self, prerequisite_id: str, dependent_id: str) -> bool:
        """
        添加一个任务间的依赖关系，表示prerequisite_id一定要在dependent_id之前完成
        如果添加的依赖会导致dependent_id不再ready，则需要将其从队列中移除

        参数:
            prerequisite_id (str): 前置任务ID
            dependent_id (str): 后置任务ID
        
        返回:
            bool: 如果依赖关系添加成功或已存在，返回True，若添加失败，返回False
        """
        if prerequisite_id not in self._tasks or dependent_id not in self._tasks:
            return False
        
        if prerequisite_id == dependent_id:
            return False
        
        prerequisite_task = self._tasks[prerequisite_id]
        dependent_task = self._tasks[dependent_id]

        # 如果之前已经包含了这条依赖关系，且前置任务未完成，那么这个依赖关系之前就起效了
        is_already_active_depenency = prerequisite_id in self._task_graph.get_prerequisites(dependent_id) and prerequisite_task.status != TASK_STATUS_COMPLETED
        
        # 尝试往依赖图中添加依赖关系
        if not self._task_graph.add_dependency(prerequisite_id, dependent_id):
            return False
        
        
        if not is_already_active_depenency and prerequisite_task.status != TASK_STATUS_COMPLETED:   # 如果这条依赖确实之前不存在且前置任务未完成
            # 更新入度
            self._in_degree[dependent_id] = self._in_degree.get(dependent_id, 0) + 1
            
            if dependent_id in self._ready_queue:   # 如果后置任务此前状态为ready，则需要更新ready队列与该任务的状态
                dependent_task._set_status(TASK_STATUS_PENDING)
                self._ready_queue.delete(dependent_id)
        
        return True
    
    def remove_dependency(self, prerequisite_id: str, dependent_id: str) -> bool:
        """
        移除一个已经存在的依赖关系 prerequisite_id -> dependent_id
        如果移除成功且导致dependent_id的状态变为ready，则更新ready队列

        输入:
            prerequisite_id (str): 前置任务的ID
            dependent_id (str): 后置任务的ID
        
        返回:
            bool: 如果依赖关系成功移除返回True，否则返回False
        """
        if prerequisite_id not in self._tasks or dependent_id not in self._tasks:
            return False
        
        prerequisite_task = self._tasks[prerequisite_id]

        # 检查移除这个依赖关系是否会影响dependent_id的状态
        is_active_dependency = prerequisite_id in self._task_graph.get_prerequisites(dependent_id) and prerequisite_task.status != TASK_STATUS_COMPLETED

        if not self._task_graph.remove_dependency(prerequisite_id, dependent_id):
            return False    # 不存在依赖关系
        
        if is_active_dependency:
            self._in_degree[dependent_id] = max(0, self._in_degree.get(dependent_id, 1) - 1)    # 更新入度字典

            # 如果此时入度为0且该任务并未完成，说明该任务已经不存在前置依赖，可以进入ready队列，并更新状态
            if self._in_degree[dependent_id] == 0 and self._tasks[dependent_id].status == TASK_STATUS_PENDING:
                self._tasks[dependent_id]._set_status(TASK_STATUS_READY)
                self._ready_queue.insert(dependent_id, self._tasks[dependent_id].priority)
        
        return True
    
    def mark_task_as_completed(self, task_id: str) -> bool:
        """
        将指定任务标记为已完成，同时更新其后续任务的入度字典

        输入:
            task_id (str): 要标记为完成的任务ID
        
        返回:
            bool: 如果任务成功标记则返回True，否则返回False
        """

        if task_id not in self._tasks:
            return False

        task_to_complete = self._tasks[task_id]

        if task_to_complete.status == TASK_STATUS_COMPLETED:
            return True

        if task_to_complete.status != TASK_STATUS_READY:
            return False
    
        
        task_to_complete._set_status(TASK_STATUS_COMPLETED)

        dependents = self._task_graph.get_dependents(task_id)
        for dependent in dependents:
            if dependent in self._in_degree:
                self._in_degree[dependent] -= 1

                if self._in_degree[dependent] < 0:
                    raise ValueError(f"任务 {dependent} 的前置依赖关系异常")
                
                if self._in_degree[dependent] == 0 and self._tasks[dependent].status == TASK_STATUS_PENDING:
                    self._tasks[dependent]._set_status(TASK_STATUS_READY)
                    self._ready_queue.insert(dependent, self._tasks[dependent].priority)
        
        return True
    
    def execute_next_highest_priority_task(self) -> MarketingTask | None:
        """
        从ready队列中提取优先级最高的任务，并执行

        返回:
            MarketingTask: 被执行的任务对象，如果没有可执行的任务，返回None
        """

        if self._ready_queue.is_empty():
            return None
        
        _, task_id_to_execute = self._ready_queue.extract_max()
        task_to_execute = self._tasks[task_id_to_execute]
        if task_to_execute.status != TASK_STATUS_READY:
            raise ValueError(f"任务 {task_id_to_execute} 状态异常")

        if self.mark_task_as_completed(task_id_to_execute):
            return task_to_execute

    def get_top_k_ready_tasks(self, k: int) -> list[MarketingTask]:
        """
        查看当前ready队列中的优先级最高的k个任务

        输入:
            k (int): 查看的任务数量
        
        返回:
            list[MarketingTask]: 按优先级从高到低排列的`MarketingTask`列表，最多包含k个任务，如果ready队列中的任务少于k个，则返回全部ready任务
        """      
        if not isinstance(k, int) or k <= 0:
            raise ValueError("k必须是正整数")
        
        if self._ready_queue.is_empty():
            return []
        
        top_k_tasks_info = []   # 存储(priority, task_id)
        top_k_tasks = []        # 存储MarketingTask对象

        num_to_extract = min(k, self._ready_queue.get_heap_size())

        # 从ready列表中取出top k个任务
        for _ in range(num_to_extract):
            extracted_item = self._ready_queue.extract_max()
            priority, task_id = extracted_item
            if task_id in self._tasks:
                top_k_tasks_info.append(extracted_item)
                top_k_tasks.append(self._tasks[task_id])
            else:
                raise IndexError(f"在任务列表中未找到{task_id}")
        
        # 塞回这top k个任务
        for priority, task_id in top_k_tasks_info:
            self._ready_queue.insert(task_id, priority)
        
        return top_k_tasks
    
    
    def update_task_info(self, 
                         task_id: str,
                         new_urgency: float = None,
                         new_influence: float = None,
                         new_name: str = None) -> bool:
        """
        更新现有的任务信息，如果更新的信息会导致优先级的变化，那么如果这个任务处于ready状态，会改变其在ready队列中的位置

        输入:
            task_id (str): 要更新的任务ID
            new_urgency (float, 可选): 新的紧急度
            new_influence (float, 可选): 新的影响力
            new_name (str, 可选): 新的任务名称
        
        返回:
            如果成功更新返回True，否则返回False
        """
        if task_id not in self._tasks:
            return False
        
        task_to_update = self._tasks[task_id]

        old_priority = task_to_update.priority

        if new_name is not None:
            try:
                task_to_update.name = new_name
            except ValueError as e:
                return False
        
        if new_urgency is not None or new_influence is not None: 
            try:
                task_to_update._update_details(urgency=new_urgency, influence=new_influence)
            except ValueError as e: 
                return False

        priority_changed = task_to_update.priority != old_priority

        if priority_changed and task_to_update.status == TASK_STATUS_READY:
            if task_id in self._ready_queue: # 再次确认
                self._ready_queue.update_priority(task_id, task_to_update.priority)

        return True
    
    def delete_task(self, task_id: str) -> bool:
        """
        从系统中彻底删除一个任务及其所有相关依赖，包括
        1. 任务列表中的任务
        2. 前置依赖图中的节点和依赖的边
        3. ready队列中的任务（如果存在）
        4. 更新该任务的后置任务的入度字典，并考虑是否将失去前置条件的任务加入ready队列
        5. 把该任务从入度字典中删除

        输入:
            task_id (str): 要删除的任务的ID
        
        返回:
            bool: 如果删除成功返回True，否则返回False
        """
        if task_id not in self._tasks:
            return False

        dependents = self._task_graph.get_dependents(task_id)
        # 处理其后置依赖的入度字典
        for dep in dependents:
            if dep in self._tasks and dep in self._in_degree:
                self._in_degree[dep] -= 1
                if self._in_degree[dep] < 0:
                    raise ValueError(f"任务 {dep} 依赖异常")
                
                if self._in_degree[dep] == 0 and self._tasks[dep].status == TASK_STATUS_PENDING:
                    self._tasks[dep]._set_status(TASK_STATUS_READY)
                    self._ready_queue.insert(dep, self._tasks[dep].priority)
        
        # 从依赖图中删除
        self._task_graph.remove_task(task_id)

        # 从ready队列中删除
        if task_id in self._ready_queue:
            self._ready_queue.delete(task_id)
        
        # 从任务列表中删除
        del self._tasks[task_id]

        # 从入度字典中删除
        del self._in_degree[task_id]

        return True