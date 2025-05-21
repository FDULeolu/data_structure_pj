import unittest
from src.model.product import Product

class TestProductClass(unittest.TestCase):

    def test_product_creation_valid(self):
        """测试成功创建一个有效的 Product 对象。"""
        p = Product(product_id="P001", name="Test Laptop", price=1200.50, heat=85.0)
        self.assertEqual(p.product_id, "P001")
        self.assertEqual(p.name, "Test Laptop")
        self.assertAlmostEqual(p.price, 1200.50)
        self.assertAlmostEqual(p.heat, 85.0)
        self.assertTrue(hasattr(p, '_product_id')) # 检查内部属性是否存在 (因为用了slots)
        self.assertTrue(hasattr(p, '_name'))
        self.assertTrue(hasattr(p, '_price'))
        self.assertTrue(hasattr(p, '_heat'))


    def test_product_creation_invalid_product_id(self):
        """测试创建 Product 时使用无效的 product_id。"""
        with self.assertRaisesRegex(ValueError, "product_id必须是一个非空的字符串"):
            Product(product_id="", name="Test Name", price=10.0, heat=5.0)
        with self.assertRaisesRegex(ValueError, "product_id必须是一个非空的字符串"):
            Product(product_id="   ", name="Test Name", price=10.0, heat=5.0) # 空白字符串
        with self.assertRaisesRegex(ValueError, "product_id必须是一个非空的字符串"):
            Product(product_id=None, name="Test Name", price=10.0, heat=5.0) # None

    def test_product_creation_invalid_name(self):
        """测试创建 Product 时使用无效的 name。"""
        with self.assertRaisesRegex(ValueError, "商品名称必须是一个非空的字符串"):
            Product(product_id="P001", name="", price=10.0, heat=5.0)
        with self.assertRaisesRegex(ValueError, "商品名称必须是一个非空的字符串"):
            Product(product_id="P001", name="  ", price=10.0, heat=5.0)
        # 在你的 Product __init__ 中，name 是通过 self.name = name 赋值的，会调用setter
        # 如果 __init__ 直接用 _name = name，则这里的测试方式需要调整

    def test_product_creation_invalid_price(self):
        """测试创建 Product 时使用无效的 price。"""
        with self.assertRaisesRegex(ValueError, "商品价格必须是一个正数"):
            Product(product_id="P001", name="Test Name", price=0, heat=5.0)
        with self.assertRaisesRegex(ValueError, "商品价格必须是一个正数"):
            Product(product_id="P001", name="Test Name", price=-10.0, heat=5.0)
        with self.assertRaisesRegex(ValueError, "商品价格必须是一个正数"):
            Product(product_id="P001", name="Test Name", price="invalid", heat=5.0) # 类型错误

    def test_product_creation_invalid_heat(self):
        """测试创建 Product 时使用无效的 heat。"""
        with self.assertRaisesRegex(ValueError, "商品热度必须是一个非负数字"):
            Product(product_id="P001", name="Test Name", price=10.0, heat=-5.0)
        with self.assertRaisesRegex(ValueError, "商品热度必须是一个非负数字"):
            Product(product_id="P001", name="Test Name", price=10.0, heat="invalid") # 类型错误

    def test_product_id_is_readonly(self):
        """测试 product_id 属性是否为只读。"""
        p = Product(product_id="P001", name="Test Name", price=10.0, heat=5.0)
        with self.assertRaises(AttributeError):
            p.product_id = "P002" # 尝试修改应失败，因为没有setter

    def test_name_setter_valid(self):
        """测试 name 属性的 setter 功能 (有效值)。"""
        p = Product(product_id="P001", name="Old Name", price=10.0, heat=5.0)
        p.name = "New Name"
        self.assertEqual(p.name, "New Name")
        self.assertEqual(p._name, "New Name") # 检查内部变量是否也被更新

    def test_name_setter_invalid(self):
        """测试 name 属性的 setter 功能 (无效值)。"""
        p = Product(product_id="P001", name="Valid Name", price=10.0, heat=5.0)
        with self.assertRaisesRegex(ValueError, "商品名称必须是一个非空的字符串"):
            p.name = ""
        with self.assertRaisesRegex(ValueError, "商品名称必须是一个非空的字符串"):
            p.name = "   "
        self.assertEqual(p.name, "Valid Name") # 确认无效设置后值未改变

    def test_price_setter_valid_and_invalid(self):
        """测试 price 属性的 setter 功能。"""
        p = Product(product_id="P001", name="Test Name", price=10.0, heat=5.0)
        p.price = 20.5
        self.assertAlmostEqual(p.price, 20.5)
        self.assertAlmostEqual(p._price, 20.5)

        with self.assertRaisesRegex(ValueError, "商品价格必须是一个正数"):
            p.price = 0
        with self.assertRaisesRegex(ValueError, "商品价格必须是一个正数"):
            p.price = -5
        self.assertAlmostEqual(p.price, 20.5) # 确认无效设置后值未改变

    def test_heat_setter_valid_and_invalid(self):
        """测试 heat 属性的 setter 功能。"""
        p = Product(product_id="P001", name="Test Name", price=10.0, heat=5.0)
        p.heat = 0 # 热度允许为0
        self.assertAlmostEqual(p.heat, 0.0)
        self.assertAlmostEqual(p._heat, 0.0)
        
        p.heat = 15.5
        self.assertAlmostEqual(p.heat, 15.5)

        with self.assertRaisesRegex(ValueError, "商品热度必须是一个非负数字"):
            p.heat = -10
        self.assertAlmostEqual(p.heat, 15.5) # 确认无效设置后值未改变

    def test_repr_and_str(self):
        """测试对象的字符串表示。"""
        p = Product(product_id="P001", name="Test Laptop", price=1200.99123, heat=85.505)
        expected_repr = "Product(id='P001', name='Test Laptop', price=1200.99, heat=85.50)"
        self.assertEqual(repr(p), expected_repr)
        self.assertEqual(str(p), expected_repr)

    def test_hash_and_eq(self):
            """测试基于 product_id 的哈希和相等性比较。"""
            p1a = Product(product_id="P001", name="Laptop A", price=100.0, heat=10.0)
            p1b = Product(product_id="P001", name="Laptop B", price=200.0, heat=20.0) # 相同ID，不同其他属性
            p2 = Product(product_id="P002", name="Mouse", price=20.0, heat=5.0)

            self.assertEqual(p1a, p1b) # 应该相等因为 product_id 相同
            self.assertNotEqual(p1a, p2)

            self.assertEqual(hash(p1a), hash(p1b)) # 哈希值也应相同
            self.assertNotEqual(hash(p1a), hash(p2))

            # 测试与不同类型的对象比较
            self.assertNotEqual(p1a, "P001")
            self.assertNotEqual(p1a, None)

            # 测试集合操作
            s = {p1a, p2}
            self.assertIn(p1a, s)
            self.assertIn(p1b, s) # 因为 p1a == p1b，所以 p1b 也被认为在集合中
            self.assertTrue(len(s) == 2)


if __name__ == '__main__':
    unittest.main()