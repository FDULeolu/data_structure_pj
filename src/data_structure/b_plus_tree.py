import math
import bisect   # 用于支持二分查找，二分查找不是这个数据结构的核心内容，所以为了代码简化在此使用现有函数

from src.model.product import Product



# ---------------- 节点类 ----------------
class BPlusTreeNode:
    """
    B+树的节点类
    """
    def __init__(self, order: int, is_leaf: bool = False):
        """
        初始化 B+ 树节点。

        参数:
            order (int): 节点允许存储的最大键的数量
                         内部节点将有最多 order+1 个子节点指针
                         叶节点将存储最多 order 个键值对
            is_leaf (bool): 标记此节点是否为叶节点
        """
        if not isinstance(order, int) or order < 2:
            raise ValueError("B+树的阶必须是大于等于2的整数")

        self.order: int = order
        self.is_leaf: bool = is_leaf
        self.parent: BPlusTreeNode | None = None  
        self.keys: list = []             # 对于内部节点，keys中的键用来划分区域，对于子节点，keys中的键的位置就是对应的values的位置

        # 内部节点
        self.children: list[BPlusTreeNode] = []  # 存储指向子节点的引用

        # 子节点
        self.values: list = []
        self.next_leaf: BPlusTreeNode | None = None
        self.prev_leaf: BPlusTreeNode | None = None 

    def is_overflow(self) -> bool:
        """检查节点的键数量是否超过上限"""
        return len(self.keys) > self.order

    def min_keys_for_node(self) -> int:
        """
        返回此节点（如果非根）应包含的最小键数
        """
        return math.ceil(self.order / 2)

    def is_deficient(self) -> bool:
        """
        检查节点是否下溢
        """
        if self.parent is None:     # 不考虑根节点的下溢
            return False                        
        return len(self.keys) < self.min_keys_for_node()

    def can_lend_key(self) -> bool:
        """
        检查节点是否有富余的键可以借给兄弟节点（即键数量 > 最小允许数量）
        不考虑根节点，因为根节点不参与这种借用
        """
        if self.parent is None: # 根节点不参与向兄弟借出
            return False
        return len(self.keys) > self.min_keys_for_node()

    def get_num_keys(self) -> int:
        """返回当前节点中的键数量"""
        return len(self.keys)

    def get_num_children(self) -> int:
        """返回当前内部节点的子节点数量"""
        if self.is_leaf:
            return 0
        return len(self.children)
    
    # 用来Debug
    def __str__(self) -> str:
        if self.is_leaf:
            if len(self.values) == 0:
                return (f"LeafNode(Order:{self.order}, Keys:{self.keys}, ValuesCounts:[{self.values}], ")
            if isinstance(self.values[0], Product):
                return (f"LeafNode(Order:{self.order}, Keys:{self.keys}, ValuesCounts:[{self.values}], ")
            else:
                val_counts_str = ", ".join([f"{k}:{len(v_list)}" for k, v_list in zip(self.keys, self.values)])
                return (f"LeafNode(Order:{self.order}, Keys:{self.keys}, ValuesCounts:[{val_counts_str}], ")
                
        else:
            return (f"InternalNode(Order:{self.order}, Keys:{self.keys}, "
                    f"ChildrenCount:{len(self.children)})")

    def __repr__(self) -> str:
        return self.__str__()

# ---------------- 主类 ----------------
class BaseBPlusTree:
    """B+树基类"""
    def __init__(self, order: int):
        """
        初始化B+树

        参数:
            order (int): B+树的阶
        """
        if not isinstance(order, int) or order < 2:
            raise ValueError("B+树的阶必须是大于等于2的整数")
        
        # self.root: BPlusTreeNode = BPlusTreeNode(order, is_leaf=True)
        self.order: int = order
    
    def _find_leaf_node(self, key) -> BPlusTreeNode:
        """根据输入的键，找到这个键对应的叶子结点"""
        current_node = self.root
        while not current_node.is_leaf:
            found_next_node = False
            for i, k_node in enumerate(current_node.keys):
                if key < k_node:
                    current_node = current_node.children[i]
                    found_next_node = True
                    break
            if not found_next_node:
                current_node = current_node.children[len(current_node.keys)]
        return current_node
    
    def _split_leaf(self, leaf_to_split: BPlusTreeNode) -> None:
        """辅助函数：分裂一个已满的叶节点"""

        # 创建新的右兄弟叶节点

        new_leaf = BPlusTreeNode(self.order, is_leaf=True)
        new_leaf.parent = leaf_to_split.parent # 新节点与旧节点有相同的父节点 (暂时)

        # print("原节点:", leaf_to_split.keys)

        split_point = math.ceil((self.order + 1) / 2)
        # print("midpoint index:", mid_point_index)

        # 将原叶节点后半部分的键和值移动到新叶节点
        new_leaf.keys = leaf_to_split.keys[split_point:]
        new_leaf.values = leaf_to_split.values[split_point:]


        # 更新原叶节点的键和值
        leaf_to_split.keys = leaf_to_split.keys[:split_point]
        leaf_to_split.values = leaf_to_split.values[:split_point]

        # print("新节点", new_leaf.keys)
        # print("老节点（分裂后）:", leaf_to_split.keys)

        # 更新叶节点链表指针
        new_leaf.next_leaf = leaf_to_split.next_leaf
        if leaf_to_split.next_leaf:
            leaf_to_split.next_leaf.prev_leaf = new_leaf
        leaf_to_split.next_leaf = new_leaf
        new_leaf.prev_leaf = leaf_to_split 

        # 获取要上推到父节点的键 (新叶节点的第一个键)
        key_to_push_up = new_leaf.keys[0]


        # 将键和新节点指针插入到父节点
        self._insert_into_parent(leaf_to_split, key_to_push_up, new_leaf)

    def _insert_into_parent(self, left_child: BPlusTreeNode, key_to_insert: float, right_child: BPlusTreeNode):
        """
        辅助函数：在父节点中插入一个键和指向新右子节点的指针，left_child 是分裂前的节点（现在是分裂后的左节点），key_to_insert 是分隔 left_child 和 right_child 的键，right_child 是分裂后产生的新右节点
        """
        parent = left_child.parent

        if parent is None: # 如果 left_child 是根节点，需要创建一个新的根
            new_root = BPlusTreeNode(self.order, is_leaf=False)
            new_root.keys = [key_to_insert]
            new_root.children = [left_child, right_child]
            self.root = new_root
            left_child.parent = new_root
            right_child.parent = new_root
            return

        # 非根节点，将 key_to_insert 和 right_child 插入父节点
        # 找到 key_to_insert 在父节点 keys 列表中的插入位置
        chile_insert_idx = parent.children.index(left_child)
        
        parent.keys.insert(chile_insert_idx, key_to_insert)
        parent.children.insert(chile_insert_idx + 1, right_child)  # 由于在内部节点中，键只用于做分割，而不是一一对应
        right_child.parent = parent

        # 检查父节点是否溢出，如果溢出，继续分裂父节点，此时父节点一定是内部节点
        if parent.is_overflow(): 
            self._split_internal_node(parent)

    def _split_internal_node(self, node_to_split: BPlusTreeNode):
        """辅助函数：分裂一个已满的内部节点"""
        new_internal_node = BPlusTreeNode(self.order, is_leaf=False)
        new_internal_node.parent = node_to_split.parent

        # 计算分裂点
        mid_key_index = self.order // 2

        # 获取分裂点的键
        key_to_push_up = node_to_split.keys[mid_key_index]

        # 新内部节点获取原节点的后半部分键和相应的子节点
        new_internal_node.keys = node_to_split.keys[mid_key_index + 1:]
        new_internal_node.children = node_to_split.children[mid_key_index + 1:]

        # 更新被移动到新内部节点的子节点的父指针
        for child in new_internal_node.children:
            child.parent = new_internal_node

        # 原内部节点保留前半部分
        node_to_split.keys = node_to_split.keys[:mid_key_index]
        node_to_split.children = node_to_split.children[:mid_key_index + 1]

        # 将上推的键和新内部节点插入到父节点
        self._insert_into_parent(node_to_split, key_to_push_up, new_internal_node)


    # def delete(self, price: float, product_id: str) -> bool:
    #     """
    #     从B+树中删除一个具有指定价格和product_id的商品

    #     参数:
    #         price (float): 要删除的商品的价格
    #         product_id (str): 要删除的商品的唯一ID

    #     返回:
    #         bool: 如果成功找到并删除商品则返回True，否则返回False
    #     """
    #     leaf_node = self._find_leaf_node(price)
    #     # print("找到了叶子结点！", leaf_node.keys, leaf_node.values)
    #     # 在叶节点中查找并移除商品
    #     try:
    #         key_index_in_leaf = leaf_node.keys.index(price)
    #         products_at_this_price = leaf_node.values[key_index_in_leaf]
            
    #         # print("找到了！", products_at_this_price)

    #         product_to_remove = None
    #         for p_obj in products_at_this_price:
    #             if p_obj.product_id == product_id:
    #                 product_to_remove = p_obj
    #                 break
            
    #         if product_to_remove:
    #             products_at_this_price.remove(product_to_remove)

    #             # 如果这个价格下没有其他商品了，则需要移除整个键
    #             if not products_at_this_price:
    #                 leaf_node.keys.pop(key_index_in_leaf)
    #                 leaf_node.values.pop(key_index_in_leaf)

    #                 # 当键被移除后，需要考察节点是否下溢
    #                 if self.root == leaf_node and not leaf_node.keys:   # 根是叶子，且现在为空的
    #                     pass 
    #                 elif leaf_node.is_deficient():                      # 如果当前节点发生下溢，且不是空根叶子节点
    #                     self._handle_leaf_node_underflow(leaf_node) 
                
    #             return True
    #         else:
    #             return False                                        # 商品ID在该价格下未找到
    #     except ValueError:
    #         # print("没找到！", [price, product_id])
    #         # print("self._find_leaf_node返回的叶子结点", leaf_node.keys, leaf_node.values)
    #         return False                                            # 价格不存在于该叶节点



    def _handle_leaf_node_underflow(self, leaf_node: BPlusTreeNode):
        """处理叶节点下溢。尝试从兄弟节点借用，否则进行合并"""
        if leaf_node.parent is None:        # 根节点作为叶子，如果键为空则树为空，已在delete中处理
            return

        parent = leaf_node.parent
        # 找到当前叶节点在父节点children列表中的索引，以及其左右兄弟
        child_index = parent.children.index(leaf_node)
        

        # 尝试从右兄弟借用
        if child_index < len(parent.children) - 1:                      # 如果有右兄弟
            right_sibling = parent.children[child_index + 1]
            if right_sibling.is_leaf and right_sibling.can_lend_key():  # 且右兄弟是叶子且有富余key
                
                # 获取右兄弟第一个key和value
                borrowed_key = right_sibling.keys.pop(0)                
                borrowed_value_list = right_sibling.values.pop(0)

                # 添加到原节点最后
                leaf_node.keys.append(borrowed_key)
                leaf_node.values.append(borrowed_value_list)

                # 更新父节点中分隔这两个兄弟的键
                parent.keys[child_index] = right_sibling.keys[0]
                return

        # 尝试从左兄弟借用
        if child_index > 0:                                             # 如果有左兄弟
            left_sibling = parent.children[child_index - 1]
            if left_sibling.is_leaf and left_sibling.can_lend_key():    # 且左兄弟是叶子且有富余key
                
                # 获取右兄弟最后一个key和value
                borrowed_key = left_sibling.keys.pop()
                borrowed_value_list = left_sibling.values.pop()

                # 添加到原节点最开始
                leaf_node.keys.insert(0, borrowed_key)
                leaf_node.values.insert(0, borrowed_value_list)

                # 更新父节点中分隔这两个兄弟的键
                parent.keys[child_index - 1] = leaf_node.keys[0]
                return


        # 如果无法从兄弟节点借用，则进行合并
        if child_index < len(parent.children) - 1:                      # 如果有右兄弟，则与右兄弟合并
            
            # 合并右兄弟
            right_sibling = parent.children[child_index + 1]
            leaf_node.keys.extend(right_sibling.keys)
            leaf_node.values.extend(right_sibling.values)
            
            # 更新链表指针
            leaf_node.next_leaf = right_sibling.next_leaf
            if right_sibling.next_leaf:
                right_sibling.next_leaf.prev_leaf = leaf_node
            
            # 从父节点移除分隔键和指向右兄弟的指针, 分隔键在 parent.keys[child_index], 指向右兄弟的指针在 parent.children[child_index + 1]
            parent.keys.pop(child_index)
            parent.children.pop(child_index + 1)
            
            if parent == self.root:
                # print("这个根节点是否下溢:", parent.is_deficient())
                self._handle_internal_node_underflow(parent)
            # 检查父内部节点是否下溢
            if parent.is_deficient(): # 且 parent 不是根或者根的特殊情况
                 self._handle_internal_node_underflow(parent) 

        elif child_index > 0:                                           # 只有左兄弟，与左兄弟合并

            # 把当前节点合并到左兄弟
            left_sibling = parent.children[child_index - 1]
            left_sibling.keys.extend(leaf_node.keys)
            left_sibling.values.extend(leaf_node.values)

            # 更新链表指针
            left_sibling.next_leaf = leaf_node.next_leaf
            if leaf_node.next_leaf:
                leaf_node.next_leaf.prev_leaf = left_sibling
            
            # 从父节点移除分隔键和指向当前节点的指针, 分隔键在 parent.keys[child_index - 1], 指向当前节点的指针在 parent.children[child_index]
            parent.keys.pop(child_index - 1)
            parent.children.pop(child_index)
            
            if parent == self.root:
                # print("这个根节点是否下溢:", parent.is_deficient())
                self._handle_internal_node_underflow(parent)
            # 检查父内部节点是否下溢
            if parent.is_deficient():
                 self._handle_internal_node_underflow(parent)

    def _handle_internal_node_underflow(self, internal_node: BPlusTreeNode):
        """处理内部节点下溢。尝试从兄弟节点借用，否则进行合并"""

        # if internal_node.parent is None: # 如果是根内部节点
        #     # print(f"[DEBUG _handle_internal_node_underflow] Handling root underflow. Initial internal_node: {internal_node}")
        #     # 循环处理根节点收缩，直到根不再是“空内部节点且只有一个孩子”的情况
        #     # 或者直到根是叶子节点
        #     current_potential_root = internal_node
        #     while not current_potential_root.is_leaf and \
        #         not current_potential_root.keys and \
        #         len(current_potential_root.children) == 1:
        #         # print(f"[DEBUG _handle_internal_node_underflow] Root ({current_potential_root}) is becoming its single child.")
        #         current_potential_root = current_potential_root.children[0]
        #         # self.root = current_potential_root # 更新树的根
        #         # self.root.parent = None
            
        #     # 循环结束后，current_potential_root 是最终的根
        #     if self.root != current_potential_root: # 如果根确实发生了变化
        #         self.root = current_potential_root
        #         self.root.parent = None # 确保最终根的父指针是 None
        #         # print(f"[DEBUG _handle_internal_node_underflow] Final new root: {self.root}, is_leaf: {self.root.is_leaf}")
        #     return
        parent = internal_node.parent

        if parent is None:  # 要处理的内部节点是根节点
            if not internal_node.keys and internal_node.children:
                self.root = internal_node.children[0]
                self.root.parent = None
            return 
        
        child_index = parent.children.index(internal_node)

        # 尝试从右兄弟内部节点借用
        if child_index < len(parent.children) - 1:
            right_sibling = parent.children[child_index + 1]
            if not right_sibling.is_leaf and right_sibling.can_lend_key():

                # 父节点中分隔 right_sibling 和 internal_node 的键下放 internal_node
                key_from_parent = parent.keys[child_index]
                internal_node.keys.append(key_from_parent)
                
                # right_sibling的第一个孩子移动到internal_node的末尾
                child_to_move = right_sibling.children.pop(0)
                child_to_move.parent = internal_node
                internal_node.children.append(child_to_move)
                
                # right_sibling的第一个键上移到父节点，替换原来的分隔键
                parent.keys[child_index] = right_sibling.keys.pop(0)
                return

        # 尝试从左兄弟内部节点借用
        if child_index > 0:
            left_sibling = parent.children[child_index - 1]
            if not left_sibling.is_leaf and left_sibling.can_lend_key():

                # 父节点中分隔 left_sibling 和 internal_node 的键下放 internal_node
                key_from_parent = parent.keys[child_index - 1]
                internal_node.keys.insert(0, key_from_parent)

                # left_sibling 的最后一个孩子移动到 internal_node 的开头
                child_to_move = left_sibling.children.pop(-1)
                child_to_move.parent = internal_node
                internal_node.children.insert(0, child_to_move)

                # left_sibling 的最后一个键上移到父节点，替换原来的分隔键
                parent.keys[child_index - 1] = left_sibling.keys.pop(-1)
                return

        # 如果无法借用，则进行合并
        if child_index < len(parent.children) - 1:              # 与右兄弟合并
            right_sibling = parent.children[child_index + 1]

            # 父节点中分隔它们的键下放到 internal_node
            key_from_parent = parent.keys.pop(child_index)
            internal_node.keys.append(key_from_parent)
            
            # 将右兄弟的键和孩子全部合并到 internal_node
            internal_node.keys.extend(right_sibling.keys)
            internal_node.children.extend(right_sibling.children)

            # 更新被移动孩子的父指针
            for child in right_sibling.children:
                child.parent = internal_node
            
            # 从父节点中移除指向右兄弟的指针
            parent.children.pop(child_index + 1)

        elif child_index > 0:                                   # 把当前节点合并到左兄弟
            left_sibling = parent.children[child_index - 1]

            # 父节点中分隔它们的键下放到 left_sibling
            key_from_parent = parent.keys.pop(child_index - 1)
            left_sibling.keys.append(key_from_parent)
            
            # 将 internal_node 的键和孩子全部合并到 left_sibling
            left_sibling.keys.extend(internal_node.keys)
            left_sibling.children.extend(internal_node.children)

            # 更新被移动孩子的父指针
            for child in internal_node.children:
                child.parent = left_sibling
                
            # 从父节点中移除指向 internal_node 的指针
            parent.children.pop(child_index)
        
        # 检查父节点是否因此次键和指针的移除而下溢
        if parent.is_deficient():
            self._handle_internal_node_underflow(parent)
        elif parent == self.root:
            self._handle_internal_node_underflow(parent)


    def _print_tree_structure(self, node: BPlusTreeNode = None, level: int = 0, prefix: str = "Root:"):
        """辅助函数，用于打印树的结构 (调试用)。"""
        if node is None:
            if not hasattr(self, 'root') or self.root is None : # 防御性检查
                print("树为空或未初始化根节点。")
                return
            node = self.root
        
        print(" " * (level * 4) + prefix + str(node)) # 使用节点的 __str__
        if not node.is_leaf:
            for i, child in enumerate(node.children):
                # 构造传递给下一层的前缀
                # 如果是最后一个孩子，连接线不同
                if isinstance(node.children, list):
                    is_last_child = (i == len(node.children) - 1)
                else:
                    is_last_child == True
                child_prefix = "  └── " if is_last_child else "  ├── "
                self._print_tree_structure(child, level + 1, child_prefix)
        print()




class BPlusTreeProducts(BaseBPlusTree):
    """
    B+树数据结构，用于存储和检索Product ID，以商品价格为键
    """

    def __init__(self, order: int):
        """
        初始化B+树

        参数:
            order (int): B+树的阶
        """
        super().__init__(order)
        self.root = BPlusTreeNode(order, is_leaf=True)

    # def _find_leaf_node(self, price: float) -> BPlusTreeNode:
    #     """
    #     从根开始查找给定价格应该属于的叶节点，返回包含该价格或价格应插入位置的叶节点
    #     """
    #     current_node = self.root
    #     while not current_node.is_leaf:
    #         idx = bisect.bisect_right(current_node.keys, price)
    #         current_node = current_node.children[idx]
    #     return current_node

    def search_exact(self, price: float, product_id_to_find: str = None) -> list[Product]:
        """
        精确查找具有指定价格的商品，如果提供了 product_id_to_find，则在相同价格的商品中进一步筛选特定ID的商品。

        参数:
            price (float): 要查找的商品价格
            product_id_to_find (str, 可选): 要精确查找的商品ID

        返回:
            list[Product]: 包含所有匹配商品的列表。如果未找到，则为空列表
        """
        leaf_node = self._find_leaf_node(price)
        found_products = []

        try:
            key_index = leaf_node.keys.index(price)
            
            products_at_this_price = leaf_node.values[key_index]
            if product_id_to_find:
                for product in products_at_this_price:
                    if product == product_id_to_find:
                        found_products.append(product)
                        break 
            else:
                found_products.extend(products_at_this_price)
        except ValueError:
            pass 
            
        return found_products

    def search_range(self, min_price: float, max_price: float) -> list[str]:
        """
        查找价格在 [min_price, max_price] (包含边界) 区间内的所有商品

        参数:
            min_price (float): 最小价格
            max_price (float): 最大价格

        返回:
            list[Product]: 包含所有在指定价格范围内的商品的列表
        """
        if min_price > max_price:
            return []

        results = []
        current_leaf = self._find_leaf_node(min_price) # 定位到可能包含min_price的起始叶节点

        # 遍历叶节点链表
        while current_leaf is not None:
            for i, key_price in enumerate(current_leaf.keys):
                if key_price > max_price:
                    return results 

                if key_price >= min_price:
                    results.extend(current_leaf.values[i]) 
            
            if not current_leaf.keys or current_leaf.keys[-1] <= max_price: # 倘若当前节点的最大值小余搜索上界，进入相邻节点继续搜索
                current_leaf = current_leaf.next_leaf
        
        return results

    def insert(self, price: float, product_id: str) -> None:
        """
        向B+树中插入一个商品ID

        参数:
            product (str): 要插入的商品ID
        """

        leaf_node_to_insert_in = self._find_leaf_node(price)

        self._insert_into_leaf(leaf_node_to_insert_in, price, product_id)

        if leaf_node_to_insert_in.is_overflow():        # 如果此次插入导致节点上溢了，那么尝试分裂节点
            self._split_leaf(leaf_node_to_insert_in)
            
    def _insert_into_leaf(self, leaf: BPlusTreeNode, price: float, product: str) -> None:
        """辅助函数：将商品插入到指定的叶节点中"""
        insertion_point = bisect.bisect_left(leaf.keys, price)

        if insertion_point < len(leaf.keys) and leaf.keys[insertion_point] == price:
            # 价格已存在，将商品添加到对应的值列表中
            leaf.values[insertion_point].append(product)
            # # 按照id排序
            # leaf.values[insertion_point].sort(key = product.)
        else:
            # 价格不存在，插入新的键和新的值列表
            leaf.keys.insert(insertion_point, price)
            leaf.values.insert(insertion_point, [product]) # 创建一个新的列表包含此product

    def delete(self, price: float, product_id: str) -> bool:
        """
        从B+树中删除一个具有指定价格和product_id的商品

        参数:
            price (float): 要删除的商品的价格
            product_id (str): 要删除的商品的唯一ID

        返回:
            bool: 如果成功找到并删除商品则返回True，否则返回False
        """
        leaf_node = self._find_leaf_node(price)
        # print("找到了叶子结点！", leaf_node.keys, leaf_node.values)
        # 在叶节点中查找并移除商品
        try:
            key_index_in_leaf = leaf_node.keys.index(price)
            products_at_this_price = leaf_node.values[key_index_in_leaf]
            
            # print("找到了！", products_at_this_price)

            product_to_remove = None
            for p_obj in products_at_this_price:
                if p_obj == product_id:
                    product_to_remove = p_obj
                    break
            
            if product_to_remove:
                products_at_this_price.remove(product_to_remove)

                # 如果这个价格下没有其他商品了，则需要移除整个键
                if not products_at_this_price:
                    leaf_node.keys.pop(key_index_in_leaf)
                    leaf_node.values.pop(key_index_in_leaf)

                    # 当键被移除后，需要考察节点是否下溢
                    if self.root == leaf_node and not leaf_node.keys:   # 根是叶子，且键空了，说明整个树是空的，跳过，如果这个根是叶子，且键非空，不对非空根叶节点设置下溢阈值
                        pass 
                    elif leaf_node.is_deficient():                      # 如果当前节点发生下溢，且不是空根叶子节点
                        self._handle_leaf_node_underflow(leaf_node) 
                
                return True
            else:
                return False                                        # 商品ID在该价格下未找到
        except ValueError:
            # print("没找到！", [price, product_id])
            # print("self._find_leaf_node返回的叶子结点", leaf_node.keys, leaf_node.values)
            return False                                            # 价格不存在于该叶节点



class BPlusTreeID(BaseBPlusTree):
    """
    B+树，以product id为键，Product对象为值
    """
    def __init__(self, order: int):
        """
        初始化B+树

        参数:
            order (int): B+树的阶
        """
        super().__init__(order)
        self.root = BPlusTreeNode(order, is_leaf=True)

    # def _find_leaf_node(self, produtid: str) -> BPlusTreeNode:
    #     """
    #     从根开始查找给定ID的Product对象，返回存储该对象的叶子节点
    #     """
    #     current_node = self.root
    #     while not current_node.is_leaf:
    #         idx = bisect.bisect_right(current_node.keys, produtid)
    #         current_node = current_node.children[idx]
    #     return current_node

    def search(self, productid: str) -> Product:
        """
        精确查找具有指定ID的商品

        参数:
            price (str): 要查找的商品id

        返回:
            Product: 包含该商品ID的Product对象，若没找到，返回None
        """
        leaf_node = self._find_leaf_node(productid)

        try:
            key_index = leaf_node.keys.index(productid)
            products_at_this_price = leaf_node.values[key_index]
            return products_at_this_price
        except ValueError:
            return None


    def insert(self, product: Product, test=False) -> None:
        """
        向B+树中插入一个商品

        参数:
            productid (Product): 要插入的商品
        """
        if not isinstance(product, Product):
            raise TypeError("插入的对象必须是 Product 类型")

        prodict_id = product.product_id
        leaf_node_to_insert_in = self._find_leaf_node(prodict_id)

        self._insert_into_leaf(leaf_node_to_insert_in, prodict_id, product, test)

        if leaf_node_to_insert_in.is_overflow():        # 如果此次插入导致节点上溢了，那么尝试分裂节点
            self._split_leaf(leaf_node_to_insert_in)
            
    def _insert_into_leaf(self, leaf: BPlusTreeNode, product_id: str, product: Product, test = False) -> None:
        """辅助函数：将商品插入到指定的叶节点中"""
        insertion_point = bisect.bisect_left(leaf.keys, product_id)
        # if test:
        #     print("key:", leaf.keys, "insertion_point", insertion_point, "value:", leaf.values)

        leaf.keys.insert(insertion_point, product_id)
        leaf.values.insert(insertion_point, product) # 创建一个新的列表包含此product

    def delete(self, product_id: str) -> bool:
        """
        从B+树中删除一个具有指定product_id的商品

        参数:
            product_id (str): 要删除的商品的唯一ID

        返回:
            bool: 如果成功找到并删除商品则返回True，否则返回False
        """
        leaf_node = self._find_leaf_node(product_id)
        # print("找到了叶子结点！", leaf_node.keys, leaf_node.values)
        # 在叶节点中查找并移除商品
        try:
            key_index_in_leaf = leaf_node.keys.index(product_id)
            # products_to_remove = leaf_node.values[key_index_in_leaf]
            
            # leaf_node.values.remove(products_to_remove)

            
            leaf_node.keys.pop(key_index_in_leaf)
            leaf_node.values.pop(key_index_in_leaf)

            # 当键被移除后，需要考察节点是否下溢
            if self.root == leaf_node and not leaf_node.keys:   # 根是叶子，且现在为空的
                pass
            elif leaf_node.is_deficient():                      # 如果当前节点发生下溢，且不是空根叶子节点
                self._handle_leaf_node_underflow(leaf_node) 
            return True
        except ValueError:
            return False                                            # 价格不存在于该叶节点