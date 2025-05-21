class TaskDependencyGraph:
    """
    一个有向图, 用于表示和管理任务之间的依赖关系
    边 u -> v 表示任务 u 必须在任务 v 完成之前完成
    需要包含环路检测, 防止任务依赖永远无法满足
    """
    def __init__(self):
        self.nodes = set()  # 存储所有节点
        self.adj = {}       # 存储任务的依赖关系 {task_id: set(subsequent_task_id)}
        self.rev_adj = {}   # 储存任务的反向依赖关系 {task_id: set(pre_task_id)}

    def add_task(self, task_id) -> bool:
        """
        向图中添加一个任务节点
        
        输入:
            task_id: 任务名称
        
        返回:
            bool: 如果添加成功, 返回True，如果添加失败(已存在), 返回False
        """
        if task_id not in self.nodes:
            self.nodes.add(task_id)
            self.adj[task_id] = set()
            self.rev_adj[task_id] = set()
            return True
        return False

    def remove_task(self, task_id):
        """从图中移除一个任务节点及其所有相关依赖, 并返回这个节点id"""
        if task_id not in self.nodes:
            raise IndexError(f"节点 {task_id} 不存在")

        # 移除 task_id 作为前置任务的所有依赖
        dependents_to_update = list(self.adj.get(task_id, set())) # 创建副本
        for dependent in dependents_to_update:
            if dependent in self.rev_adj:
                 self.rev_adj[dependent].discard(task_id)
                 # 不在self.adj[task_id]中删除这个dependent，因为之后会直接删除task_id这个key

        # 移除 task_id 作为后续任务的所有依赖
        prerequisites_to_update = list(self.rev_adj.get(task_id, set())) # 创建副本
        for prereq in prerequisites_to_update:
             if prereq in self.adj: # 确认 prereq 仍然存在
                 self.adj[prereq].discard(task_id)
                # 不在self.rev_adj[task_id]中删除这个dependent，因为之后会直接删除task_id这个key

        # 从节点集合和邻接列表中移除task_id这个key
        self.nodes.discard(task_id)
        if task_id in self.adj:
            del self.adj[task_id]
        if task_id in self.rev_adj:
            del self.rev_adj[task_id]
        
        return task_id

    def _has_path(self, start_node, end_node) -> bool:
        """
        使用DFS检测从 start_node 是否存在到 end_node 的路径, 用于环路检查
        
        输入:
            start_node: 起始节点
            end_node: 搜索的目标节点
        
        返回:
            bool: 如果存在一条从start_node到end_node的路径，那么返回True, 否则返回False
        """
        if start_node not in self.nodes or end_node not in self.nodes:
            return False

        stack = [start_node]
        visited_in_this_traversal = {start_node}

        while stack:
            current_node = stack.pop()

            for neighbor in self.adj.get(current_node, set()):
                if neighbor == end_node: 
                    return True
                
                if neighbor not in visited_in_this_traversal:
                    visited_in_this_traversal.add(neighbor)
                    stack.append(neighbor)
        
        return False

    def add_dependency(self, prerequisite_id, dependent_id) -> bool:
        """
        添加依赖关系：prerequisite_id -> dependent_id
        在添加前会进行环路检测

        返回:
            bool: 如果成功添加返回True，如果会形成环路或节点不存在则返回False
        """
        # 检查节点是否存在
        if prerequisite_id not in self.nodes or dependent_id not in self.nodes:
            return False
        if prerequisite_id == dependent_id:     # 不允许添加自环
            return False 

        # 检查是否已存在此依赖
        if dependent_id in self.adj.get(prerequisite_id, set()):
            return True

        # 环路检测
        if self._has_path(dependent_id, prerequisite_id):
            return False

        # 添加依赖关系
        self.adj[prerequisite_id].add(dependent_id)
        self.rev_adj[dependent_id].add(prerequisite_id)
        return True

    def remove_dependency(self, prerequisite_id, dependent_id) -> bool:
        """
        移除依赖关系prerequisite_id -> dependent_id
        
        返回:
            bool: 如果移除成功返回True，否则返回False
        """
        if prerequisite_id not in self.nodes or dependent_id not in self.nodes:
            return False
        
        if prerequisite_id in self.adj:
            if dependent_id in self.adj[prerequisite_id]:
                self.adj[prerequisite_id].remove(dependent_id)
                self.rev_adj[dependent_id].remove(prerequisite_id)
                return True
        
        return False

    def get_dependents(self, task_id) -> set:
        """获取直接依赖于task_id的任务集合"""
        if task_id not in self.nodes:
             return set()

        return self.adj.get(task_id, set()).copy()      # 返回副本以至于防止被外部修改

    def get_prerequisites(self, task_id) -> set:
        """获取task_id的前置任务集合"""
        if task_id not in self.nodes:
            return set()

        return self.rev_adj.get(task_id, set()).copy()  # 返回副本以至于防止被外部修改

    def has_task(self, task_id) -> bool:
        """检查任务是否存在于图中"""
        return task_id in self.nodes

    def get_all_tasks(self) -> list:
         """返回图中所有任务的列表"""
         return list(self.nodes)