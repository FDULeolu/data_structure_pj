import unittest
from src.data_structure.dependency_graph import TaskDependencyGraph

class TestTaskDependencyGraph(unittest.TestCase):

    def setUp(self):
        """在每个测试方法运行前初始化一个空的依赖图。"""
        self.graph = TaskDependencyGraph()

    # --- 测试 add_task ---
    def test_add_task_new(self):
        """测试添加一个新任务节点。"""
        self.assertTrue(self.graph.add_task("T1"))
        self.assertIn("T1", self.graph.nodes)
        self.assertIn("T1", self.graph.adj)
        self.assertIn("T1", self.graph.rev_adj)
        self.assertEqual(self.graph.adj["T1"], set())
        self.assertEqual(self.graph.rev_adj["T1"], set())
        self.assertEqual(len(self.graph.nodes), 1)

    def test_add_task_existing(self):
        """测试添加一个已存在的任务节点。"""
        self.graph.add_task("T1")
        self.assertFalse(self.graph.add_task("T1")) # 再次添加应返回 False
        self.assertEqual(len(self.graph.nodes), 1) # 节点数量不应改变

    # --- 测试 remove_task ---
    def test_remove_task_non_existent(self):
        """测试移除一个不存在的任务节点。"""
        with self.assertRaisesRegex(IndexError, "节点 T_non_existent 不存在"):
            self.graph.remove_task("T_non_existent")

    def test_remove_task_isolated(self):
        """测试移除一个孤立的任务节点。"""
        self.graph.add_task("T1")
        removed_id = self.graph.remove_task("T1")
        self.assertEqual(removed_id, "T1")
        self.assertNotIn("T1", self.graph.nodes)
        self.assertNotIn("T1", self.graph.adj)
        self.assertNotIn("T1", self.graph.rev_adj)
        self.assertTrue(not self.graph.nodes) # 集合应为空

    def test_remove_task_with_dependencies(self):
        """测试移除有依赖关系的任务节点。"""
        self.graph.add_task("T1")
        self.graph.add_task("T2")
        self.graph.add_task("T3")
        self.graph.add_task("T4")
        self.graph.add_dependency("T1", "T2") # T1 -> T2
        self.graph.add_dependency("T3", "T2") # T3 -> T2
        self.graph.add_dependency("T2", "T4") # T2 -> T4

        # 移除 T2
        removed_id = self.graph.remove_task("T2")
        self.assertEqual(removed_id, "T2")
        self.assertNotIn("T2", self.graph.nodes)
        self.assertNotIn("T2", self.graph.adj)
        self.assertNotIn("T2", self.graph.rev_adj)

        # 检查其他节点的依赖是否正确更新
        self.assertNotIn("T2", self.graph.adj.get("T1", set()))
        self.assertNotIn("T2", self.graph.adj.get("T3", set()))
        self.assertNotIn("T2", self.graph.rev_adj.get("T4", set()))

        # 确保其他节点和依赖还在
        self.assertTrue(self.graph.has_task("T1"))
        self.assertTrue(self.graph.has_task("T3"))
        self.assertTrue(self.graph.has_task("T4"))
        self.assertEqual(self.graph.adj["T1"], set()) # T1 不再指向 T2
        self.assertEqual(self.graph.rev_adj["T4"], set()) # T4 不再依赖 T2

    # --- 测试 add_dependency ---
    def test_add_dependency_valid(self):
        """测试添加有效的依赖关系。"""
        self.graph.add_task("T1")
        self.graph.add_task("T2")
        self.assertTrue(self.graph.add_dependency("T1", "T2"))
        self.assertIn("T2", self.graph.adj["T1"])
        self.assertIn("T1", self.graph.rev_adj["T2"])

    def test_add_dependency_node_non_existent(self):
        """测试添加依赖时节点不存在。"""
        self.graph.add_task("T1")
        self.assertFalse(self.graph.add_dependency("T1", "T_non")) # T_non 不存在
        self.assertFalse(self.graph.add_dependency("T_non", "T1")) # T_non 不存在
        self.assertEqual(self.graph.adj["T1"], set()) # 确认没有添加成功
        self.assertEqual(self.graph.rev_adj["T1"], set())

    def test_add_dependency_self_loop(self):
        """测试添加自环依赖。"""
        self.graph.add_task("T1")
        self.assertFalse(self.graph.add_dependency("T1", "T1")) # 不应允许自环
        self.assertEqual(self.graph.adj["T1"], set())
        self.assertEqual(self.graph.rev_adj["T1"], set())

    def test_add_dependency_existing(self):
        """测试添加已存在的依赖。"""
        self.graph.add_task("T1")
        self.graph.add_task("T2")
        self.graph.add_dependency("T1", "T2")
        # 再次添加应返回 True，但集合大小不变
        self.assertTrue(self.graph.add_dependency("T1", "T2"))
        self.assertEqual(len(self.graph.adj["T1"]), 1)
        self.assertEqual(len(self.graph.rev_adj["T2"]), 1)

    def test_add_dependency_creates_cycle_simple(self):
        """测试添加依赖导致简单环路。"""
        self.graph.add_task("T1")
        self.graph.add_task("T2")
        self.graph.add_dependency("T1", "T2")
        self.assertFalse(self.graph.add_dependency("T2", "T1")) # 添加 T2->T1 会形成环路
        # 确认 T2->T1 未被添加
        self.assertNotIn("T1", self.graph.adj["T2"])
        self.assertNotIn("T2", self.graph.rev_adj["T1"])

    def test_add_dependency_creates_cycle_longer(self):
        """测试添加依赖导致长环路。"""
        self.graph.add_task("T1")
        self.graph.add_task("T2")
        self.graph.add_task("T3")
        self.graph.add_task("T4")
        self.graph.add_dependency("T1", "T2")
        self.graph.add_dependency("T2", "T3")
        self.graph.add_dependency("T3", "T4")
        self.assertFalse(self.graph.add_dependency("T4", "T1")) # 添加 T4->T1 会形成 T1->T2->T3->T4->T1 环路
        self.assertNotIn("T1", self.graph.adj["T4"])
        self.assertNotIn("T4", self.graph.rev_adj["T1"])

    def test_add_dependency_no_cycle(self):
        """测试添加不会导致环路的依赖。"""
        self.graph.add_task("T1")
        self.graph.add_task("T2")
        self.graph.add_task("T3")
        self.graph.add_task("T4")
        self.graph.add_dependency("T1", "T2")
        self.graph.add_dependency("T1", "T3")
        self.graph.add_dependency("T2", "T4")
        self.graph.add_dependency("T3", "T4")
        # 添加 T1 -> T4 不会形成环路
        self.assertTrue(self.graph.add_dependency("T1", "T4"))
        self.assertIn("T4", self.graph.adj["T1"])
        self.assertIn("T1", self.graph.rev_adj["T4"])

    # --- 测试 remove_dependency ---
    def test_remove_dependency_valid(self):
        """测试移除存在的依赖关系。"""
        self.graph.add_task("T1")
        self.graph.add_task("T2")
        self.graph.add_dependency("T1", "T2")
        self.assertTrue(self.graph.remove_dependency("T1", "T2"))
        self.assertNotIn("T2", self.graph.adj["T1"])
        self.assertNotIn("T1", self.graph.rev_adj["T2"])

    def test_remove_dependency_non_existent_edge(self):
        """测试移除不存在的依赖关系（节点存在）。"""
        self.graph.add_task("T1")
        self.graph.add_task("T2")
        self.assertFalse(self.graph.remove_dependency("T1", "T2")) # T1->T2 不存在

    def test_remove_dependency_non_existent_node(self):
        """测试移除依赖时节点不存在。"""
        self.graph.add_task("T1")
        self.assertFalse(self.graph.remove_dependency("T1", "T_non"))
        self.assertFalse(self.graph.remove_dependency("T_non", "T1"))

    # --- 测试查询方法 ---
    def test_get_dependents_and_prerequisites(self):
        """测试 get_dependents 和 get_prerequisites 方法。"""
        self.graph.add_task("T1")
        self.graph.add_task("T2")
        self.graph.add_task("T3")
        self.graph.add_dependency("T1", "T2")
        self.graph.add_dependency("T1", "T3")
        self.graph.add_dependency("T2", "T3")

        self.assertEqual(self.graph.get_dependents("T1"), {"T2", "T3"})
        self.assertEqual(self.graph.get_dependents("T2"), {"T3"})
        self.assertEqual(self.graph.get_dependents("T3"), set())

        self.assertEqual(self.graph.get_prerequisites("T1"), set())
        self.assertEqual(self.graph.get_prerequisites("T2"), {"T1"})
        self.assertEqual(self.graph.get_prerequisites("T3"), {"T1", "T2"})

        # 测试不存在的节点
        self.assertEqual(self.graph.get_dependents("T_non"), set())
        self.assertEqual(self.graph.get_prerequisites("T_non"), set())

    def test_get_methods_return_copy(self):
        """测试 get_dependents/prerequisites 返回的是副本。"""
        self.graph.add_task("T1")
        self.graph.add_task("T2")
        self.graph.add_dependency("T1", "T2")

        dependents = self.graph.get_dependents("T1")
        dependents.add("T_fake")
        self.assertEqual(self.graph.get_dependents("T1"), {"T2"}) # 原图不应被修改

        prereqs = self.graph.get_prerequisites("T2")
        prereqs.add("T_fake")
        self.assertEqual(self.graph.get_prerequisites("T2"), {"T1"}) # 原图不应被修改


    def test_has_task(self):
        """测试 has_task 方法。"""
        self.assertFalse(self.graph.has_task("T1"))
        self.graph.add_task("T1")
        self.assertTrue(self.graph.has_task("T1"))
        self.graph.remove_task("T1")
        self.assertFalse(self.graph.has_task("T1"))

    def test_get_all_tasks(self):
        """测试 get_all_tasks 方法。"""
        self.assertEqual(self.graph.get_all_tasks(), [])
        self.graph.add_task("T1")
        self.graph.add_task("T3")
        self.graph.add_task("T2")
        # 返回列表，顺序不保证，所以比较集合
        self.assertEqual(set(self.graph.get_all_tasks()), {"T1", "T2", "T3"})
        self.assertEqual(len(self.graph.get_all_tasks()), 3)
        self.graph.remove_task("T2")
        self.assertEqual(set(self.graph.get_all_tasks()), {"T1", "T3"})

    # --- 测试 _has_path (间接通过 add_dependency, 但也可以补充直接测试) ---
    def test_has_path_direct(self):
        """直接测试 _has_path：直接路径。"""
        self.graph.add_task("A"); self.graph.add_task("B")
        self.graph.add_dependency("A", "B")
        self.assertTrue(self.graph._has_path("A", "B"))
        self.assertFalse(self.graph._has_path("B", "A"))

    def test_has_path_indirect(self):
        """直接测试 _has_path：间接路径。"""
        self.graph.add_task("A"); self.graph.add_task("B"); self.graph.add_task("C")
        self.graph.add_dependency("A", "B")
        self.graph.add_dependency("B", "C")
        self.assertTrue(self.graph._has_path("A", "C"))
        self.assertFalse(self.graph._has_path("C", "A"))

    def test_has_path_no_path(self):
        """直接测试 _has_path：不存在路径。"""
        self.graph.add_task("A"); self.graph.add_task("B"); self.graph.add_task("C")
        self.graph.add_dependency("A", "B")
        self.assertFalse(self.graph._has_path("A", "C"))
        self.assertFalse(self.graph._has_path("C", "A"))

    def test_has_path_with_cycle(self):
        """直接测试 _has_path：在有环图中查找路径。"""
        # Setup graph nodes
        self.graph.add_task("A"); self.graph.add_task("B"); self.graph.add_task("C")
        self.graph.add_task("D")

        # Manually create the cyclic structure for testing _has_path
        # Bypassing add_dependency's cycle check for this specific test case setup
        self.graph.adj["A"].add("B")
        self.graph.rev_adj["B"].add("A")

        self.graph.adj["B"].add("C")
        self.graph.rev_adj["C"].add("B")

        self.graph.adj["C"].add("A") # Manually add the edge that forms the cycle
        self.graph.rev_adj["A"].add("C")

        self.graph.adj["C"].add("D") # Add the exit edge
        self.graph.rev_adj["D"].add("C")
        
        # Now the graph truly contains the cycle A->B->C->A and edge C->D

        # --- Assertions on the cyclic graph ---
        
        # Can we reach D from A? (A -> B -> C -> D) - YES
        self.assertTrue(self.graph._has_path("A", "D"), "应能找到路径 A->D")

        # Can we reach A from A (via cycle)?
        self.assertTrue(self.graph._has_path("A", "A"), "_has_path(node, node) 应返回 True")

        # Can we reach A from B? (B -> C -> A) - YES
        self.assertTrue(self.graph._has_path("B", "A"), "应能找到路径 B->A") # 现在这个断言应该通过了

        # Can we reach A from D? (D has no outgoing edges) - NO
        self.assertFalse(self.graph._has_path("D", "A"), "不应找到路径 D->A")


if __name__ == '__main__':
    unittest.main()