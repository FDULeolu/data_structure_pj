import unittest
from src.data_structure.customer_graph import CustomerGraph
from src.module.customer_network_analysis import (
    calculate_weighted_out_degree_centrality,
    calculate_weighted_in_degree_centrality
)

class TestCustomerGraphAnalysis(unittest.TestCase):

    def setUp(self):
        """
        在每个测试方法运行前调用，用于设置测试环境。
        """
        self.graph = CustomerGraph()

    def test_calculate_weighted_out_degree_centrality_empty_graph(self):
        """测试空图的加权出度中心性"""
        expected_centrality = {}
        self.assertEqual(calculate_weighted_out_degree_centrality(self.graph), expected_centrality)

    def test_calculate_weighted_in_degree_centrality_empty_graph(self):
        """测试空图的加权入度中心性"""
        expected_centrality = {}
        self.assertEqual(calculate_weighted_in_degree_centrality(self.graph), expected_centrality)

    def test_calculate_weighted_out_degree_centrality_simple_graph(self):
        """测试简单图的加权出度中心性"""
        self.graph.add_influence("A", "B", 0.5)
        self.graph.add_influence("A", "C", 1)
        self.graph.add_influence("B", "C", 0.8)
        self.graph.add_customer("D") # 孤立节点

        expected_centrality = {
            "A": 0.5 + 1,
            "B": 0.8,
            "C": 0.0,
            "D": 0.0
        }
        # 使用 assertAlmostEqual 比较浮点数，或者确保精度一致
        result = calculate_weighted_out_degree_centrality(self.graph)
        for node, score in expected_centrality.items():
            self.assertAlmostEqual(result.get(node, 0.0), score, places=7)
        self.assertEqual(set(result.keys()), set(expected_centrality.keys()))


    def test_calculate_weighted_in_degree_centrality_simple_graph(self):
        """测试简单图的加权入度中心性"""
        self.graph.add_influence("A", "B", 0.5)
        self.graph.add_influence("A", "C", 1.0)
        self.graph.add_influence("B", "C", 0.8)
        self.graph.add_customer("D") # 孤立节点

        expected_centrality = {
            "A": 0.0,
            "B": 0.5,
            "C": 1.0 + 0.8, # 2.3
            "D": 0.0
        }
        result = calculate_weighted_in_degree_centrality(self.graph)
        for node, score in expected_centrality.items():
            self.assertAlmostEqual(result.get(node, 0.0), score, places=7)
        self.assertEqual(set(result.keys()), set(expected_centrality.keys()))

    def test_centrality_with_zero_weight_edges(self):
        """测试包含零权重边的图的中心性"""
        self.graph.add_influence("A", "B", 0.0)
        self.graph.add_influence("A", "C", 1.0)
        self.graph.add_influence("C", "A", 0.5)

        # 加权出度
        expected_out_centrality = {
            "A": 0.0 + 1.0, # 1.0
            "B": 0.0,
            "C": 0.5
        }
        result_out = calculate_weighted_out_degree_centrality(self.graph)
        for node, score in expected_out_centrality.items():
            self.assertAlmostEqual(result_out.get(node, 0.0), score, places=7)
        self.assertEqual(set(result_out.keys()), set(expected_out_centrality.keys()))

        # 加权入度
        expected_in_centrality = {
            "A": 0.5,
            "B": 0.0,
            "C": 1.0
        }
        result_in = calculate_weighted_in_degree_centrality(self.graph)
        for node, score in expected_in_centrality.items():
            self.assertAlmostEqual(result_in.get(node, 0.0), score, places=7)
        self.assertEqual(set(result_in.keys()), set(expected_in_centrality.keys()))


    def test_calculate_weighted_out_degree_centrality_graph_with_no_edges(self):
        """测试只有节点没有边的图的加权出度中心性"""
        self.graph.add_customer("A")
        self.graph.add_customer("B")
        expected_centrality = {"A": 0.0, "B": 0.0}
        self.assertEqual(calculate_weighted_out_degree_centrality(self.graph), expected_centrality)

    def test_calculate_weighted_in_degree_centrality_graph_with_no_edges(self):
        """测试只有节点没有边的图的加权入度中心性"""
        self.graph.add_customer("A")
        self.graph.add_customer("B")
        expected_centrality = {"A": 0.0, "B": 0.0}
        self.assertEqual(calculate_weighted_in_degree_centrality(self.graph), expected_centrality)

    def test_out_degree_centrality_type_error(self):
        """测试加权出度中心性函数对无效输入的类型错误"""
        with self.assertRaisesRegex(TypeError, "输入必须是一个 CustomerGraph 对象"):
            calculate_weighted_out_degree_centrality("not_a_graph_object")
        with self.assertRaisesRegex(TypeError, "输入必须是一个 CustomerGraph 对象"):
            calculate_weighted_out_degree_centrality([1, 2, 3])

    def test_in_degree_centrality_type_error(self):
        """测试加权入度中心性函数对无效输入的类型错误"""
        with self.assertRaisesRegex(TypeError, "输入必须是一个 CustomerGraph 对象"):
            calculate_weighted_in_degree_centrality(None)
        with self.assertRaisesRegex(TypeError, "输入必须是一个 CustomerGraph 对象"):
            calculate_weighted_in_degree_centrality({"key": "value"})
            
    def test_centrality_complex_graph(self):
        """测试一个更复杂的图的中心性计算"""
        self.graph.add_influence("Alice", "Bob", 0.8)
        self.graph.add_influence("Alice", "Charlie", 0.6)
        self.graph.add_influence("Bob", "Charlie", 0.9)
        self.graph.add_influence("Bob", "David", 0.7)
        self.graph.add_influence("Charlie", "David", 0.5)
        self.graph.add_influence("Eve", "Alice", 0.4)
        self.graph.add_customer("Frank")

        # 加权出度
        expected_out = {
            "Alice": 0.8 + 0.6,   # 1.4
            "Bob": 0.9 + 0.7,     # 1.6
            "Charlie": 0.5,
            "David": 0.0,
            "Eve": 0.4,
            "Frank": 0.0
        }
        result_out = calculate_weighted_out_degree_centrality(self.graph)
        for node, score in expected_out.items():
            self.assertAlmostEqual(result_out.get(node, 0.0), score, places=7, msg=f"Out-degree for {node}")
        self.assertEqual(set(result_out.keys()), set(expected_out.keys()))

        # 加权入度
        expected_in = {
            "Alice": 0.4,
            "Bob": 0.8,
            "Charlie": 0.6 + 0.9, # 1.5
            "David": 0.7 + 0.5,   # 1.2
            "Eve": 0.0,
            "Frank": 0.0
        }
        result_in = calculate_weighted_in_degree_centrality(self.graph)
        for node, score in expected_in.items():
            self.assertAlmostEqual(result_in.get(node, 0.0), score, places=7, msg=f"In-degree for {node}")
        self.assertEqual(set(result_in.keys()), set(expected_in.keys()))

if __name__ == '__main__':
    unittest.main()