import unittest

from src.data_structure.trie import ProductPrefixTrie


class TestProductPrefixTrie(unittest.TestCase):

    def setUp(self):
        self.trie = ProductPrefixTrie()

    def test_initialization(self):
        """测试Trie树初始化是否正确。"""
        self.assertIsNotNone(self.trie.root)
        self.assertFalse(self.trie.root.is_end_of_word)
        self.assertEqual(len(self.trie.root.children), 0)
        self.assertEqual(self.trie.root.product_ids, set())

    def test_insert_and_find_prefix_node_simple(self):
        """测试插入单个词和查找其前缀节点。"""
        self.trie.insert("apple", "P001")
        
        node_a = self.trie.root.children.get('a')
        self.assertIsNotNone(node_a)
        node_p1 = node_a.children.get('p')
        self.assertIsNotNone(node_p1)
        node_p2 = node_p1.children.get('p')
        self.assertIsNotNone(node_p2)
        node_l = node_p2.children.get('l')
        self.assertIsNotNone(node_l)
        node_e = node_l.children.get('e')
        self.assertIsNotNone(node_e)
        
        self.assertTrue(node_e.is_end_of_word)
        self.assertEqual(node_e.product_ids, {"P001"})
        
        # 测试 _find_prefix_node
        self.assertIs(self.trie._find_prefix_node("apple"), node_e)
        self.assertIs(self.trie._find_prefix_node("app"), node_p2)
        self.assertIsNone(self.trie._find_prefix_node("apply"))
        self.assertIsNone(self.trie._find_prefix_node("banana"))
        self.assertIs(self.trie._find_prefix_node(""), self.trie.root) # 空前缀应返回根

    def test_insert_multiple_words_shared_prefix(self):
        """测试插入多个共享前缀的词。"""
        self.trie.insert("apple", "P001")
        self.trie.insert("apply", "P002")
        self.trie.insert("ape", "P003")

        node_ap = self.trie._find_prefix_node("ap")
        self.assertIsNotNone(node_ap)
        
        node_apple_e = self.trie._find_prefix_node("apple")
        self.assertTrue(node_apple_e.is_end_of_word)
        self.assertEqual(node_apple_e.product_ids, {"P001"})

        node_apply_y = self.trie._find_prefix_node("apply")
        self.assertTrue(node_apply_y.is_end_of_word)
        self.assertEqual(node_apply_y.product_ids, {"P002"})
        
        node_ape_e = self.trie._find_prefix_node("ape")
        self.assertTrue(node_ape_e.is_end_of_word)
        self.assertEqual(node_ape_e.product_ids, {"P003"})

        # 确保 'app' 不是单词结尾，但 'apple' 的 'p' 应该是 'ape' 的 'p' 的父节点（或同一节点）
        node_app_p = self.trie._find_prefix_node("app")
        self.assertFalse(node_app_p.is_end_of_word)
        self.assertIn('l', node_app_p.children) # for apple, apply

        node_a = self.trie._find_prefix_node("a")
        self.assertIn('p', node_a.children)


    def test_insert_same_word_multiple_product_ids(self):
        """测试为同一个词插入多个product_id。"""
        self.trie.insert("apple", "P001")
        self.trie.insert("apple", "P002")
        
        node_apple = self.trie._find_prefix_node("apple")
        self.assertTrue(node_apple.is_end_of_word)
        self.assertEqual(node_apple.product_ids, {"P001", "P002"})

    def test_insert_empty_string_or_id(self):
        """测试插入空字符串名称或空product_id（应被忽略）。"""
        self.trie.insert("", "P001")
        self.assertEqual(len(self.trie.root.children), 0, "插入空名称不应创建子节点")
        
        self.trie.insert("test", "")
        node_test = self.trie._find_prefix_node("test")
        self.assertIsNone(node_test) # 不标记为节点



    def test_get_product_ids_with_prefix(self):
        """测试 get_product_ids_with_prefix 的各种情况。"""
        self.trie.insert("apple pie", "P001")
        self.trie.insert("apple", "P002")
        self.trie.insert("apple", "P007") # "apple" 关联 P002, P007
        self.trie.insert("apricot", "P003")
        self.trie.insert("banana", "P004")
        self.trie.insert("bandana", "P005")
        self.trie.insert("orange", "P006")

        self.assertEqual(self.trie.get_product_ids_with_prefix("ap"), {"P001", "P002", "P007", "P003"})
        self.assertEqual(self.trie.get_product_ids_with_prefix("apple"), {"P001", "P002", "P007"})
        self.assertEqual(self.trie.get_product_ids_with_prefix("b"), {"P004", "P005"})
        self.assertEqual(self.trie.get_product_ids_with_prefix("ban"), {"P004", "P005"})
        self.assertEqual(self.trie.get_product_ids_with_prefix("banana"), {"P004"})
        self.assertEqual(self.trie.get_product_ids_with_prefix("ora"), {"P006"})
        self.assertEqual(self.trie.get_product_ids_with_prefix("orange"), {"P006"})
        self.assertEqual(self.trie.get_product_ids_with_prefix("xyz"), set())
        self.assertEqual(self.trie.get_product_ids_with_prefix(""), 
                         {"P001", "P002", "P007", "P003", "P004", "P005", "P006"},
                         "空前缀应返回所有ID")

    # --- 测试 Delete 操作 ---
    def test_delete_non_existent_word(self):
        """测试删除一个不存在于Trie中的词。"""
        self.trie.insert("apple", "P001")
        self.assertFalse(self.trie.delete("apply", "P001"))
        self.assertFalse(self.trie.delete("apple", "P002")) # ID 不匹配

    def test_delete_product_id_from_word_with_multiple_ids(self):
        """测试从一个关联多个ID的词中删除一个ID。"""
        self.trie.insert("apple", "P001")
        self.trie.insert("apple", "P002")
        
        self.assertTrue(self.trie.delete("apple", "P001"))
        node_apple = self.trie._find_prefix_node("apple")
        self.assertTrue(node_apple.is_end_of_word) # 仍然是单词结尾
        self.assertEqual(node_apple.product_ids, {"P002"}) # 只剩下P002
        # 节点不应被清理
        self.assertIn('e', self.trie._find_prefix_node("appl").children)

    def test_delete_last_product_id_makes_not_end_of_word(self):
        """测试删除最后一个关联ID后，节点不再是单词结尾（但可能仍有子节点）。"""
        self.trie.insert("apple", "P001")
        self.trie.insert("apple pie", "P002") # "apple" 是 "apple pie" 的前缀

        self.assertTrue(self.trie.delete("apple", "P001"))
        node_apple = self.trie._find_prefix_node("apple")
        self.assertFalse(node_apple.is_end_of_word, "apple节点不应再是单词结尾")
        self.assertEqual(node_apple.product_ids, set())
        self.assertIn(' ', node_apple.children, "apple节点应仍有指向' '的子节点 (for apple pie)")


    def test_delete_word_causes_node_cleanup_simple(self):
        """测试删除单词导致简单路径上的节点被清理。"""
        self.trie.insert("apples", "P001") # a-p-p-l-e-s
        self.trie.insert("apply", "P002")  # a-p-p-l-y
        
        # 删除 "apples"
        self.assertTrue(self.trie.delete("apples", "P001"))
        
        # 's' 节点及其到 'e' 的连接应该被删除
        node_apple_e = self.trie._find_prefix_node("appl")
        self.assertIsNotNone(node_apple_e)
        self.assertFalse(node_apple_e.is_end_of_word) # apple 不是一个词
        self.assertNotIn('s', node_apple_e.children) # 不应再有 's' 的分支

        # "apply" 应该仍然存在
        self.assertIn('y', self.trie._find_prefix_node("appl").children)
        node_apply = self.trie._find_prefix_node("apply")
        self.assertTrue(node_apply.is_end_of_word)
        self.assertEqual(node_apply.product_ids, {"P002"})


    def test_delete_word_causes_partial_cleanup_shared_prefix(self):
        """测试删除单词，但共享的前缀节点由于其他单词而不被清理。"""
        self.trie.insert("team", "P001")
        self.trie.insert("tea", "P002")
        
        # 删除 "team"
        self.assertTrue(self.trie.delete("team", "P001"))
        
        node_tea = self.trie._find_prefix_node("tea")
        self.assertIsNotNone(node_tea)
        self.assertTrue(node_tea.is_end_of_word) # "tea" 仍然是一个词
        self.assertEqual(node_tea.product_ids, {"P002"})
        self.assertNotIn('m', node_tea.children) # 不应再有 'm' 的分支

        # 检查 't' 和 'e' 节点仍然存在
        self.assertIsNotNone(self.trie._find_prefix_node("t"))
        self.assertIsNotNone(self.trie._find_prefix_node("te"))


    def test_delete_all_words_empties_trie_except_root(self):
        """测试删除所有单词后，Trie树只剩根节点。"""
        self.trie.insert("a", "P1")
        self.trie.insert("b", "P2")
        
        self.assertTrue(self.trie.delete("a", "P1"))
        self.assertTrue(self.trie.delete("b", "P2"))
        
        self.assertEqual(len(self.trie.root.children), 0)
        self.assertFalse(self.trie.root.is_end_of_word)


    def test_delete_complex_scenario_with_shared_paths_and_ids(self):
        """更复杂的删除场景。"""
        self.trie.insert("cat", "C1")
        self.trie.insert("catalog", "C2")
        self.trie.insert("catch", "C3")
        self.trie.insert("bat", "B1")
        self.trie.insert("cat", "C1_dup") # "cat" 关联 C1, C1_dup

        # 1. 删除 "cat" (C1_dup) -> "cat" 节点仍然是 is_end, product_ids={"C1"}
        self.assertTrue(self.trie.delete("cat", "C1_dup"))
        node_cat = self.trie._find_prefix_node("cat")
        self.assertTrue(node_cat.is_end_of_word)
        self.assertEqual(node_cat.product_ids, {"C1"})
        self.assertIn('a', node_cat.children) # 指向 "catalog" 的 'a'
        self.assertIn('c', node_cat.children) # 指向 "catch" 的 'c'

        # 2. 删除 "catalog" (C2) -> "alog" 分支被清理，但 "cat" 节点保留 (因为它还是 "cat" 和 "catch" 的前缀)
        self.assertTrue(self.trie.delete("catalog", "C2"))
        node_cat_after_catalog_del = self.trie._find_prefix_node("cat")
        self.assertTrue(node_cat_after_catalog_del.is_end_of_word) # "cat" 仍然是词
        self.assertEqual(node_cat_after_catalog_del.product_ids, {"C1"})
        self.assertNotIn('a', node_cat_after_catalog_del.children) # "catalog" 分支被清理
        self.assertIn('c', node_cat_after_catalog_del.children)    # "catch" 分支还在

        # 3. 删除 "cat" (C1) -> "cat" 节点 is_end=False, 但因为 "catch" 仍然保留 "c"->"a"->"t" 路径
        self.assertTrue(self.trie.delete("cat", "C1"))
        node_cat_final = self.trie._find_prefix_node("cat")
        self.assertFalse(node_cat_final.is_end_of_word)
        self.assertEqual(node_cat_final.product_ids, set())
        self.assertIn('c', node_cat_final.children) # "catch" 分支还在

        # 4. 删除 "catch" (C3) -> "c"->"a"->"t"->"c"->"h" 路径被完全清理
        self.assertTrue(self.trie.delete("catch", "C3"))
        # self.assertIsNone(self.trie._find_prefix_node("c").children.get('a'), 
        #                   "节点 'ca' 应该已被清理，所以 'c' 不再有孩子 'a'")
        # 或者说，'c' 节点本身可能就被清理了，如果它不是其他词的前缀
        # 在这个例子中，"c" 只作为 "cat", "catalog", "catch" 的起始，如果它们都没了，"c" 节点也应被清理
        self.assertNotIn('c', self.trie.root.children, "'c' 分支应被完全清理")

        # "bat" 应该不受影响
        node_bat = self.trie._find_prefix_node("bat")
        self.assertTrue(node_bat.is_end_of_word)
        self.assertEqual(node_bat.product_ids, {"B1"})


if __name__ == '__main__':
    unittest.main()