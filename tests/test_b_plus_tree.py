import unittest

from src.data_structure.b_plus_tree import *
from src.module.commodity_retrieval import *

# --- 测试 BPlusTreeProducts ---
class TestBPlusTreeProducts(unittest.TestCase):
    def setUp(self):
        # 创建一些不同阶的树进行测试
        self.tree_order3 = BPlusTreeProducts(order=3)
        self.tree_order4 = BPlusTreeProducts(order=4)
        self.tree_order2 = BPlusTreeProducts(order=2) # 最小阶

        # 模拟一些商品ID
        self.p1 = Product("prod1", price=10.0)
        self.p2 = Product("prod2", price=20.0)
        self.p3 = Product("prod3", price=10.0) # 相同价格
        self.p4 = Product("prod4", price=30.0)
        self.p5 = Product("prod5", price=5.0)
        self.p6 = Product("prod6", price=15.0)
        self.p7 = Product("prod7", price=25.0)
        self.p8 = Product("prod8", price=20.0) # 相同价格

    def _insert_products(self, tree, products_with_prices):
        for price, product_id_obj in products_with_prices:
            tree.insert(price, product_id_obj) # BPlusTreeProducts 插入的是 (price, product_id_object)

    def test_01_initialization(self):
        self.assertIsNotNone(self.tree_order3.root)
        self.assertTrue(self.tree_order3.root.is_leaf)
        self.assertEqual(self.tree_order3.order, 3)
        with self.assertRaises(ValueError):
            BPlusTreeProducts(order=1)
        with self.assertRaises(ValueError):
            BPlusTreeNode(order=1)

    def test_02_simple_insert_and_search_exact(self):
        tree = self.tree_order3
        tree.insert(10.0, self.p1)
        tree.insert(20.0, self.p2)

        self.assertEqual(len(tree.search_exact(10.0)), 1)
        self.assertIn(self.p1, tree.search_exact(10.0))
        self.assertEqual(len(tree.search_exact(20.0)), 1)
        self.assertIn(self.p2, tree.search_exact(20.0))
        self.assertEqual(len(tree.search_exact(15.0)), 0) # 不存在的价格

    def test_03_insert_duplicate_prices(self):
        tree = self.tree_order3
        tree.insert(10.0, self.p1.product_id)
        tree.insert(10.0, self.p3.product_id) # 相同价格，不同ID

        results = tree.search_exact(10.0)
        self.assertEqual(len(results), 2)
        self.assertIn(self.p1.product_id, results)
        self.assertIn(self.p3.product_id, results)

    def test_04_search_exact_with_product_id(self):
        tree = self.tree_order3
        tree.insert(10.0, self.p1.product_id)
        tree.insert(10.0, self.p3.product_id)
        tree.insert(20.0, self.p2.product_id)

        self.assertEqual(tree.search_exact(10.0, self.p1.product_id), [self.p1.product_id])
        self.assertEqual(tree.search_exact(10.0, self.p3.product_id), [self.p3.product_id])
        self.assertEqual(len(tree.search_exact(10.0, "nonexistent_id")), 0)
        self.assertEqual(tree.search_exact(20.0, self.p2.product_id), [self.p2.product_id])
        self.assertEqual(len(tree.search_exact(15.0, self.p1.product_id)), 0)


    def test_05_leaf_split(self):
        tree = BPlusTreeProducts(order=2) # 叶节点最多2个key
        # 插入会导致分裂的序列
        # tree._print_tree_structure(tree.root, 3)
        tree.insert(10.0, self.p1)
        # tree._print_tree_structure(tree.root, 3)
        tree.insert(20.0, self.p2)
        # tree._print_tree_structure(tree.root, 3)
        self.assertEqual(len(tree.root.keys), 2) # 10, 20
        tree.insert(5.0, self.p5) # 插入5.0，导致分裂 (5), (10,20) -> 根[10], 叶[5],[10,20]
        # tree._print_tree_structure(tree.root, 3)

        self.assertFalse(tree.root.is_leaf)
        self.assertEqual(len(tree.root.keys), 1)
        self.assertEqual(tree.root.keys[0], 20.0) # 上推的键
        self.assertEqual(len(tree.root.children), 2)

        left_leaf = tree.root.children[0]
        right_leaf = tree.root.children[1]

        self.assertTrue(left_leaf.is_leaf)
        self.assertEqual(left_leaf.keys, [5.0, 10.0])
        self.assertEqual(left_leaf.values[0], [self.p5])

        self.assertTrue(right_leaf.is_leaf)
        self.assertEqual(right_leaf.keys, [20.0]) #分裂逻辑可能导致分裂点不同，这里基于实现
        # 或者 [10.0], [20.0] 如果分裂点是第一个
        # 检查实现：_split_leaf 中 mid_point_index = math.ceil(len(leaf_to_split.keys) / 2)
        # 对于 [5,10,20] order=2 (max keys=2), 插入20后keys=[5,10,20] (len=3). mid=ceil(3/2)=2
        # new_leaf.keys = keys[2:] = [20]
        # leaf_to_split.keys = keys[:2] = [5,10]
        # key_to_push_up = new_leaf.keys[0] = 20
        # 实际插入顺序是 10, 20, 然后 5.
        # 1. 10 -> root=[10]
        # 2. 20 -> root=[10,20]
        # 3. 5 -> keys=[5,10,20], overflow. mid=ceil(3/2)=2. new_leaf.keys=[20], old_leaf.keys=[5,10]. push_up=20
        #    root=[20], children: leaf1([5,10]), leaf2([20])
        # self.assertEqual(right_leaf.keys, [10.0, 20.0]) # 之前的理解分裂有点问题，重新分析
        # 插入10: leaf_node.keys = [10], leaf_node.values = [[p1]]
        # 插入20: leaf_node.keys = [10, 20], leaf_node.values = [[p1], [p2]] (order 2, max 2 keys, not overflow)
        # 插入5: leaf_node.keys = [5, 10, 20], leaf_node.values = [[p5], [p1], [p2]] (overflow!)
        # mid_point = ceil(3/2) = 2. new_leaf gets keys[2:] ([20]), values[2:] ([[p2]])
        # old_leaf gets keys[:2] ([5,10]), values[:2] ([[p5],[p1]])
        # key_to_push_up = new_leaf.keys[0] = 20
        # new_root.keys = [20], children = [old_leaf, new_leaf]
        self.assertEqual(left_leaf.keys, [5.0, 10.0])
        self.assertIn(self.p5, left_leaf.values[0])
        self.assertIn(self.p1, left_leaf.values[1])
        self.assertEqual(right_leaf.keys, [20.0])
        self.assertIn(self.p2, right_leaf.values[0])
        self.assertEqual(tree.root.keys[0], 20.0) # 分裂后上推的键

        # 验证叶节点链表
        self.assertEqual(left_leaf.next_leaf, right_leaf)
        self.assertEqual(right_leaf.prev_leaf, left_leaf)
        self.assertIsNone(left_leaf.prev_leaf)
        self.assertIsNone(right_leaf.next_leaf)

    def test_06_internal_node_split(self):
        tree = BPlusTreeProducts(order=2) # 内部节点最多2个key，3个孩子
        # 插入序列触发内部节点分裂
        # 1. 10, 20 -> root(leaf)=[10,20]
        # 2. 5 (leaf split) -> root(internal)=[20], children: L([5,10]), R([20])
        tree.insert(10.0, self.p1) # [[p1]]
        tree.insert(20.0, self.p2) # [[p1],[p2]]
        tree.insert(5.0, self.p5)  # [[p5],[p1]], [[p2]] ->推20
        # 当前: root=[20], child1(leaf)=[5,10], child2(leaf)=[20]

        # 3. 30 -> child2=[20,30]
        tree.insert(30.0, self.p4) # [[p5],[p1]], [[p2],[p4]]
        # 当前: root=[20], child1(leaf)=[5,10], child2(leaf)=[20,30]

        # 4. 25 (leaf split, child2 splits) -> [20,30] + [25] -> [20,25,30]
        #    mid=ceil(3/2)=2. new_leaf_val=[30], old_leaf_val=[20,25]. push_up=30
        #    child2 becomes [20,25], new_child_for_root is [30]
        #    parent (root) was [20]. Insert key 30.
        #    _insert_into_parent(child2, 30, new_child_for_root)
        #    root.keys becomes [20, 30] (插入30)
        #    root.children becomes [child1, child2, new_child_for_root]
        #    No internal split yet, root.keys=[20,30], children=[L(5,10),L(20,25),L(30)]
        tree.insert(25.0, self.p7) # [[p5],[p1]], [[p2],[p7]], [[p4]] -> 推30
        self.assertEqual(tree.root.keys, [20.0, 30.0])
        self.assertEqual(len(tree.root.children), 3)

        # 5. 15 (leaf split, child1 splits) -> [5,10] + [15] -> [5,10,15]
        #    mid=ceil(3/2)=2. new_leaf_val=[15], old_leaf_val=[5,10]. push_up=15
        #    child1 becomes [5,10], new_child_for_root is [15]
        #    parent (root) was [20,30]. Insert key 15.
        #    _insert_into_parent(child1, 15, new_child_for_root)
        #    root.keys becomes [15, 20, 30] (插入15) - overflow for order=2 (max 2 keys)
        #    Internal split: keys=[15,20,30]. mid_key_index = 2//2 = 1. key_to_push_up = keys[1] = 20
        #    new_internal_node.keys = keys[2:] = [30]
        #    new_internal_node.children = root.children[2:] (original children for 20 and 30)
        #    node_to_split (old root).keys = keys[:1] = [15]
        #    node_to_split.children = root.children[:2] (original children for <15 and between 15,20)
        #    New root will be [20]
        tree.insert(15.0, self.p6)
        self.assertFalse(tree.root.is_leaf)
        self.assertEqual(len(tree.root.keys), 1) # Internal split, e.g. 20 pushed up
        self.assertEqual(tree.root.keys[0], 20.0) # 推20
        self.assertEqual(len(tree.root.children), 2) # Two internal nodes as children

        # Verify structure (this depends heavily on the split logic)
        # Root: [20]
        #   L-Internal: [15] children: L(5,10), L(15)
        #   R-Internal: [30] children: L(20,25), L(30)
        left_internal = tree.root.children[0]
        right_internal = tree.root.children[1]
        self.assertFalse(left_internal.is_leaf)
        self.assertEqual(left_internal.keys, [15.0])
        self.assertEqual(len(left_internal.children), 2)
        self.assertTrue(all(c.is_leaf for c in left_internal.children))
        # check values for 5,10,15
        self.assertEqual(left_internal.children[0].keys, [5.0, 10.0])
        self.assertEqual(left_internal.children[1].keys, [15.0])


        self.assertFalse(right_internal.is_leaf)
        self.assertEqual(right_internal.keys, [30.0])
        self.assertEqual(len(right_internal.children), 2)
        self.assertTrue(all(c.is_leaf for c in right_internal.children))
        self.assertEqual(right_internal.children[0].keys, [20.0, 25.0]) # or [25.0] if p7 causes split, depends on p2/p7 values
        self.assertEqual(right_internal.children[1].keys, [30.0])

        # Search for all items
        self.assertIn(self.p1, tree.search_exact(10.0))
        self.assertIn(self.p2, tree.search_exact(20.0))
        self.assertIn(self.p4, tree.search_exact(30.0))
        self.assertIn(self.p5, tree.search_exact(5.0))
        self.assertIn(self.p6, tree.search_exact(15.0))
        self.assertIn(self.p7, tree.search_exact(25.0))


    def test_07_search_range(self):
        tree = self.tree_order3
        items = [
            (10.0, self.p1), (20.0, self.p2), (10.0, self.p3),
            (30.0, self.p4), (5.0, self.p5), (15.0, self.p6),
            (25.0, self.p7), (20.0, self.p8)
        ]
        self._insert_products(tree, items)

        # Range [10, 20]
        results = tree.search_range(10.0, 20.0)
        self.assertEqual(len(results), 5) # p1,p3 (10), p6 (15), p2,p8 (20)
        expected_ids_in_range = {self.p1, self.p3, self.p6, self.p2, self.p8}
        self.assertTrue(all(item in expected_ids_in_range for item in results))

        # Range [0, 5]
        results = tree.search_range(0.0, 5.0)
        self.assertEqual(len(results), 1)
        self.assertIn(self.p5, results)

        # Range [28, 100]
        results = tree.search_range(28.0, 100.0)
        self.assertEqual(len(results), 1)
        self.assertIn(self.p4, results) # p4 is 30.0

        # Empty range
        self.assertEqual(len(tree.search_range(100.0, 200.0)), 0)
        self.assertEqual(len(tree.search_range(12.0, 14.0)), 0)

        # Min_price > max_price
        self.assertEqual(len(tree.search_range(20.0, 10.0)), 0)

        # Single point range
        results = tree.search_range(10.0, 10.0)
        self.assertEqual(len(results), 2)
        self.assertIn(self.p1, results)
        self.assertIn(self.p3, results)

        # Full range
        all_products = [p_obj for _, p_obj in items]
        results = tree.search_range(0.0, 100.0)
        self.assertEqual(len(results), len(all_products))
        self.assertTrue(all(item in results for item in all_products))

    def test_08_delete_simple_leaf_no_underflow(self):
        tree = self.tree_order3 # order=3, min_keys = ceil(3/2) = 2
        tree.insert(10.0, self.p1.product_id)
        tree.insert(20.0, self.p2.product_id)
        tree.insert(30.0, self.p4.product_id) # root=[10,20,30]

        self.assertTrue(tree.delete(20.0, self.p2.product_id))
        self.assertEqual(len(tree.search_exact(20.0)), 0)
        self.assertEqual(tree.root.keys, [10.0, 30.0]) # Keys are now [10,30]
        self.assertEqual(len(tree.root.values[0]), 1) # p1
        self.assertEqual(len(tree.root.values[1]), 1) # p4

        # Delete non-existent
        self.assertFalse(tree.delete(15.0, "any_id"))
        self.assertFalse(tree.delete(10.0, "non_existent_id_for_10"))

    def test_09_delete_from_multiple_items_at_same_key(self):
        tree = self.tree_order3
        tree.insert(10.0, self.p1.product_id)
        tree.insert(10.0, self.p3.product_id)
        tree.insert(20.0, self.p2.product_id)

        self.assertTrue(tree.delete(10.0, self.p1.product_id))
        results_10 = tree.search_exact(10.0)
        self.assertEqual(len(results_10), 1)
        self.assertIn(self.p3.product_id, results_10)
        self.assertEqual(tree.root.keys, [10.0, 20.0]) # Key 10.0 still exists

        self.assertTrue(tree.delete(10.0, self.p3.product_id)) # Delete last item for key 10.0
        self.assertEqual(len(tree.search_exact(10.0)), 0)
        self.assertEqual(tree.root.keys, [20.0]) # Key 10.0 is removed

    def test_10_delete_causing_leaf_underflow_borrow_from_right_sibling(self):
        tree = BPlusTreeProducts(order=2) # min_keys = ceil(2/2) = 1
        # Setup: root=[20], L(leaf)=[10], R(leaf)=[20,30] (after inserting 10,20,30 with order=2)
        # 10 -> [10]
        # 20 -> [10,20]
        # 30 -> [10,20,30] -> split. mid=ceil(3/2)=2. new_leaf=[30], old_leaf=[10,20], push_up=30
        # root=[30], L=[10,20], R=[30]
        tree.insert(10.0, self.p1.product_id)
        tree.insert(20.0, self.p2.product_id)
        tree.insert(30.0, self.p4.product_id) # Root: [30], Children: Leaf1([10,20]), Leaf2([30])

        # Delete 10.0 (from p1). Leaf1 becomes [20], still fine (1 key >= min_keys 1)
        self.assertTrue(tree.delete(10.0, self.p1.product_id))
        # Leaf1 is now [[p2] at key 20]. Parent key [30] is still valid for separation.
        # Leaf1.keys=[20], Leaf2.keys=[30]
        # Root.keys=[30]
        self.assertEqual(tree.root.children[0].keys, [20.0])
        self.assertEqual(tree.root.children[1].keys, [30.0])
        self.assertEqual(tree.root.keys, [30.0])


        # Now, delete 20.0 (from p2) in Leaf1. Leaf1 becomes empty -> underflow.
        # Leaf1 needs to borrow. Right sibling Leaf2([30]) has 1 key, can lend if min_keys allows.
        # Here, min_keys=1. If a node has > min_keys it can lend. Leaf2 has 1 key == min_keys, CANNOT lend.
        # So, it should merge.
        # _handle_leaf_node_underflow -> try borrow right (fails) -> try borrow left (no left) -> merge right
        # Merging L1 (empty) with L2([30])
        # L1 gets L2's keys/values. L1.keys=[30]
        # Parent (root [30]) loses key at index 0 (the key 30) and child at index 1 (L2)
        # Root.keys=[], Root.children=[L1] -> Root underflow
        # _handle_internal_node_underflow for root: if not keys and len children == 1, new root is child[0]
        # So, L1 ([30]) becomes the new root.
        self.assertTrue(tree.delete(20.0, self.p2.product_id))
        self.assertTrue(tree.root.is_leaf)
        self.assertEqual(tree.root.keys, [30.0])
        self.assertIn(self.p4.product_id, tree.root.values[0])

    def test_11_delete_causing_leaf_underflow_borrow_from_left_sibling(self):
        tree = BPlusTreeProducts(order=2) # min_keys = 1
        # Setup: root=[20], L(leaf)=[10,20], R(leaf)=[30] (after inserting 10,20,30 with order=2, then 5)
        # 10,20,30 -> root=[30], L=[10,20], R=[30]
        # Now insert 5: L=[5,10,20] -> split. mid=2. new_L_child=[20], old_L_child=[5,10], push_up=20
        # Root was [30]. insert 20 -> root.keys=[20,30]
        # Root children: L_L([5,10]), L_R([20]), R_orig([30])
        tree.insert(10.0, self.p1.product_id)
        tree.insert(20.0, self.p2.product_id)
        tree.insert(30.0, self.p4.product_id)
        tree.insert(5.0, self.p5.product_id)
        # Structure: root=[20,30]
        # Children: L1([5,10]), L2([20]), L3([30])

        # Delete 30 (p4) from L3. L3 becomes empty -> underflow.
        # L3 needs to borrow/merge. Left sibling is L2([20]). L2 has 1 key (== min_keys), cannot lend.
        # So L3 merges with L2. L2 takes L3's (empty) stuff.
        # Parent (root) loses key at index 1 (which is 30) and child at index 2 (L3).
        # Root.keys becomes [20]. Root.children becomes [L1, L2]. No root underflow.
        self.assertTrue(tree.delete(30.0, self.p4.product_id))
        self.assertEqual(tree.root.keys, [20.0])
        self.assertEqual(len(tree.root.children), 2)
        self.assertEqual(tree.root.children[0].keys, [5.0, 10.0]) # L1
        self.assertEqual(tree.root.children[1].keys, [20.0])    # L2 (merged with L3's nothingness)
        # Check leaf links
        self.assertEqual(tree.root.children[0].next_leaf, tree.root.children[1])
        self.assertEqual(tree.root.children[1].prev_leaf, tree.root.children[0])

    def test_12_delete_causing_leaf_merge_and_internal_underflow_borrow(self):
        tree = BPlusTreeProducts(order=2) # min_keys_leaf=1, 
        items_to_insert = [
            (10.0, Product("p10")), (20.0, Product("p20")), (30.0, Product("p30")),
            (40.0, Product("p40")), (5.0, Product("p05")), (60.0, Product("p60"))
        ]
        for price, prod_obj in items_to_insert:
            tree.insert(price, prod_obj.product_id)


        # tree._print_tree_structure(tree.root, 4)
        self.assertTrue(tree.delete(60.0, "p60"))

        root_node = tree.root
        self.assertFalse(root_node.is_leaf)
        self.assertEqual(root_node.keys, [30.0])
        self.assertEqual(len(root_node.children), 2)

        l_internal = root_node.children[0]
        r_internal = root_node.children[1]

        self.assertFalse(l_internal.is_leaf)
        self.assertEqual(l_internal.keys, [20.0])
        self.assertEqual(len(l_internal.children), 2)

        self.assertFalse(r_internal.is_leaf)
        self.assertEqual(r_internal.keys, [40.0])
        self.assertEqual(len(r_internal.children), 2)

        # 获取叶子节点
        leaf_A = l_internal.children[0] # Keys: [5.0, 10.0]
        leaf_B = l_internal.children[1] # Keys: [20.0]
        leaf_C = r_internal.children[0] # Keys: [30.0]
        leaf_D = r_internal.children[1] # Keys: [40.0]

        self.assertTrue(leaf_A.is_leaf)
        self.assertEqual(leaf_A.keys, [5.0, 10.0])
        # ... 其他叶子节点的键和 is_leaf 检查 ...

        # 检查叶节点链表指针
        self.assertEqual(leaf_A.next_leaf, leaf_B)
        self.assertEqual(leaf_B.prev_leaf, leaf_A)

        self.assertEqual(leaf_B.next_leaf, leaf_C)
        self.assertEqual(leaf_C.prev_leaf, leaf_B)

        self.assertEqual(leaf_C.next_leaf, leaf_D)
        self.assertEqual(leaf_D.prev_leaf, leaf_C)

        self.assertIsNone(leaf_A.prev_leaf)
        self.assertIsNone(leaf_D.next_leaf)


    def test_13_delete_all_elements_empty_tree(self):
        tree = self.tree_order3
        tree.insert(10.0, self.p1.product_id)
        tree.insert(20.0, self.p2.product_id)

        self.assertTrue(tree.delete(10.0, self.p1.product_id))
        self.assertTrue(tree.delete(20.0, self.p2.product_id))

        self.assertTrue(tree.root.is_leaf)
        self.assertEqual(len(tree.root.keys), 0)
        self.assertEqual(len(tree.root.values), 0)
        self.assertEqual(len(tree.search_range(0, 100)), 0)

        # Try deleting from empty tree
        self.assertFalse(tree.delete(10.0, self.p1.product_id))

    def test_14_delete_root_becomes_leaf_after_merge(self):
        tree = BPlusTreeProducts(order=2) # min_keys=1
        # 10, 20, 30 -> Root(30), L1(10,20), L2(30)
        tree.insert(10.0, self.p1.product_id)
        tree.insert(20.0, self.p2.product_id)
        tree.insert(30.0, self.p4.product_id)

        # Delete 10 (p1). L1 becomes (20). Root(30), L1(20), L2(30). Still valid.
        tree.delete(10.0, self.p1.product_id)
        self.assertEqual(tree.root.keys, [30.0])
        self.assertEqual(tree.root.children[0].keys, [20.0])
        self.assertEqual(tree.root.children[1].keys, [30.0])


        # Delete 20 (p2). L1 becomes empty, underflow. Merges with L2(30).
        # L1 gets [30] (p4). Parent Root(30) loses key 30 and child L2.
        # Root.keys=[], Root.children=[L1]. Root underflow.
        # New root is L1. Tree becomes a single leaf node.
        tree.delete(20.0, self.p2.product_id)
        self.assertTrue(tree.root.is_leaf)
        self.assertEqual(tree.root.keys, [30.0])
        self.assertIn(self.p4.product_id, tree.root.values[0])
        self.assertIsNone(tree.root.parent)

    def test_15_large_number_of_insertions_and_deletions_order3(self):
        tree = BPlusTreeProducts(order=3)
        products = []
        num_items = 100
        for i in range(num_items):
            p_id = f"prod_lg_{i}"
            price = float(i * 10.0 + (i % 7) + 1) # Some variation
            product = Product(p_id, price=price)
            products.append(product)
            tree.insert(price, product.product_id)

        # Verify all inserted
        for prod in products:
            self.assertIn(prod.product_id, tree.search_exact(prod.price, prod.product_id))

        # Delete half of them
        for i in range(0, num_items, 2):
            prod_to_delete = products[i]
            self.assertTrue(tree.delete(prod_to_delete.price, prod_to_delete.product_id), f"Failed to delete {prod_to_delete}")

        # Verify deleted items are gone and others remain
        for i in range(num_items):
            prod = products[i]
            if i % 2 == 0: # Deleted
                self.assertEqual(len(tree.search_exact(prod.price, prod.product_id)), 0, f"{prod} should be deleted")
            else: # Kept
                self.assertIn(prod.product_id, tree.search_exact(prod.price, prod.product_id), f"{prod} should exist")

        # Delete the rest
        for i in range(1, num_items, 2):
            prod_to_delete = products[i]
            self.assertTrue(tree.delete(prod_to_delete.price, prod_to_delete.product_id),  f"Failed to delete remaining {prod_to_delete}")

        self.assertTrue(tree.root.is_leaf)
        self.assertEqual(len(tree.root.keys), 0)

    def test_16_find_leaf_node_logic(self):
        tree = self.tree_order3
        tree.insert(10.0, self.p1)
        tree.insert(20.0, self.p2)
        tree.insert(5.0, self.p5) # order 3, root=[5,10,20] is leaf

        leaf = tree._find_leaf_node(10.0)
        self.assertIn(10.0, leaf.keys)
        leaf = tree._find_leaf_node(7.0) # Should go to the leaf where 7 would be inserted
        self.assertEqual(leaf, tree.root) # Still root as it's a leaf containing 5,10,20

        # After split
        tree.insert(30.0, self.p4) # Keys: 5,10,20,30 -> overflow. mid=ceil(4/2)=2. (keys[0],keys[1]) | (keys[2],keys[3])
                                 # Old=[5,10], New=[20,30], push_up=20. Root(I)=[20], L(L)=[5,10], R(L)=[20,30]
        self.assertFalse(tree.root.is_leaf)
        leaf_for_7 = tree._find_leaf_node(7.0)
        self.assertEqual(leaf_for_7.keys, [5.0, 10.0])

        leaf_for_15 = tree._find_leaf_node(15.0) # Should go to L(L)
        self.assertEqual(leaf_for_15.keys, [5.0, 10.0]) # bisect_right for 15 in [20] gives index 0.
                                                      # So _find_leaf_node(15) returns the left child [5,10]

        leaf_for_25 = tree._find_leaf_node(25.0)
        self.assertEqual(leaf_for_25.keys, [20.0, 30.0])

        leaf_for_35 = tree._find_leaf_node(35.0)
        self.assertEqual(leaf_for_35.keys, [20.0, 30.0])


# --- 测试 BPlusTreeID ---
class TestBPlusTreeID(unittest.TestCase):
    def setUp(self):
        self.tree_order3 = BPlusTreeID(order=3)
        self.tree_order2 = BPlusTreeID(order=2)

        self.prod_obj1 = Product("prod_apple_123", price=1.0)
        self.prod_obj2 = Product("prod_banana_456", price=0.5)
        self.prod_obj3 = Product("prod_cherry_789", price=2.0)
        self.prod_obj4 = Product("prod_apricot_000", price=1.5) # To test string ordering
        self.prod_obj5 = Product("prod_blueberry_111", price=2.5)


    def test_01_initialization(self):
        self.assertIsNotNone(self.tree_order3.root)
        self.assertTrue(self.tree_order3.root.is_leaf)
        self.assertEqual(self.tree_order3.order, 3)
        with self.assertRaises(ValueError):
            BPlusTreeID(order=0)

    def test_02_insert_and_search(self):
        tree = self.tree_order3
        tree.insert(self.prod_obj1)
        tree.insert(self.prod_obj2)

        self.assertEqual(tree.search(self.prod_obj1.product_id), self.prod_obj1)
        self.assertEqual(tree.search(self.prod_obj2.product_id), self.prod_obj2)
        self.assertIsNone(tree.search("non_existent_id"))

        # Insert with non-Product type
        with self.assertRaises(TypeError):
            tree.insert("not_a_product_object")


    def test_03_leaf_split(self):
        tree = self.tree_order2 # Max 2 keys per leaf
        # tree._print_tree_structure(tree.root, 4)
        tree.insert(self.prod_obj1, test=True) # id: prod_apple_123
        # tree._print_tree_structure(tree.root, 4)
        tree.insert(self.prod_obj2, test=True) # id: prod_banana_456
        # Leaf: ["prod_apple_123", "prod_banana_456"]
        # tree._print_tree_structure(tree.root, 4)

        tree.insert(self.prod_obj4, test=True) # id: prod_apricot_000 (comes before apple)
        # tree._print_tree_structure(tree.root, 4)
        # Keys before split in leaf: ["prod_apricot_000", "prod_apple_123", "prod_banana_456"] - overflow
        # mid = ceil(3/2) = 2.
        # new_leaf_keys = keys[2:] = ["prod_banana_456"]
        # old_leaf_keys = keys[:2] = ["prod_apricot_000", "prod_apple_123"]
        # key_to_push_up = new_leaf_keys[0] = "prod_banana_456"

        self.assertFalse(tree.root.is_leaf)
        self.assertEqual(tree.root.keys, ["prod_banana_456"])
        left_leaf = tree.root.children[0]
        right_leaf = tree.root.children[1]

        self.assertEqual(left_leaf.keys, ["prod_apple_123", "prod_apricot_000"])
        self.assertIn(self.prod_obj4, left_leaf.values)
        self.assertIn(self.prod_obj1, left_leaf.values)

        self.assertEqual(right_leaf.keys, ["prod_banana_456"])
        self.assertIn(self.prod_obj2, right_leaf.values)


    def test_04_delete_simple_no_underflow(self):
        tree = self.tree_order3
        tree.insert(self.prod_obj1)
        tree.insert(self.prod_obj2)
        tree.insert(self.prod_obj3)
        # Root (leaf): [apple, banana, cherry]

        self.assertTrue(tree.delete(self.prod_obj2.product_id)) # Delete banana
        self.assertIsNone(tree.search(self.prod_obj2.product_id))
        self.assertEqual(tree.root.keys, [self.prod_obj1.product_id, self.prod_obj3.product_id])
        self.assertEqual(tree.search(self.prod_obj1.product_id), self.prod_obj1)
        self.assertEqual(tree.search(self.prod_obj3.product_id), self.prod_obj3)

        self.assertFalse(tree.delete("non_existent_id"))

    def test_05_delete_causing_underflow_and_merge_root_becomes_leaf(self):
        tree = self.tree_order2 # min_keys = 1
        # Insert obj1, obj2, obj4 (apricot, apple, banana)
        # Root: [banana], L: [apricot, apple], R: [banana]
        tree.insert(self.prod_obj1)
        tree.insert(self.prod_obj2)
        tree.insert(self.prod_obj4)

        # Delete apple (prod_obj1) from L. L becomes [apricot]. Still valid.
        self.assertTrue(tree.delete(self.prod_obj1.product_id))
        self.assertEqual(tree.root.children[0].keys, [self.prod_obj4.product_id]) # Apricot

        # Delete apricot (prod_obj4) from L. L becomes empty -> underflow.
        # L merges with R ([banana]).
        # L gets [banana].
        # Parent root [banana] loses key "banana" and child R.
        # Root.keys=[], Root.children=[L]. Root underflow.
        # New root is L.
        # tree._print_tree_structure(tree.root, 3)
        self.assertTrue(tree.delete(self.prod_obj4.product_id))
        # tree._print_tree_structure(tree.root, 3)
        self.assertTrue(tree.root.is_leaf)
        self.assertEqual(tree.root.keys, [self.prod_obj2.product_id]) # Banana
        self.assertEqual(tree.search(self.prod_obj2.product_id), self.prod_obj2)
        self.assertIsNone(tree.root.parent)

    def test_06_delete_all_elements_empty_tree(self):
        tree = self.tree_order3
        tree.insert(self.prod_obj1)
        tree.insert(self.prod_obj2)

        self.assertTrue(tree.delete(self.prod_obj1.product_id))
        self.assertTrue(tree.delete(self.prod_obj2.product_id))

        self.assertTrue(tree.root.is_leaf)
        self.assertEqual(len(tree.root.keys), 0)
        self.assertEqual(len(tree.root.values), 0)
        self.assertIsNone(tree.search(self.prod_obj1.product_id))

    def test_07_many_insertions_and_deletions_string_keys(self):
        tree = BPlusTreeID(order=4)
        products = []
        num_items = 150 # Should cause multiple splits and merges

        for i in range(num_items):
            # Create somewhat ordered but not perfectly sequential IDs
            # Pad with zeros to ensure lexicographical sort is intuitive
            p_id = f"prod_id_{i:03d}_{chr(97 + (i % 26))}"
            product = Product(p_id, price=float(i + 1))
            products.append(product)
            tree.insert(product)

        # Verify all inserted
        for prod in products:
            self.assertEqual(tree.search(prod.product_id), prod, f"Failed to find {prod.product_id} after insertion batch")

        # Delete items in a shuffled order
        import random
        random.shuffle(products)

        for i in range(num_items // 2):
            prod_to_delete = products.pop()
            self.assertTrue(tree.delete(prod_to_delete.product_id), f"Failed to delete {prod_to_delete.product_id}")
            self.assertIsNone(tree.search(prod_to_delete.product_id), f"{prod_to_delete.product_id} found after deletion")

        # Verify remaining items are still there
        for prod_kept in products:
            self.assertEqual(tree.search(prod_kept.product_id), prod_kept, f"{prod_kept.product_id} missing after partial deletion")
        # tree._print_tree_structure(tree.root, 4)
        # Delete the rest
        while products:
            prod_to_delete = products.pop()
            self.assertTrue(tree.delete(prod_to_delete.product_id), f"Failed to delete remaining {prod_to_delete.product_id}")
            # tree._print_tree_structure(tree.root, 4)
        # print(f"[DEBUG] Final tree root: {tree.root}")
        # print(f"[DEBUG] Final tree root keys: {tree.root.keys}")
        # print(f"[DEBUG] Final tree root is_leaf: {tree.root.is_leaf}")
        # if not tree.root.is_leaf:
        #     print(f"[DEBUG] Final tree root children count: {len(tree.root.children)}")
        #     if tree.root.children:
        #         print(f"[DEBUG] Final tree root first child: {tree.root.children[0]}")
        self.assertTrue(tree.root.is_leaf)
        self.assertEqual(len(tree.root.keys), 0, f"Root keys not empty: {tree.root.keys}")

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)