import unittest
from src.data_structure.customer_graph import CustomerGraph 
from src.module.customer_network_analysis import analyze_all_customer_influence_nodes 

class TestInfluenceSpreadAnalysis(unittest.TestCase):

    def setUp(self):
        """
        在每个测试方法运行前调用，用于设置测试环境。
        """
        self.graph = CustomerGraph()

    def test_analyze_all_param_validation_invalid_graph(self):
        """测试 analyze_all_customer_influence_nodes 函数传入无效的图类型"""
        with self.assertRaisesRegex(TypeError, "输入图必须是 CustomerGraph 对象"):
            analyze_all_customer_influence_nodes("not_a_graph", 0.5)

    def test_analyze_all_param_validation_invalid_min_influence(self):
        """测试 analyze_all_customer_influence_nodes 函数传入无效的 min_influence"""
        self.graph.add_customer("A")
        with self.assertRaisesRegex(ValueError, "min_influence 必须属于0和1之间"):
            analyze_all_customer_influence_nodes(self.graph, -0.1)
        with self.assertRaisesRegex(ValueError, "min_influence 必须属于0和1之间"):
            analyze_all_customer_influence_nodes(self.graph, 1.1)
        # 测试有效的边界值 (0, 1] - 你的代码实现意味着 min_influence=1 是有效的
        # 如果 min_influence == 1 是有效的：
        try:
            analyze_all_customer_influence_nodes(self.graph, 1.0) # 不应抛出异常
            analyze_all_customer_influence_nodes(self.graph, 0.0001) # 不应抛出异常
        except ValueError:
            self.fail("有效的 min_influence (例如 0.0001 或 1.0) 意外地引发了 ValueError")


    def test_empty_graph(self):
        """测试空图的情况"""
        result = analyze_all_customer_influence_nodes(self.graph, 0.1)
        self.assertEqual(result, {})

    def test_single_node_graph(self):
        """测试只包含一个节点的图"""
        self.graph.add_customer("A")
        result = analyze_all_customer_influence_nodes(self.graph, 0.1)
        self.assertEqual(result, {"A": set()})

    def test_two_nodes_no_influence_below_threshold(self):
        """测试 A->B，但影响力低于阈值的情况"""
        self.graph.add_influence("A", "B", 0.05)
        result = analyze_all_customer_influence_nodes(self.graph, 0.1)
        expected = {
            "A": set(),
            "B": set()
        }
        self.assertEqual(result, expected)

    def test_two_nodes_influence_at_threshold(self):
        """测试 A->B，影响力恰好等于阈值的情况"""
        self.graph.add_influence("A", "B", 0.1)
        result = analyze_all_customer_influence_nodes(self.graph, 0.1)
        expected = {
            "A": {"B"},
            "B": set()
        }
        self.assertEqual(result, expected)

    def test_two_nodes_influence_above_threshold(self):
        """测试 A->B，影响力高于阈值的情况"""
        self.graph.add_influence("A", "B", 0.2)
        result = analyze_all_customer_influence_nodes(self.graph, 0.1)
        expected = {
            "A": {"B"},
            "B": set()
        }
        self.assertEqual(result, expected)

    def test_chain_influence_A_B_C(self):
        """测试链式影响 A->B->C 在不同阈值下的情况"""
        self.graph.add_influence("A", "B", 0.5)
        self.graph.add_influence("B", "C", 0.4) # A->B->C 的路径影响力 = 0.5 * 0.4 = 0.2
        self.graph.add_customer("D") # 未连接的节点

        # 情况1: min_influence = 0.3 (A 无法影响到 C，因为 0.2 < 0.3)
        result1 = analyze_all_customer_influence_nodes(self.graph, 0.3)
        expected1 = {
            "A": {"B"},          # A->B (0.5) 符合条件
            "B": {"C"},          # B->C (0.4) 符合条件
            "C": set(),
            "D": set()
        }
        self.assertEqual(result1, expected1)
        
        # 情况2: min_influence = 0.1 (A 可以影响到 C)
        result2 = analyze_all_customer_influence_nodes(self.graph, 0.1)
        expected2 = {
            "A": {"B", "C"},    # A->B (0.5), A->B->C (0.2)
            "B": {"C"},         # B->C (0.4)
            "C": set(),
            "D": set()
        }
        self.assertEqual(result2, expected2)

        # 情况3: min_influence = 0.45 (A 无法影响到 C, B 无法影响到 C)
        result3 = analyze_all_customer_influence_nodes(self.graph, 0.45)
        expected3 = {
            "A": {"B"},        # A->B (0.5)
            "B": set(),        # B->C (0.4) < 0.45
            "C": set(),
            "D": set()
        }
        self.assertEqual(result3, expected3)

    def test_branch_and_merge(self):
        """测试分支与合并路径 A->B, A->C, B->D, C->D"""
        self.graph.add_influence("A", "B", 0.6)
        self.graph.add_influence("A", "C", 0.3)
        self.graph.add_influence("B", "D", 0.5) # A->B->D 路径影响力 = 0.6 * 0.5 = 0.3
        self.graph.add_influence("C", "D", 0.9) # A->C->D 路径影响力 = 0.3 * 0.9 = 0.27

        # min_influence = 0.25
        result = analyze_all_customer_influence_nodes(self.graph, 0.25)
        expected = {
            "A": {"B", "C", "D"}, # B (0.6), C (0.3), D 可通过 A->B->D (0.3) 和 A->C->D (0.27) 到达
            "B": {"D"},           # D (0.5)
            "C": {"D"},           # D (0.9)
            "D": set()
        }
        self.assertEqual(result, expected)

        # min_influence = 0.28 (A->C->D 这条路径被剪枝)
        result_stricter = analyze_all_customer_influence_nodes(self.graph, 0.28)
        expected_stricter = {
            "A": {"B", "C", "D"}, # B (0.6), C (0.3), D 只能通过 A->B->D (0.3) 到达
            "B": {"D"},           # D (0.5)
            "C": {"D"},           # D (0.9)
            "D": set()
        }
        self.assertEqual(result_stricter, expected_stricter)


    def test_cycle_handling(self):
        """测试包含环路的图 A->B, B->A"""
        self.graph.add_influence("A", "B", 0.8)
        self.graph.add_influence("B", "A", 0.7) # A->B->A 路径影响力 = 0.8 * 0.7 = 0.56
        self.graph.add_influence("A", "C", 0.2) # A->C 路径影响力 = 0.2

        # min_influence = 0.1
        result = analyze_all_customer_influence_nodes(self.graph, 0.1)
        # A 能影响: B (0.8), C (0.2)
        # B 能影响: A (0.7)
        # A 通过 A->B->A (0.56) 也能影响到 A，但起始节点不计入其自身的影响集合。
        expected = {
            "A": {"B", "C"},
            "B": {"A", "C"}, 
            "C": set()
        }
        self.assertEqual(result, expected)

    def test_cycle_with_exit_path(self):
        """测试包含环路并有出口的路径 A->B, B->C, C->B (B-C形成环), B->D"""
        self.graph.add_influence("A", "B", 0.9)
        self.graph.add_influence("B", "C", 0.8) # A->B->C 路径影响力 = 0.72
        self.graph.add_influence("C", "B", 0.7) # A->B->C->B 路径影响力 = 0.72 * 0.7 = 0.504
        self.graph.add_influence("B", "D", 0.6) # A->B->D 路径影响力 = 0.9 * 0.6 = 0.54
                                            # A->B->C->B->D 路径影响力 = 0.504 * 0.6 = 0.3024

        # min_influence = 0.3
        result = analyze_all_customer_influence_nodes(self.graph, 0.3)
        # A 能影响 B (0.9)
        # A 能影响 C (通过 A->B->C = 0.72)
        # A 能影响 D (通过 A->B->D = 0.54 和 A->B->C->B->D = 0.3024)
        # B 能影响 C (0.8)
        # B 能影响 D (0.6)
        # C 能影响 B (0.7)
        # C 能影响 D (通过 C->B->D = 0.7 * 0.6 = 0.42)
        expected = {
            "A": {"B", "C", "D"},
            "B": {"C", "D"}, 
            "C": {"B", "D"}, 
            "D": set()
        }
        self.assertEqual(result, expected)

    def test_self_loop(self):
        """测试包含自环的图 A->A"""
        self.graph.add_influence("A", "A", 0.9) # 自环
        self.graph.add_influence("A", "B", 0.5)
        
        result = analyze_all_customer_influence_nodes(self.graph, 0.1)
        # A 能影响 B (0.5)。根据题目“其他客户”，A 不把自己算作被影响者。
        # 通过 A->A->B (0.9*0.5 = 0.45) 也是 A 影响 B 的一条路径。
        expected = {
            "A": {"B"},
            "B": set()
        }
        self.assertEqual(result, expected)

    def test_zero_weight_edge_pruning(self):
        """测试当路径中某条边权重为0时，路径被剪枝的情况"""
        self.graph.add_influence("A", "B", 1.0)
        self.graph.add_influence("B", "C", 0.0) # 这条边使得 A->B->C 路径影响力为 0
        self.graph.add_influence("C", "D", 1.0)
        self.graph.add_influence("A", "E", 0.5)

        # min_influence 必须为正数 (例如，0.01，根据你代码中的校验)
        result = analyze_all_customer_influence_nodes(self.graph, 0.01)
        # A 能影响 B (1.0)
        # A 能影响 E (0.5)
        # A 不能通过 B 影响到 C 或 D，因为 A->B->C 的路径影响力是 0。
        # B 不能影响 C 或 D。
        # C 能影响 D (1.0)
        expected = {
            "A": {"B", "E"},
            "B": set(),
            "C": {"D"},
            "D": set(),
            "E": set()
        }
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()