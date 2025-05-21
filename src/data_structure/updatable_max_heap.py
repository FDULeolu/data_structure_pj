class UpdatableMaxHeap:
    """
    一个支持高效更新和删除的最大堆, 使用列表作为底层存储, 并维护一个位置映射字典
    存储的元素是`(负优先级, 任务ID)`的元组, 对优先级取负以适应最小堆的操作封装在类方法内, 外部使用按照最大堆使用
    """
    def __init__(self):
        self._heap = [] 
        self._position_map = {}     # 位置映射, 用于实现快速查找, 删除和更新

    def _parent(self, i):
        """返回父节点索引"""
        if i == 0:
            return None
        return (i - 1) // 2

    def _left_child(self, i):
        """返回左子节点索引"""
        return 2 * i + 1

    def _right_child(self, i):
        """返回右子节点索引"""
        return 2 * i + 2

    def _swap(self, i, j):
        """交换堆中索引i和j的元素, 并更新位置映射"""
        if i == j:
            return

        item_i = self._heap[i]
        item_j = self._heap[j]
        
        # 交换列表中的元素
        self._heap[i], self._heap[j] = self._heap[j], self._heap[i]
        
        # 更新位置映射
        task_id_i = item_i[1]
        task_id_j = item_j[1]
        self._position_map[task_id_i] = j
        self._position_map[task_id_j] = i

    def _heapify_up(self, i):
        """从索引i向上调整, 维护最小堆性质"""
        parent_index = self._parent(i)

        while parent_index is not None and self._heap[i][0] < self._heap[parent_index][0]:
            self._swap(i, parent_index)
            i = parent_index
            parent_index = self._parent(i)

    def _heapify_down(self, i):
        """从索引i向下调整, 维护最小堆性质"""
        size = len(self._heap)
        while True:
            left = self._left_child(i)
            right = self._right_child(i)
            smallest = i

            if left < size and self._heap[left][0] < self._heap[smallest][0]:
                smallest = left
            if right < size and self._heap[right][0] < self._heap[smallest][0]:
                smallest = right

            if smallest == i:   # 此时，i就是最小的，停止向下调整
                break
            
            self._swap(i, smallest)
            i = smallest

    # ------------------- 公共接口 -------------------

    def insert(self, task_id, priority: float):
        """
        向堆中插入一个新任务
        如果任务已存在，则更新优先级

        输入:
            task_id: 任务名称
            priority (float): 任务优先级
        """
        if task_id in self._position_map:   # 更新优先级
            self.update_priority(task_id, priority)
            return

        item = (-priority, task_id)         # 处理负优先级
        
        self._heap.append(item)
        new_index = len(self._heap) - 1
        self._position_map[task_id] = new_index # 更新位置映射
        
        # 上浮调整
        self._heapify_up(new_index)

    def peek_max(self) -> tuple[float, any] | None:
        """查看堆顶元素, 不移除"""
        if not self._heap:
            return None
        neg_priority, task_id = self._heap[0]
        return -neg_priority, task_id       # 处理负优先级

    def extract_max(self) -> tuple[float, any] | None:
        """移除并返回堆顶元素"""
        if not self._heap:
            return None
        
        neg_priority, task_id = self._heap[0]
        
        # 用最后一个元素替换堆顶
        last_item = self._heap.pop() 
        if self._heap:
            self._heap[0] = last_item
            last_task_id = last_item[1]
            self._position_map[last_task_id] = 0 # 更新被移动元素的位置

            # 从堆顶向下调整
            self._heapify_down(0)
        
        # 从位置映射中移除被提取的任务
        del self._position_map[task_id]
        
        return -neg_priority, task_id   # 处理负优先级

    def is_empty(self) -> bool:
        """检查堆是否为空"""
        return len(self._heap) == 0

    def __contains__(self, task_id) -> bool:
        """检查任务ID是否存在于堆中"""
        return task_id in self._position_map

    def update_priority(self, task_id, new_priority: float):
        """
        更新堆中已存在任务的优先级

        输入:
            task_id: 任务名称
            new_priority (float): 需要更新的任务的新的优先级
        """
        if task_id not in self._position_map:
            raise KeyError(f"任务 '{task_id}' 不在堆中，无法更新")
            
        index = self._position_map[task_id]
        old_neg_priority = self._heap[index][0]     # 负优先级
        new_neg_priority = -new_priority

        # 更新堆中元素的优先级
        self._heap[index] = (new_neg_priority, task_id)    # 处理负优先级

        # 更新改任务在堆中的位置
        if new_neg_priority < old_neg_priority:
            self._heapify_up(index)
        else:
            self._heapify_down(index)

    def delete(self, task_id):
        """
        从堆中删除指定任务ID的元素
        
        输入:
            task_id: 要删除的任务ID
        """
        if task_id not in self._position_map:
            raise KeyError(f"任务 '{task_id}' 不在堆中")

        index_to_delete = self._position_map[task_id]
        last_index = len(self._heap) - 1

        if index_to_delete == last_index:
            self._heap.pop()
            del self._position_map[task_id]
        else:
            # 与最后一个元素交换
            self._swap(index_to_delete, last_index)
            
            # 弹出最后一个元素
            self._heap.pop()
            del self._position_map[task_id]
            
            # 对换上来的元素进行调整
            if index_to_delete < len(self._heap): # 防止删除的是最后一个任务
                 self._heapify_up(index_to_delete) 
                 self._heapify_down(index_to_delete) 

    def get_heap_size(self) -> int:
         """返回堆中元素的数量"""
         return len(self._heap)
