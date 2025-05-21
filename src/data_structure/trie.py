class TrieNode:
    """
    Trie树的节点类
    """
    __slots__ = ('children', 'is_end_of_word', 'product_ids')
    def __init__(self):
        """
        初始化一个Trie节点
        """

        self.children: dict[str, TrieNode] = {}
        
        self.is_end_of_word: bool = False
        
        # 如果 is_end_of_word 为 True，则此集合存储与该单词关联的一个或多个 product_id
        self.product_ids: set[str] = set() 

    def __repr__(self):
        return (f"TrieNode(children_keys={list(self.children.keys())}, "
                f"is_end={self.is_end_of_word}, product_ids_count={len(self.product_ids)})")

    def __str__(self):
        return self.__repr__()


class ProductPrefixTrie:
    """
    用于商品名称前缀搜索的Trie树
    存储商品名称，并在单词结束节点关联一个或多个product_id
    """
    def __init__(self):
        """
        初始化一个空的Trie树，包含一个根节点
        """
        self.root = TrieNode()

    def insert(self, name: str, product_id: str) -> None:
        """
        向Trie树中插入一个商品名称及其关联的 product_id

        参数:
            name (str): 要插入的商品名称
            product_id (str): 与该商品名称关联的商品ID
        """
        if not isinstance(name, str) or not name:
            return
        if not isinstance(product_id, str) or not product_id:
            return

        node = self.root
        for char in name:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        
        # 到达单词末尾
        if isinstance(product_id, str) and product_id: 
            node.is_end_of_word = True
            node.product_ids.add(product_id)

    def _find_prefix_node(self, prefix: str) -> TrieNode | None:
        """
        辅助函数：查找给定前缀在Trie树中对应的节点

        参数:
            prefix (str): 要查找的前缀

        返回:
            TrieNode | None: 如果前缀存在，则返回前缀末尾字符对应的节点；否则返回None
        """
        node = self.root
        for char in prefix:
            if char in node.children:
                node = node.children[char]
            else:
                return None
        return node

    def get_product_ids_with_prefix(self, prefix: str) -> set[str]:
        """
        获取所有以指定前缀开头的商品名称所关联的product_id集合

        参数:
            prefix (str): 商品名称前缀

        返回:
            set[str]: 一个包含所有匹配商品product_id的集合
        """
        prefix_node = self._find_prefix_node(prefix)
        if prefix_node is None:
            return set()

        # 从前缀节点开始，收集所有后续的product_id
        product_ids_found = set()
        
        stack = [prefix_node] 
        
        while stack:
            current_node = stack.pop()
            
            if current_node.is_end_of_word:
                product_ids_found.update(current_node.product_ids)
            
            for char, child_node in current_node.children.items():
                stack.append(child_node)
                
        return product_ids_found

    def delete(self, name: str, product_id: str) -> bool:
        """
        从Trie树中删除一个商品名称与特定product_id的关联
        如果删除后某些节点变为冗余（非单词结尾且无子节点），则会清理这些节点

        参数:
            name (str): 要删除的商品名称
            product_id (str): 要从该名称关联中移除的特定商品ID

        返回:
            bool: 如果成功找到并移除了关联，则返回 True；否则返回 False
        """

        # 找到单词路径上的所有节点，并记录每个节点的父节点和对应的字符
        path_trace = []
        current_node = self.root # 用一个新变量来追踪，避免混淆 current_node 的角色
        for char_idx, char in enumerate(name):
            if char in current_node.children:
                child_node = current_node.children[char]
                path_trace.append({'parent': current_node, 
                                'char_on_edge': char, 
                                'node': child_node})
                current_node = child_node # 前进到子节点
            else:
                return False # 名称不存在于Trie中

        if not current_node.is_end_of_word or product_id not in current_node.product_ids:
            return False 

        # 移除 product_id 的关联
        current_node.product_ids.remove(product_id)
        if not current_node.product_ids:    # 如果当前的节点不再存储商品名，那么将当前节点标注为非单词结尾
            current_node.is_end_of_word = False

        # 回溯并清理冗余节点
        if not current_node.is_end_of_word and not current_node.children:
            for i in range(len(path_trace) - 1, -1, -1):
                parent_of_node_to_delete = path_trace[i]['parent'] # 这是真正要修改的父节点
                char_edge_to_delete = path_trace[i]['char_on_edge']
                node_to_delete = path_trace[i]['node']

                if parent_of_node_to_delete is None:
                    parent_of_node_to_delete = self.root


                if not node_to_delete.is_end_of_word and not node_to_delete.children:
                    del parent_of_node_to_delete.children[char_edge_to_delete]
                else:
                    break 
        
        return True