import unittest

from src.model.marketing_task import *
from src.module.marketing_task_schedule import *

class TestMarketingTaskManager(unittest.TestCase):

    def setUp(self):
        """在每个测试方法运行前初始化一个空的 TaskManager。"""
        self.tm = TaskManager()
        # 为了可预测的ID，我们可以mock _generate_task_id，或者接受其随机性
        # 这里我们暂时接受其随机性，测试主要关注逻辑
        self.id_counter = 1 # 用于辅助生成可预测的ID（如果需要）

    def _add_sample_task(self, urgency, influence, name=None, expect_success=True) -> str | None:
        """辅助方法添加任务，并处理可能的None返回值"""
        # 如果要使用可预测ID进行测试:
        # task_id_to_use = f"T{self.id_counter}"
        # self.tm._tasks[task_id_to_use] = MarketingTask(...) # 手动插入以控制ID
        # self.tm._task_graph.add_task(task_id_to_use)
        # self.tm._in_degree[task_id_to_use] = 0
        # ... 手动加入ready_queue ...
        # self.id_counter += 1
        # return task_id_to_use
        # 但这会绕过 add_task 的逻辑，所以我们还是调用 add_task
        task_id = self.tm.add_task(urgency, influence, name)
        if expect_success:
            self.assertIsNotNone(task_id, f"添加任务 (u:{urgency}, i:{influence}, n:{name}) 时期望成功，但返回 None")
            if task_id: # 确保 task_id 不是 None 才进行后续断言
                self.assertIn(task_id, self.tm._tasks)
        else:
            self.assertIsNone(task_id, f"添加任务 (u:{urgency}, i:{influence}, n:{name}) 时期望失败，但返回 task_id")
        return task_id

    # --- 测试 MarketingTask 本身 (确保与 TaskManager 交互的基础是正确的) ---
    def test_marketing_task_creation_and_priority(self):
        task = MarketingTask("id1", 10, 5, "Task One")
        self.assertEqual(task.task_id, "id1")
        self.assertEqual(task.name, "Task One")
        self.assertEqual(task.urgency, 10)
        self.assertEqual(task.influence, 5)
        self.assertEqual(task.priority, 50) # 10 * 5
        self.assertEqual(task.status, TASK_STATUS_PENDING)

    def test_marketing_task_update_details(self):
        task = MarketingTask("id1", 10, 5, "Task One")
        task.urgency = 20 # 通过setter更新，应重新计算优先级
        self.assertEqual(task.priority, 100) # 20 * 5
        task.influence = 2
        self.assertEqual(task.priority, 40) # 20 * 2
        
        # 测试 update_details 方法 (你的实现中这个方法似乎和直接用setter效果重叠了)
        # 如果 MarketingTask.priority 是直接通过 _recalculate_priority 在setter中更新的，
        # 那么 MarketingTask.update_details 中的 self.priority = self._calculate_priority() 可能是多余的
        # 但如果 update_details 是主要的更新接口，则测试它：
        task._update_details(urgency=5, influence=5)
        self.assertEqual(task.priority, 25)


    # --- 测试 TaskManager ---
    def test_add_task(self):
        """测试添加新任务。"""
        tid1 = self._add_sample_task(10, 5, "Task Alpha")
        self.assertIn(tid1, self.tm._ready_queue) # 新任务应在就绪队列
        self.assertEqual(self.tm._tasks[tid1].status, TASK_STATUS_READY)
        self.assertEqual(self.tm._in_degree[tid1], 0)

        tid2 = self._add_sample_task(20, 2, "Task Beta")
        self.assertIn(tid2, self.tm._ready_queue)
        self.assertEqual(self.tm._ready_queue.get_heap_size(), 2)

        # 测试添加无效参数的任务 (MarketingTask的__init__会校验)
        invalid_tid = self.tm.add_task(0, 5, "Invalid Urgency") # urgency <= 0 会失败
        self.assertIsNone(invalid_tid)
        invalid_tid_2 = self.tm.add_task(5, -1, "Invalid Influence") # influence <=0 会失败
        self.assertIsNone(invalid_tid_2)
        self.assertEqual(self.tm._ready_queue.get_heap_size(), 2) # 确保无效添加未影响队列

    def test_add_dependency_simple_and_status_change(self):
        """测试添加依赖，以及后继任务状态和就绪队列的变化。"""
        t1 = self._add_sample_task(10, 1, "T1") # P=10
        t2 = self._add_sample_task(5, 1, "T2")  # P=5
        
        # T1 和 T2 初始都应该是 READY 且在队列中
        self.assertEqual(self.tm._tasks[t1].status, TASK_STATUS_READY)
        self.assertEqual(self.tm._tasks[t2].status, TASK_STATUS_READY)
        self.assertTrue(t1 in self.tm._ready_queue)
        self.assertTrue(t2 in self.tm._ready_queue)
        self.assertEqual(self.tm._in_degree[t2], 0)

        # 添加依赖 T1 -> T2 (T1 未完成)
        self.assertTrue(self.tm.add_dependency(t1, t2))
        self.assertEqual(self.tm._in_degree[t2], 1) # T2 入度增加
        self.assertEqual(self.tm._tasks[t2].status, TASK_STATUS_PENDING) # T2 状态变为 PENDING
        self.assertFalse(t2 in self.tm._ready_queue) # T2 从就绪队列移除
        self.assertTrue(t1 in self.tm._ready_queue) # T1 仍在队列中

    def test_add_dependency_prerequisite_already_completed(self):
        """测试添加依赖时，如果前置任务已完成，不影响后继任务的就绪状态。"""
        t1 = self._add_sample_task(10, 1, "T1")
        t2 = self._add_sample_task(5, 1, "T2")
        
        # 先完成 T1
        self.tm._tasks[t1]._set_status(TASK_STATUS_COMPLETED) 
        # 模拟外部完成，注意这不会自动更新T1的后继，因为还没建立依赖
        # 如果要严格，应该通过 TaskManager 的完成方法来做，但这里是为了测试 add_dependency

        # 添加依赖 T1 -> T2 (T1 已完成)
        self.assertTrue(self.tm.add_dependency(t1, t2))
        self.assertEqual(self.tm._in_degree[t2], 0) # T2 入度不应增加，因为T1已完成
        self.assertEqual(self.tm._tasks[t2].status, TASK_STATUS_READY) # T2 状态应保持 READY
        self.assertTrue(t2 in self.tm._ready_queue) # T2 应仍在就绪队列

    def test_add_dependency_creates_cycle(self):
        """测试添加依赖时形成环路。"""
        t1 = self._add_sample_task(1,1, "T1")
        t2 = self._add_sample_task(1,1, "T2")
        self.assertTrue(self.tm.add_dependency(t1, t2))
        self.assertFalse(self.tm.add_dependency(t2, t1)) # 应形成环路并失败

    def test_add_duplicate_active_dependency(self):
        """测试重复添加一个已存在的、前置未完成的依赖。"""
        t1 = self._add_sample_task(1,1, "T1")
        t2 = self._add_sample_task(1,1, "T2")
        self.assertTrue(self.tm.add_dependency(t1, t2)) # 第一次添加
        self.assertEqual(self.tm._in_degree[t2], 1)
        self.assertEqual(self.tm._tasks[t2].status, TASK_STATUS_PENDING)
        self.assertFalse(t2 in self.tm._ready_queue)

        # 重复添加同一个活跃依赖
        self.assertTrue(self.tm.add_dependency(t1, t2)) 
        # in_degree 不应再次增加，状态不应改变
        self.assertEqual(self.tm._in_degree[t2], 1, "重复添加活跃依赖不应增加in_degree")
        self.assertEqual(self.tm._tasks[t2].status, TASK_STATUS_PENDING)
        self.assertFalse(t2 in self.tm._ready_queue)

    def test_remove_dependency_makes_task_ready(self):
        """测试移除依赖后，任务变为就绪状态。"""
        t1 = self._add_sample_task(1,1,"T1")
        t2 = self._add_sample_task(1,1,"T2")
        t3 = self._add_sample_task(1,1,"T3")
        
        self.tm.add_dependency(t1, t3) # T3 依赖 T1
        self.tm.add_dependency(t2, t3) # T3 依赖 T2
        
        self.assertEqual(self.tm._in_degree[t3], 2)
        self.assertEqual(self.tm._tasks[t3].status, TASK_STATUS_PENDING)
        self.assertFalse(t3 in self.tm._ready_queue)

        # 移除 T1 -> T3，但 T2 -> T3 仍然存在 (假设 T1, T2 都未完成)
        self.assertTrue(self.tm.remove_dependency(t1, t3))
        self.assertEqual(self.tm._in_degree[t3], 1)
        self.assertEqual(self.tm._tasks[t3].status, TASK_STATUS_PENDING)
        self.assertFalse(t3 in self.tm._ready_queue)

        # 移除 T2 -> T3，现在 T3 应该就绪 (假设 T2 未完成)
        self.assertTrue(self.tm.remove_dependency(t2, t3))
        self.assertEqual(self.tm._in_degree[t3], 0)
        self.assertEqual(self.tm._tasks[t3].status, TASK_STATUS_READY)
        self.assertTrue(t3 in self.tm._ready_queue)

    def test_mark_task_as_completed(self):
        """测试标记任务完成及其对后续任务的影响。"""
        t1 = self._add_sample_task(10,1,"T1") # P=10
        t2 = self._add_sample_task(5,1,"T2")  # P=5
        t3 = self._add_sample_task(20,1,"T3") # P=20
        
        self.tm.add_dependency(t1, t2) # T1 -> T2
        self.tm.add_dependency(t1, t3) # T1 -> T3

        # 初始状态：T1 READY, T2 PENDING (in=1), T3 PENDING (in=1)
        self.assertEqual(self.tm._tasks[t1].status, TASK_STATUS_READY)
        self.assertEqual(self.tm._tasks[t2].status, TASK_STATUS_PENDING)
        self.assertEqual(self.tm._tasks[t3].status, TASK_STATUS_PENDING)
        self.assertTrue(t1 in self.tm._ready_queue)
        self.assertFalse(t2 in self.tm._ready_queue)
        self.assertFalse(t3 in self.tm._ready_queue)

        # 准备标记 T1 完成。为了模拟真实场景，T1 应该是从 ready_queue 中取出的。
        # 但这里我们直接测试 mark_task_as_completed。
        # 我们需要确保 T1 的状态是 READY，这在 _add_sample_task 中已保证（如果无依赖）。
        self.assertTrue(self.tm.mark_task_as_completed(t1))
        
        # 验证 T1 的状态
        self.assertEqual(self.tm._tasks[t1].status, TASK_STATUS_COMPLETED)
        
        # **关键点：mark_task_as_completed 不负责将 t1 从 ready_queue 中移除。**
        # **execute_next_highest_priority_task 才负责移除。**
        # 所以，如果 ready_queue 的 delete 不是由 mark_task_as_completed 触发，
        # 那么 t1 可能仍然在队列中，或者它的存在与否取决于 extract_max 的行为。
        # 但如果一个任务 COMPLETED 了，它理论上不应该再被视为“就绪”去执行。
        # 这是一个需要厘清的设计点：mark_task_as_completed 是否应该假设任务已被从队列取出？
        # 当前 TaskManager.mark_task_as_completed 检查 task_to_complete.status != TASK_STATUS_READY 时会返回False。
        # 所以，调用 mark_task_as_completed 前，任务必须是 READY。
        # 该方法本身不从 ready_queue 移除。
        
        # 让我们检查 _ready_queue 的行为。
        # 如果我们期望 mark_task_as_completed 不改变 t1 在队列中的存在性（只是改变状态）：
        # self.assertTrue(t1 in self.tm._ready_queue) # 这会是 True
        # 但这可能不是我们想要的，一个COMPLETED的任务不应该在READY队列。

        # 更好的做法是，测试 "execute_next_highest_priority_task" 时，
        # 再验证任务是否从队列中移除。
        # 对于 mark_task_as_completed，我们主要关注其对 *后继任务* 的影响。

        # T2 和 T3 应该变为 READY 并加入队列
        self.assertEqual(self.tm._in_degree[t2], 0)
        self.assertEqual(self.tm._tasks[t2].status, TASK_STATUS_READY)
        self.assertTrue(t2 in self.tm._ready_queue)
        
        self.assertEqual(self.tm._in_degree[t3], 0)
        self.assertEqual(self.tm._tasks[t3].status, TASK_STATUS_READY)
        self.assertTrue(t3 in self.tm._ready_queue)
        
        # 尝试标记一个 PENDING 任务为完成，应该失败
        t4 = self._add_sample_task(1,1,"T4")
        self.tm.add_dependency(t2, t4) # T2 -> T4, T2 此时是 READY
                                        # 所以 add_dependency(t2,t4) 时，由于 t2 未完成，t4 入度为1，状态 PENDING
        self.assertFalse(self.tm.mark_task_as_completed(t4), "不应能标记 PENDING 任务为完成")
        
        # 尝试标记一个已经是 COMPLETED 的任务 (t1)
        self.assertTrue(self.tm.mark_task_as_completed(t1), "标记已完成的任务应返回 True (幂等)")


    def test_execute_next_highest_priority_task(self):
        """测试执行最高优先级任务。"""
        t1 = self._add_sample_task(10, 5, "T1_High") # P=50
        t2 = self._add_sample_task(20, 1, "T2_Mid")  # P=20
        t3 = self._add_sample_task(5, 1, "T3_Low")   # P=5
        
        executed_task = self.tm.execute_next_highest_priority_task()
        self.assertIsNotNone(executed_task)
        self.assertEqual(executed_task.task_id, t1)
        self.assertEqual(self.tm._tasks[t1].status, TASK_STATUS_COMPLETED)
        self.assertFalse(t1 in self.tm._ready_queue)

        executed_task = self.tm.execute_next_highest_priority_task()
        self.assertEqual(executed_task.task_id, t2)
        
        executed_task = self.tm.execute_next_highest_priority_task()
        self.assertEqual(executed_task.task_id, t3)

        self.assertIsNone(self.tm.execute_next_highest_priority_task(), "队列为空时应返回None")

    def test_get_top_k_ready_tasks(self):
        """测试查看最高优先级的 k 个任务。"""
        t1 = self._add_sample_task(10, 5, "T1_50") # P=50
        t2 = self._add_sample_task(20, 4, "T2_80") # P=80
        t3 = self._add_sample_task(5, 10, "T3_50") # P=50
        t4 = self._add_sample_task(60, 1, "T4_60") # P=60
        t5 = self._add_sample_task(1, 1, "T5_1")   # P=1
        
        # 当前就绪队列中应有5个任务

        # 查看 top 3
        top_3 = self.tm.get_top_k_ready_tasks(3)
        self.assertEqual(len(top_3), 3)
        # 优先级顺序应为 T2(80), T4(60), T1(50) 或 T3(50)
        self.assertEqual(top_3[0].task_id, t2)
        self.assertEqual(top_3[1].task_id, t4)
        self.assertIn(top_3[2].task_id, {t1, t3}) # 第三个可能是 T1 或 T3

        # 确保原队列未被永久改变
        self.assertEqual(self.tm._ready_queue.get_heap_size(), 5)
        priority, task_id = self.tm._ready_queue.peek_max() # 最高优先级应仍是 T2
        self.assertEqual(task_id, t2)
        self.assertAlmostEqual(priority, 80.0)

        # 查看 top 10 (队列中只有5个)
        top_10 = self.tm.get_top_k_ready_tasks(10)
        self.assertEqual(len(top_10), 5)
        self.assertEqual(top_10[0].task_id, t2) # 顺序应该保持

        # 测试 k <= 0
        with self.assertRaisesRegex(ValueError, "k必须是正整数"):
            self.tm.get_top_k_ready_tasks(0)
        with self.assertRaisesRegex(ValueError, "k必须是正整数"):
            self.tm.get_top_k_ready_tasks(-1)


    def test_update_task_info_priority_and_queue(self):
        """测试更新任务信息导致优先级变化和在就绪队列中的调整。"""
        t1 = self._add_sample_task(10, 1, "T1") # P=10
        t2 = self._add_sample_task(50, 1, "T2") # P=50, Max
        
        self.assertEqual(self.tm._ready_queue.peek_max()[1], t2)

        # 提高 T1 的优先级，使其超过 T2
        self.assertTrue(self.tm.update_task_info(t1, new_urgency=60)) # New P(T1) = 60 * 1 = 60
        self.assertEqual(self.tm._tasks[t1].priority, 60.0)
        self.assertEqual(self.tm._ready_queue.peek_max()[1], t1) # T1 现在是最高

        # 降低 T1 的优先级，使其低于 T2
        self.assertTrue(self.tm.update_task_info(t1, new_urgency=4)) # New P(T1) = 4 * 1 = 4
        self.assertEqual(self.tm._tasks[t1].priority, 4.0)
        self.assertEqual(self.tm._ready_queue.peek_max()[1], t2) # T2 重新成为最高

    def test_update_task_info_for_pending_task(self):
        """测试更新 PENDING 状态任务的优先级（不应影响就绪队列）。"""
        t1 = self._add_sample_task(10, 1, "T1")
        t2 = self._add_sample_task(5, 1, "T2")
        self.tm.add_dependency(t1, t2) # T2 变为 PENDING

        self.assertFalse(t2 in self.tm._ready_queue)
        old_t2_priority = self.tm._tasks[t2].priority

        # 更新 T2 的优先级
        self.assertTrue(self.tm.update_task_info(t2, new_urgency=100)) # P(T2) 现在很高
        self.assertNotEqual(self.tm._tasks[t2].priority, old_t2_priority)
        self.assertFalse(t2 in self.tm._ready_queue, "PENDING 任务更新优先级后不应进入就绪队列")


    def test_delete_task_simple(self):
        """测试删除任务。"""
        t1 = self._add_sample_task(10, 1, "T1")
        t2 = self._add_sample_task(5, 1, "T2")
        
        self.assertTrue(self.tm.delete_task(t1))
        self.assertNotIn(t1, self.tm._tasks)
        self.assertNotIn(t1, self.tm._ready_queue)
        self.assertNotIn(t1, self.tm._in_degree)
        self.assertFalse(self.tm._task_graph.has_task(t1))
        self.assertEqual(self.tm._ready_queue.get_heap_size(), 1) # 只剩 T2
        
        self.assertFalse(self.tm.delete_task("non_existent_task"))

    def test_delete_task_with_dependencies_updates_dependents(self):
        """测试删除任务时，其后继任务的入度和就绪状态被正确更新。"""
        t1 = self._add_sample_task(1,1,"T1_Prereq")
        t2 = self._add_sample_task(1,1,"T2_Dependent")
        t3 = self._add_sample_task(1,1,"T3_AlsoDependent")
        t4 = self._add_sample_task(1,1,"T4_AnotherPrereq")

        self.tm.add_dependency(t1, t2) # T1 -> T2
        self.tm.add_dependency(t1, t3) # T1 -> T3
        self.tm.add_dependency(t4, t2) # T4 -> T2

        # T2 依赖 T1, T4. T3 依赖 T1.
        # 初始: T1, T4 READY. T2, T3 PENDING.
        # in_degree: T2=2, T3=1
        self.assertEqual(self.tm._in_degree[t2], 2)
        self.assertEqual(self.tm._tasks[t2].status, TASK_STATUS_PENDING)
        self.assertEqual(self.tm._in_degree[t3], 1)
        self.assertEqual(self.tm._tasks[t3].status, TASK_STATUS_PENDING)

        # 删除 T1
        self.assertTrue(self.tm.delete_task(t1))
        
        # T2 现在只依赖 T4 (因为 T1 被删除，T1->T2 依赖消失)
        self.assertEqual(self.tm._in_degree[t2], 1, "T2的入度应因T1删除而减少")
        self.assertEqual(self.tm._tasks[t2].status, TASK_STATUS_PENDING, "T2仍应PENDING因为它还依赖T4")
        
        # T3 现在应该变为 READY (因为它唯一的依赖 T1 被删除)
        self.assertEqual(self.tm._in_degree[t3], 0, "T3的入度应因T1删除而变为0")
        self.assertEqual(self.tm._tasks[t3].status, TASK_STATUS_READY, "T3应变为READY")
        self.assertTrue(t3 in self.tm._ready_queue)
        
        # 再次删除 T4
        self.assertTrue(self.tm.delete_task(t4))
        # T2 现在应该变为 READY (因为它唯一的依赖 T4 被删除)
        self.assertEqual(self.tm._in_degree[t2], 0, "T2的入度应因T4删除而变为0")
        self.assertEqual(self.tm._tasks[t2].status, TASK_STATUS_READY, "T2应变为READY")
        self.assertTrue(t2 in self.tm._ready_queue)


if __name__ == '__main__':
    # 为了让这个测试文件能独立运行，你需要确保以下类可以被导入：
    # MarketingTask, TaskManager, TASK_STATUS_* (来自你的 marketing_task_schedule.py)
    # UpdatableMaxHeap (来自你的 updatable_max_heap.py)
    # TaskDependencyGraph (来自你的 dependency_graph.py)
    # 这通常意味着你的 src 目录在 PYTHONPATH 中，或者你从项目根目录运行测试。
    unittest.main()