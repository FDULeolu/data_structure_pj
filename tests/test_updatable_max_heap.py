import unittest
from src.data_structure.updatable_max_heap import UpdatableMaxHeap

class TestUpdatableMaxHeap(unittest.TestCase):

    def setUp(self):
        """在每个测试方法运行前初始化一个空的堆。"""
        self.heap = UpdatableMaxHeap()

    def test_initialization(self):
        """测试堆的初始状态。"""
        self.assertTrue(self.heap.is_empty())
        self.assertEqual(self.heap.get_heap_size(), 0)
        self.assertIsNone(self.heap.peek_max())
        self.assertIsNone(self.heap.extract_max())
        self.assertEqual(self.heap._heap, [])
        self.assertEqual(self.heap._position_map, {})

    def test_insert_single_element(self):
        """测试插入单个元素。"""
        self.heap.insert("task1", 50)
        self.assertFalse(self.heap.is_empty())
        self.assertEqual(self.heap.get_heap_size(), 1)
        self.assertIn("task1", self.heap)
        self.assertIn("task1", self.heap._position_map)
        self.assertEqual(self.heap._position_map["task1"], 0)
        self.assertEqual(self.heap._heap[0], (-50.0, "task1")) # 内部存储负优先级
        priority, task_id = self.heap.peek_max()
        self.assertEqual(task_id, "task1")
        self.assertAlmostEqual(priority, 50.0)

    def test_insert_multiple_elements_order(self):
        """测试插入多个元素后，extract_max 是否按优先级降序返回。"""
        tasks = {"task1": 50, "task2": 30, "task3": 70, "task4": 40, "task5": 70}
        for task_id, priority in tasks.items():
            self.heap.insert(task_id, priority)

        self.assertEqual(self.heap.get_heap_size(), 5)
        
        extracted_order = []
        while not self.heap.is_empty():
            priority, task_id = self.heap.extract_max()
            extracted_order.append((priority, task_id))

        # 预期顺序：优先级高的在前，优先级相同的不保证顺序
        self.assertEqual(extracted_order[0][0], 70) # task3 或 task5
        self.assertEqual(extracted_order[1][0], 70) # task3 或 task5
        self.assertEqual(extracted_order[2][0], 50) # task1
        self.assertEqual(extracted_order[3][0], 40) # task4
        self.assertEqual(extracted_order[4][0], 30) # task2
        
        # 确保 ID 都在里面
        extracted_ids = {item[1] for item in extracted_order}
        self.assertEqual(extracted_ids, set(tasks.keys()))
        
        # 提取后应为空
        self.assertTrue(self.heap.is_empty())
        self.assertEqual(self.heap._position_map, {})

    def test_insert_duplicate_task_id_updates_priority(self):
        """测试插入已存在的 task_id 时，行为应等同于更新优先级。"""
        self.heap.insert("taskA", 50)
        self.heap.insert("taskB", 70)
        
        # 插入 taskA，但使用新优先级
        self.heap.insert("taskA", 80) 
        
        self.assertEqual(self.heap.get_heap_size(), 2) # 大小应不变
        priority, task_id = self.heap.peek_max()
        self.assertEqual(task_id, "taskA") # taskA 现在优先级最高
        self.assertAlmostEqual(priority, 80.0)

        # 再次插入 taskA，优先级降低
        self.heap.insert("taskA", 60)
        self.assertEqual(self.heap.get_heap_size(), 2)
        priority, task_id = self.heap.peek_max()
        self.assertEqual(task_id, "taskB") # taskB 现在优先级最高
        self.assertAlmostEqual(priority, 70.0)

    def test_peek_max_on_empty_heap(self):
        """测试在空堆上调用 peek_max。"""
        self.assertIsNone(self.heap.peek_max())

    def test_peek_max_does_not_modify(self):
        """测试 peek_max 不会修改堆。"""
        self.heap.insert("task1", 50)
        self.heap.insert("task2", 70)
        initial_heap = list(self.heap._heap)
        initial_map = dict(self.heap._position_map)
        initial_size = self.heap.get_heap_size()

        priority, task_id = self.heap.peek_max()
        self.assertEqual(task_id, "task2")
        self.assertAlmostEqual(priority, 70.0)

        # 验证堆未被修改
        self.assertEqual(self.heap._heap, initial_heap)
        self.assertEqual(self.heap._position_map, initial_map)
        self.assertEqual(self.heap.get_heap_size(), initial_size)

    def test_extract_max_on_empty_heap(self):
        """测试在空堆上调用 extract_max。"""
        self.assertIsNone(self.heap.extract_max())

    def test_extract_max_single_element(self):
        """测试从只有一个元素的堆中提取。"""
        self.heap.insert("task1", 50)
        priority, task_id = self.heap.extract_max()
        self.assertEqual(task_id, "task1")
        self.assertAlmostEqual(priority, 50.0)
        self.assertTrue(self.heap.is_empty())
        self.assertEqual(self.heap._position_map, {})

    def test_contains(self):
        """测试 __contains__ (__in__) 的行为。"""
        self.assertFalse("task1" in self.heap)
        self.heap.insert("task1", 50)
        self.assertTrue("task1" in self.heap)
        self.assertFalse("task2" in self.heap)
        self.heap.insert("task2", 70)
        self.assertTrue("task2" in self.heap)
        self.heap.extract_max() # 提取 task2
        self.assertTrue("task1" in self.heap)
        self.assertFalse("task2" in self.heap)
        self.heap.delete("task1")
        self.assertFalse("task1" in self.heap)

    def test_update_priority_non_existent(self):
        """测试更新不存在的任务时抛出 KeyError。"""
        with self.assertRaisesRegex(KeyError, "任务 'task_non_existent' 不在堆中"):
            self.heap.update_priority("task_non_existent", 100)

    def test_update_priority_increase(self):
        """测试增加任务优先级（可能触发上浮）。"""
        self.heap.insert("task1", 50)
        self.heap.insert("task2", 30)
        self.heap.insert("task3", 70) # Max
        self.heap.insert("task4", 40)
        
        self.heap.update_priority("task4", 90) # task4 优先级变为最高
        self.assertEqual(self.heap.get_heap_size(), 4)
        priority, task_id = self.heap.peek_max()
        self.assertEqual(task_id, "task4")
        self.assertAlmostEqual(priority, 90.0)
        # 可以进一步检查内部堆结构或通过extract_max验证顺序

    def test_update_priority_decrease(self):
        """测试降低任务优先级（可能触发下沉）。"""
        self.heap.insert("task1", 50)
        self.heap.insert("task2", 80) # Max
        self.heap.insert("task3", 70)
        self.heap.insert("task4", 40)

        self.heap.update_priority("task2", 20) # task2 优先级降到最低
        self.assertEqual(self.heap.get_heap_size(), 4)
        priority, task_id = self.heap.peek_max()
        self.assertEqual(task_id, "task3") # task3 现在应为最高
        self.assertAlmostEqual(priority, 70.0)
        # 可以进一步检查内部堆结构或通过extract_max验证顺序

    def test_update_priority_no_change(self):
        """测试更新为相同优先级（堆结构应不变）。"""
        self.heap.insert("task1", 50)
        self.heap.insert("task2", 70)
        initial_heap = list(self.heap._heap)
        initial_map = dict(self.heap._position_map)

        self.heap.update_priority("task1", 50)

        self.assertEqual(self.heap._heap, initial_heap)
        self.assertEqual(self.heap._position_map, initial_map)

    def test_delete_non_existent(self):
        """测试删除不存在的任务时抛出 KeyError。"""
        with self.assertRaisesRegex(KeyError, "任务 'task_non_existent' 不在堆中"):
            self.heap.delete("task_non_existent")

    def test_delete_root(self):
        """测试删除堆顶元素。"""
        self.heap.insert("task1", 50)
        self.heap.insert("task2", 30)
        self.heap.insert("task3", 70) # Max
        self.heap.insert("task4", 40)

        self.heap.delete("task3") # 删除当前最大值
        self.assertEqual(self.heap.get_heap_size(), 3)
        self.assertNotIn("task3", self.heap)
        priority, task_id = self.heap.peek_max()
        self.assertEqual(task_id, "task1") # task1 应该成为新的最大值
        self.assertAlmostEqual(priority, 50.0)
        # 验证堆性质是否保持 (可以通过多次extract_max检查顺序)
        items = []
        while not self.heap.is_empty(): items.append(self.heap.extract_max())
        self.assertEqual([p for p,i in items], [50.0, 40.0, 30.0])


    def test_delete_leaf(self):
        """测试删除一个叶子节点元素。"""
        # 构建一个堆，使某个元素确定在叶子层
        # 例如：insert 70, 50, 30, 40, 20
        self.heap.insert("t70", 70)
        self.heap.insert("t50", 50)
        self.heap.insert("t30", 30)
        self.heap.insert("t40", 40)
        self.heap.insert("t20", 20) # t20 可能是叶子节点
        
        # 假设我们知道 't20' 或 't30' 或 't40' 在叶子层（取决于具体插入顺序和堆实现）
        # 为了确定性，我们先检查一个叶子节点
        # 内部堆可能是 [(-70,t70), (-50,t50), (-30,t30), (-40,t40), (-20,t20)]
        # 或者          [(-70,t70), (-50,t50), (-30,t30), (-40,t40), (-20,t20)] 或其他变种
        # 索引：           0         1         2         3         4
        # 最后一个元素 t20 在索引 4，其父为 (4-1)//2 = 1。它肯定是叶子。
        # 元素 t40 在索引 3，其父为 (3-1)//2 = 1。它也肯定是叶子。
        # 元素 t30 在索引 2，其父为 (2-1)//2 = 0。它也肯定是叶子。
        
        leaf_to_delete = "t30" # 尝试删除叶子 t30
        
        self.assertIn(leaf_to_delete, self.heap)
        self.heap.delete(leaf_to_delete)
        
        self.assertEqual(self.heap.get_heap_size(), 4)
        self.assertNotIn(leaf_to_delete, self.heap)
        
        # 验证堆性质
        items = []
        while not self.heap.is_empty(): items.append(self.heap.extract_max())
        self.assertEqual([p for p,i in items], [70.0, 50.0, 40.0, 20.0])

    def test_delete_internal_node(self):
        """测试删除一个内部节点元素。"""
        self.heap.insert("t70", 70)
        self.heap.insert("t50", 50) # 将成为内部节点
        self.heap.insert("t30", 30)
        self.heap.insert("t40", 40)
        self.heap.insert("t20", 20)
        self.heap.insert("t60", 60) # t50 或 t60 可能是内部节点

        # 假设 't50' 是内部节点 (index 1)
        internal_to_delete = "t50"
        
        self.assertIn(internal_to_delete, self.heap)
        self.heap.delete(internal_to_delete)

        self.assertEqual(self.heap.get_heap_size(), 5)
        self.assertNotIn(internal_to_delete, self.heap)
        
        # 验证堆性质
        items = []
        while not self.heap.is_empty(): items.append(self.heap.extract_max())
        # 预期顺序: 70, 60, 40, 30, 20
        self.assertEqual([p for p,i in items], [70.0, 60.0, 40.0, 30.0, 20.0])

    def test_delete_only_element(self):
        """测试删除堆中唯一的元素。"""
        self.heap.insert("task1", 100)
        self.heap.delete("task1")
        self.assertTrue(self.heap.is_empty())
        self.assertEqual(self.heap._position_map, {})

    def test_delete_all_elements(self):
        """测试通过 delete 删除所有元素。"""
        tasks = {"task1": 50, "task2": 30, "task3": 70}
        for task_id, priority in tasks.items():
            self.heap.insert(task_id, priority)
            
        self.heap.delete("task1")
        self.heap.delete("task3")
        self.heap.delete("task2")
        
        self.assertTrue(self.heap.is_empty())
        self.assertEqual(self.heap._position_map, {})

    def test_mixed_operations(self):
        """测试混合插入、更新、删除、提取操作。"""
        self.heap.insert("A", 10)
        self.heap.insert("B", 20)
        self.assertTrue("A" in self.heap)
        self.assertTrue("B" in self.heap)
        self.assertEqual(self.heap.peek_max(), (20.0, "B"))
        
        self.heap.insert("C", 5)
        self.heap.update_priority("A", 30) # A 变为最大
        self.assertEqual(self.heap.peek_max(), (30.0, "A"))
        
        self.heap.delete("B") # 删除原来的最大值 B
        self.assertNotIn("B", self.heap)
        self.assertEqual(self.heap.get_heap_size(), 2)
        self.assertEqual(self.heap.peek_max(), (30.0, "A")) # A 仍然最大
        
        extracted_priority, extracted_id = self.heap.extract_max() # 提取 A
        self.assertEqual(extracted_id, "A")
        self.assertAlmostEqual(extracted_priority, 30.0)
        
        self.assertEqual(self.heap.peek_max(), (5.0, "C")) # 只剩 C
        
        self.heap.insert("D", 15)
        self.assertEqual(self.heap.peek_max(), (15.0, "D"))
        
        self.heap.update_priority("C", 25) # C 现在最大
        self.assertEqual(self.heap.peek_max(), (25.0, "C"))
        
        # 清空
        self.heap.extract_max()
        self.heap.extract_max()
        self.assertTrue(self.heap.is_empty())

if __name__ == '__main__':
    unittest.main()