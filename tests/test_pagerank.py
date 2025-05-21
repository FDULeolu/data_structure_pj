import unittest
import math # 用于 isclose 比较浮点数总和

from src.data_structure.customer_graph import CustomerGraph
from src.module.customer_network_analysis import (
    _preprocess_for_pagerank,                 
    calculate_pagerank
)


class TestPageRankAnalysis(unittest.TestCase):

    def setUp(self):
        self.graph = CustomerGraph()
        # 常用的 PageRank 参数
        self.damping_factor = 0.85
        self.max_iterations = 100 # 使用一个合理的迭代次数进行测试
        self.epsilon = 1e-7 # 一个较小的 epsilon

    def test_pagerank_parameter_validation(self):
        """测试 calculate_pagerank 函数的参数校验"""
        with self.assertRaisesRegex(TypeError, "输入必须是一个 CustomerGraph 对象"):
            calculate_pagerank("not_a_graph")
        
        g = CustomerGraph()
        g.add_customer("A")
        
        with self.assertRaisesRegex(ValueError, "阻尼因子必须在 0 和 1 之间"):
            calculate_pagerank(g, damping_factor=1.5)
        with self.assertRaisesRegex(ValueError, "阻尼因子必须在 0 和 1 之间"):
            calculate_pagerank(g, damping_factor=0)
        with self.assertRaisesRegex(ValueError, "阻尼因子必须在 0 和 1 之间"):
            calculate_pagerank(g, damping_factor=-0.1)

        with self.assertRaisesRegex(ValueError, "最大迭代次数必须大于 0"):
            calculate_pagerank(g, max_iterations=0)
        with self.assertRaisesRegex(ValueError, "最大迭代次数必须大于 0"):
            calculate_pagerank(g, max_iterations=-5)

        with self.assertRaisesRegex(ValueError, "Epsilon 必须大于 0"):
            calculate_pagerank(g, epsilon=0)
        with self.assertRaisesRegex(ValueError, "Epsilon 必须大于 0"):
            calculate_pagerank(g, epsilon=-0.001)

    def test_pagerank_empty_graph(self):
        """测试空图的 PageRank"""
        self.assertEqual(calculate_pagerank(self.graph), {})

    def test_pagerank_single_node_graph(self):
        """测试单个节点的图的 PageRank"""
        self.graph.add_customer("A")
        expected_pagerank = {"A": 1.0 / 1.0} # 初始为 1/N，迭代后应保持
        # 对于单个节点，没有入链，没有悬挂节点贡献给自己，只有 (1-d)/N
        # 实际PageRank公式 (1-d)/N + d*0 + d*PR(A)/N (如果悬挂节点是这样处理的)
        # 如果悬挂节点PR(A)被分配给它自己(1/N * PR(A))，则PR(A) = (1-d)/N + d*PR(A)/N
        # PR(A)*(1-d/N) = (1-d)/N => PR(A) = (1-d)/(N-d)
        # 但对于单节点 N=1，通常其 PageRank 就是 1.0 (或 1/N)。
        # 我们的实现中，单节点出度为0，是悬挂节点。
        # PR(A) = (1-d)/1 + d * (PR(A)/1) => PR(A) = 1-d + d*PR(A) => PR(A)(1-d) = 1-d => PR(A)=1
        
        # 让我们跟踪代码逻辑：
        # pagerank_scores = {"A": 1.0}
        # dangling_nodes_pagerank_sum = 1.0
        # pagerank_from_dangling_nodes = d * (1.0 / 1.0) = d
        # pagerank_from_teleport = (1.0 - d) / 1.0 = 1.0 - d
        # pagerank_from_incoming_links = 0.0
        # new_pagerank_scores["A"] = (1.0 - d) + 0 + d = 1.0
        # 它会立即收敛到 1.0
        
        result = calculate_pagerank(self.graph, 
                                    damping_factor=self.damping_factor, 
                                    max_iterations=self.max_iterations, 
                                    epsilon=self.epsilon)
        self.assertIn("A", result)
        self.assertAlmostEqual(result["A"], 1.0, places=7)
        self.assertTrue(math.isclose(sum(result.values()), 1.0, rel_tol=1e-5))


    def test_pagerank_two_nodes_symmetric_link(self):
        """测试两个节点双向连接的 PageRank (A<->B)"""
        self.graph.add_influence("A", "B", 1.0)
        self.graph.add_influence("B", "A", 1.0)
        # 预期: A 和 B 的 PageRank 应该相等，且总和为1 (即各0.5)
        result = calculate_pagerank(self.graph, 
                                    damping_factor=self.damping_factor, 
                                    max_iterations=self.max_iterations, 
                                    epsilon=self.epsilon)
        self.assertIn("A", result)
        self.assertIn("B", result)
        self.assertAlmostEqual(result["A"], 0.5, places=5) # 精度可能会有影响
        self.assertAlmostEqual(result["B"], 0.5, places=5)
        self.assertTrue(math.isclose(sum(result.values()), 1.0, rel_tol=1e-5))

    def test_pagerank_three_nodes_loop(self):
        """测试三个节点的简单循环 (A->B, B->C, C->A)"""
        self.graph.add_influence("A", "B", 1.0)
        self.graph.add_influence("B", "C", 1.0)
        self.graph.add_influence("C", "A", 1.0)
        # 预期: A, B, C 的 PageRank 应该相等，且总和为1 (即各约1/3)
        result = calculate_pagerank(self.graph, 
                                    damping_factor=self.damping_factor, 
                                    max_iterations=self.max_iterations, 
                                    epsilon=self.epsilon)
        self.assertIn("A", result)
        self.assertIn("B", result)
        self.assertIn("C", result)
        expected_score = 1.0 / 3.0
        self.assertAlmostEqual(result["A"], expected_score, places=5)
        self.assertAlmostEqual(result["B"], expected_score, places=5)
        self.assertAlmostEqual(result["C"], expected_score, places=5)
        self.assertTrue(math.isclose(sum(result.values()), 1.0, rel_tol=1e-5))

    def test_pagerank_dangling_node_simple(self):
        """测试包含一个简单悬挂节点的 PageRank (A->B, A->C, B是悬挂节点)"""
        self.graph.add_influence("A", "B", 1.0) # B 是悬挂节点 (无出链)
        self.graph.add_influence("A", "C", 1.0)
        # A 指向 B 和 C。B 是悬挂节点。
        # C 也可能是悬挂节点，如果它没有出链。让我们让 C 指回 A 来使其不悬挂。
        self.graph.add_influence("C", "A", 1.0)

        # 节点: A, B, C
        # 初始 PR: A=1/3, B=1/3, C=1/3
        # WOD: A=2, B=0, C=1

        # 迭代1 (大致思路):
        # Dangling PR sum (from B) = PR(B) = 1/3
        # PR_dangling_contrib_per_node = d * ( (1/3) / 3 ) = d/9
        # For A: (1-d)/3 + d * (PR(C)*1/WOD(C)) + PR_dangling_contrib_per_node
        #        = (1-d)/3 + d * ( (1/3)*1/1 ) + d/9 = (1-d)/3 + d/3 + d/9 = 1/3 + d/9
        # For B (no in-links other than its own dangling contribution):
        #        = (1-d)/3 + d * (0) + PR_dangling_contrib_per_node
        #        = (1-d)/3 + d/9
        # For C: (1-d)/3 + d * (PR(A)*1/WOD(A)) + PR_dangling_contrib_per_node
        #        = (1-d)/3 + d * ( (1/3)*1/2 ) + d/9 = (1-d)/3 + d/6 + d/9
        # A 和 C 应该比 B 有更高的PR。

        result = calculate_pagerank(self.graph, 
                                    damping_factor=self.damping_factor, 
                                    max_iterations=self.max_iterations, 
                                    epsilon=self.epsilon)
        
        self.assertIn("A", result)
        self.assertIn("B", result)
        self.assertIn("C", result)
        self.assertTrue(result["A"] > result["B"] or math.isclose(result["A"], result["B"], rel_tol=1e-5)) # A should be >= B
        self.assertAlmostEqual(result["C"], result["B"], places=5, msg="PR(C) and PR(B) should be equal in this graph")
        self.assertTrue(math.isclose(sum(result.values()), 1.0, rel_tol=1e-5), 
                        f"Sum of PageRanks is not 1.0: {sum(result.values())}")

    def test_pagerank_node_with_only_zero_weight_out_edge(self):
        """测试节点的唯一出边权重为0 (应视为悬挂节点)"""
        self.graph.add_influence("A", "B", 0.0) # A 的 WOD 是 0, 所以 A 是悬挂节点
        self.graph.add_influence("C", "A", 1.0) # C 指向 A
        # 节点: A, B, C
        # WOD: A=0, B=0, C=1
        # A 和 B 都是悬挂节点

        result = calculate_pagerank(self.graph,
                                    damping_factor=self.damping_factor,
                                    max_iterations=self.max_iterations,
                                    epsilon=self.epsilon)
        self.assertIn("A", result)
        self.assertIn("B", result)
        self.assertIn("C", result)
        # 预期 C 的 PageRank 会比较高，因为它有实际的出链并且接收了随机跳转部分，
        # A 和 B 的 PageRank 主要来自随机跳转和悬挂节点的分配。
        # A 应该比 B 高，因为它有来自 C 的入链(即使 A 自身是悬挂的)。
        self.assertTrue(result["A"] > result["B"] or math.isclose(result["A"], result["B"])) # A比B高或相近
        self.assertTrue(result["C"] > result["B"] or math.isclose(result["C"], result["B"])) # C比B高或相近
        self.assertTrue(math.isclose(sum(result.values()), 1.0, rel_tol=1e-5))


    def test_pagerank_complex_graph_relative_ranks(self):
        """测试一个稍复杂图的相对 PageRank 顺序"""
        self.graph.add_influence("A", "B", 1.0)
        self.graph.add_influence("A", "C", 1.0)
        self.graph.add_influence("B", "D", 1.0)
        self.graph.add_influence("C", "D", 1.0) # D 被两个节点指向
        self.graph.add_influence("E", "A", 1.0) # E 指向 A (A 的重要性来源之一)
        self.graph.add_influence("D", "E", 0.5) # D 也指回 E 形成一个小循环
        # F 是孤立的，但通过随机跳转获得 PR
        self.graph.add_customer("F")

        # 预期 D 应该有较高的 PageRank
        # A 和 E 也会因为互相指向及 E 指向 A 而有一定 PageRank
        # B 和 C 作为中间节点
        # F 作为孤立节点，PR 应该最低（仅来自随机跳转和悬挂贡献）
        result = calculate_pagerank(self.graph, 
                                    damping_factor=self.damping_factor, 
                                    max_iterations=200, # 增加迭代次数确保收敛
                                    epsilon=self.epsilon)
        
        self.assertTrue(all(score >= 0 for score in result.values()))
        self.assertTrue(math.isclose(sum(result.values()), 1.0, rel_tol=1e-4),
                        f"Sum of PageRanks is not 1.0: {sum(result.values())}")

        # 难以精确预测，但可以做一些相对比较
        # print("\nComplex Graph PR:", {k: round(v,4) for k,v in result.items()}) # 用于调试
        if "D" in result and "F" in result:
             self.assertTrue(result["D"] > result["F"], "PR(D) should be > PR(F)")
        if "A" in result and "B" in result:
             self.assertTrue(result["A"] > result["B"] or result["A"] > result["C"], "PR(A) should be relatively high")


    def test_preprocess_function_directly(self):
        """(可选) 直接测试 _preprocess_for_pagerank 的基本功能"""
        self.graph.add_influence("A", "B", 0.5)
        self.graph.add_influence("A", "C", 1.0)
        self.graph.add_influence("X", "A", 0.8)
        self.graph.add_customer("D") # Isolated

        incoming_links_map, weighted_out_degrees = _preprocess_for_pagerank(self.graph)

        expected_incoming_A = {"X": 0.8}
        expected_incoming_B = {"A": 0.5}
        expected_incoming_C = {"A": 1.0}
        expected_incoming_D = {}
        expected_incoming_X = {}
        
        self.assertEqual(incoming_links_map.get("A", {}), expected_incoming_A)
        self.assertEqual(incoming_links_map.get("B", {}), expected_incoming_B)
        self.assertEqual(incoming_links_map.get("C", {}), expected_incoming_C)
        self.assertEqual(incoming_links_map.get("D", {}), expected_incoming_D)
        self.assertEqual(incoming_links_map.get("X", {}), expected_incoming_X)
        self.assertEqual(set(incoming_links_map.keys()), {"A", "B", "C", "X", "D"})

        expected_wod_A = 0.5 + 1.0
        expected_wod_X = 0.8
        expected_wod_B = 0.0
        expected_wod_C = 0.0
        expected_wod_D = 0.0

        self.assertAlmostEqual(weighted_out_degrees.get("A", 0.0), expected_wod_A)
        self.assertAlmostEqual(weighted_out_degrees.get("X", 0.0), expected_wod_X)
        self.assertAlmostEqual(weighted_out_degrees.get("B", 0.0), expected_wod_B)
        self.assertAlmostEqual(weighted_out_degrees.get("C", 0.0), expected_wod_C)
        self.assertAlmostEqual(weighted_out_degrees.get("D", 0.0), expected_wod_D)
        self.assertEqual(set(weighted_out_degrees.keys()), {"A", "B", "C", "X", "D"})


if __name__ == '__main__':
    unittest.main()