import unittest
from src.data_structure.customer_graph import CustomerGraph

class TestCustomerGraph(unittest.TestCase):

    def setUp(self):
        """
        在每个测试方法运行前调用，用于设置测试环境。
        """
        self.graph = CustomerGraph()

    def test_initialization(self):
        """测试图是否被正确初始化为空"""
        self.assertEqual(len(self.graph._adj_list), 0)
        self.assertEqual(self.graph.get_all_customers(), [])

    def test_add_customer(self):
        """测试添加客户节点"""
        self.graph.add_customer("Alice")
        self.assertIn("Alice", self.graph._adj_list)
        self.assertEqual(self.graph._adj_list["Alice"], {})
        self.assertEqual(self.graph.get_all_customers(), ["Alice"])

        self.graph.add_customer("Bob")
        self.assertIn("Bob", self.graph._adj_list)
        self.assertEqual(set(self.graph.get_all_customers()), {"Alice", "Bob"})

        # 测试重复添加客户
        initial_alice_edges = self.graph._adj_list["Alice"].copy()
        self.graph.add_customer("Alice") # 不应有任何改变或错误
        self.assertEqual(len(self.graph._adj_list), 2, "重复添加客户后，客户总数不应改变")
        self.assertEqual(self.graph._adj_list["Alice"], initial_alice_edges, "重复添加客户 'Alice' 后，其出边字典应保持不变")


    def test_add_customer_invalid_type(self):
        """测试添加无效类型的客户名称 (非字符串)"""
        # 准确匹配 CustomerGraph 中定义的错误信息
        with self.assertRaisesRegex(TypeError, r"错误: 客户名称 '123' 必须是字符串，但收到了<class 'int'>"):
            self.graph.add_customer(123)
        with self.assertRaisesRegex(TypeError, r"错误: 客户名称 'None' 必须是字符串，但收到了<class 'NoneType'>"):
            self.graph.add_customer(None)
        with self.assertRaisesRegex(TypeError, r"错误: 客户名称 '\['ListCustomer'\]' 必须是字符串，但收到了<class 'list'>"):
            self.graph.add_customer(["ListCustomer"])
        self.assertEqual(len(self.graph._adj_list), 0, "添加无效类型客户后，图应仍为空")

    def test_get_all_customers(self):
        """测试获取所有客户"""
        self.assertEqual(self.graph.get_all_customers(), [])
        self.graph.add_customer("Alice")
        self.graph.add_customer("Bob")
        customers = self.graph.get_all_customers()
        self.assertEqual(set(customers), {"Alice", "Bob"})
        self.assertEqual(len(customers), 2)

    def test_add_influence_valid(self):
        """测试添加有效的影响力关系"""
        self.graph.add_influence("Alice", "Bob", 0.8)
        self.assertIn("Alice", self.graph._adj_list)
        self.assertIn("Bob", self.graph._adj_list)
        self.assertIn("Bob", self.graph._adj_list["Alice"])
        self.assertEqual(self.graph._adj_list["Alice"]["Bob"], 0.8)

        self.graph.add_influence("Alice", "Bob", 0.9) # 更新权重
        self.assertEqual(self.graph._adj_list["Alice"]["Bob"], 0.9)

        self.graph.add_influence("Alice", "Charlie", 0.0) # 权重为0是允许的
        self.assertIn("Charlie", self.graph._adj_list)
        self.assertEqual(self.graph._adj_list["Alice"]["Charlie"], 0.0)

    def test_add_influence_invalid_customer_names_type(self):
        """测试 add_influence 时客户名称类型无效 (使用组合错误消息)"""
        # from_customer 无效
        with self.assertRaisesRegex(TypeError, r"错误: 客户名称 '123' 以及 'Bob' 必须是字符串，但收到了<class 'int'>以及<class 'str'>"):
            self.graph.add_influence(123, "Bob", 0.5)
        
        # to_customer 无效
        with self.assertRaisesRegex(TypeError, r"错误: 客户名称 'Alice' 以及 '\['Charlie'\]' 必须是字符串，但收到了<class 'str'>以及<class 'list'>"):
            self.graph.add_influence("Alice", ["Charlie"], 0.5)

        # 两者都无效
        with self.assertRaisesRegex(TypeError, r"错误: 客户名称 '123' 以及 '456' 必须是字符串，但收到了<class 'int'>以及<class 'int'>"):
            self.graph.add_influence(123, 456, 0.5)
        
        self.assertEqual(len(self.graph._adj_list), 0, "发生类型错误后，不应添加任何客户或边")

    def test_add_influence_invalid_weight_type(self):
        """测试 add_influence 时权重类型无效"""
        with self.assertRaisesRegex(TypeError, r"错误: 影响力权重 'invalid_weight' 必须是数字，但收到了<class 'str'>"):
            self.graph.add_influence("Alice", "Bob", "invalid_weight")
        # 客户可能已被 add_customer 添加（因为类型检查在 add_customer 之后），但边不应添加
        # 根据 CustomerGraph 实现, 类型检查优先于 add_customer 调用
        self.assertEqual(len(self.graph._adj_list),0,"客户不应被添加如果参数类型检查失败")


    def test_add_influence_negative_weight(self):
        """测试 add_influence 时权重为负数"""
        with self.assertRaisesRegex(ValueError, r"警告: 影响力权重 '-0.5' 不允许为负数"):
            self.graph.add_influence("Alice", "Bob", -0.5)


    def test_get_direct_influencees(self):
        """测试获取直接影响的客户"""
        self.graph.add_influence("Alice", "Bob", 0.8)
        self.graph.add_influence("Alice", "Charlie", 0.6)
        self.graph.add_influence("Bob", "Charlie", 0.9)

        alice_influences = self.graph.get_direct_influencees("Alice")
        self.assertEqual(alice_influences, {"Bob": 0.8, "Charlie": 0.6})
        # 确保返回的是副本
        alice_influences["David"] = 1.0 
        self.assertEqual(self.graph.get_direct_influencees("Alice"), {"Bob": 0.8, "Charlie": 0.6})


        bob_influences = self.graph.get_direct_influencees("Bob")
        self.assertEqual(bob_influences, {"Charlie": 0.9})

        self.graph.add_customer("David") # David 没有影响任何人
        david_influences = self.graph.get_direct_influencees("David")
        self.assertEqual(david_influences, {})

        non_existent_influences = self.graph.get_direct_influencees("Zoe") # Zoe 不存在
        self.assertEqual(non_existent_influences, {})

    def test_get_direct_influencees_invalid_type(self):
        """测试 get_direct_influencees 时客户名称类型无效"""
        with self.assertRaisesRegex(TypeError, r"错误: 客户名称 '123' 必须是字符串，但收到了<class 'int'>"):
            self.graph.get_direct_influencees(123)

    def test_get_influence_weight(self):
        """测试获取特定的影响力权重"""
        self.graph.add_influence("Alice", "Bob", 0.8)
        self.graph.add_influence("Alice", "Charlie", 0.0)

        self.assertEqual(self.graph.get_influence_weight("Alice", "Bob"), 0.8)
        self.assertEqual(self.graph.get_influence_weight("Alice", "Charlie"), 0.0)
        self.assertIsNone(self.graph.get_influence_weight("Alice", "David")) # David 未被 Alice 影响
        self.assertIsNone(self.graph.get_influence_weight("Bob", "Alice"))   # Bob 未影响 Alice
        self.assertIsNone(self.graph.get_influence_weight("Zoe", "Alice"))   # Zoe 不存在
        self.assertIsNone(self.graph.get_influence_weight("Alice", "Zoe"))   # Zoe 不存在

    def test_get_influence_weight_invalid_customer_names_type(self):
        """测试 get_influence_weight 时客户名称类型无效 (组合错误消息)"""
        with self.assertRaisesRegex(TypeError, r"错误: 客户名称 '123' 以及 'Bob' 必须是字符串，但收到了<class 'int'>以及<class 'str'>"):
            self.graph.get_influence_weight(123, "Bob")
        with self.assertRaisesRegex(TypeError, r"错误: 客户名称 'Alice' 以及 '\['Eve'\]' 必须是字符串，但收到了<class 'str'>以及<class 'list'>"):
            self.graph.get_influence_weight("Alice", ["Eve"])


if __name__ == '__main__':
    unittest.main()