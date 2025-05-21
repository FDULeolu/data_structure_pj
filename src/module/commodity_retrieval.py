import uuid
import time

from src.model.product import Product
from src.data_structure.trie import *
from src.data_structure.b_plus_tree import *


class ProductManager:
    def __init__(self, btree_order: int = 3):
        """
        初始化商品目录管理器。

        参数:
            btree_order (int): 用于内部B+树的阶
        """
        self._product_id_index: BPlusTreeID = BPlusTreeID(order=btree_order)        # product_id - Product对象
        self._price_index: BPlusTreeProducts = BPlusTreeProducts(order=btree_order) # price - product_id
        self._name_prefix_trie: ProductPrefixTrie = ProductPrefixTrie()

    def _generate_product_id(self) -> str:
        """生成一个唯一的商品ID"""

        now_struct = time.localtime()
        timestamp_prefix = time.strftime("%Y%m%d%H%M%S", now_struct)
        microseconds = f"{int((time.time() % 1) * 1_000_000):06d}"
        unique_suffix = uuid.uuid4().hex
        return f"PROD-{timestamp_prefix}{microseconds}-{unique_suffix}"


    def add_product(self, name: str, price: float, heat: float) -> Product | None:
        """
        向目录中添加新商品。自动生成id

        返回:
            成功则返回 Product 对象，否则返回 None
        """

        product_id = self._generate_product_id()

        try:
            product = Product(product_id, name, price, heat)
        except ValueError as e:
            return None

        self._product_id_index.insert(product)
        self._price_index.insert(price, product_id) # B+树按价格索引Product对象
        self._name_prefix_trie.insert(product.name, product.product_id)
        
        return product

    def get_product_by_id(self, product_id: str) -> Product | None:
        """通过ID获取商品。"""
        return self._product_id_index.search(product_id)

    def delete_product(self, product_id: str) -> bool:
        """通过ID删除商品，并同步更新所有索引。"""
        product_to_delete = self._product_id_index.search(product_id)
        if not product_to_delete:
            return False
        
        old_price = product_to_delete.price
        old_name = product_to_delete.name

        # 从B+树价格索引中删除
        if not self._price_index.delete(old_price, product_id):
            raise IndexError(f"价格索引树中找不到键 {product_id}")

        # 从名称前缀Trie树中删除
        if not self._name_prefix_trie.delete(old_name, product_id):
            raise IndexError(f"警告: 从Trie树删除 (name:{old_name}, id:{product_id}) 时未找到或失败。")

        # 从主存储B+树中删除
        if not self._product_id_index.delete(product_id):
            raise IndexError(f"ID索引树中找不到键 {product_id}")
        
        return True

    def update_product(self, product_id: str,
                       new_name: str = None,
                       new_price: float = None,
                       new_heat: float = None) -> bool:
        """
        更新商品信息。
        如果价格或名称改变，会相应地更新B+树和Trie树索引。
        """
        product_to_update = self._product_id_index.search(product_id)
        if not product_to_update:
            return False
        
        old_price = product_to_update.price
        old_name = product_to_update.name
        
        something_actually_changed = False

        try:
            product_to_update.name = new_name
            product_to_update.price = new_price
            product_to_update.heat = new_heat


            # 标记哪些关键索引字段发生了变化
            name_changed = (new_name is not None and new_name != old_name)
            price_changed = (new_price is not None and abs(new_price - old_price) > 1e-9) # 浮点比较

            # 如果名称改变，更新Trie树
            if name_changed:
                self._name_prefix_trie.delete(old_name, product_id) # 删除旧名称的关联
                self._name_prefix_trie.insert(new_name, product_id) # 插入新名称的关联
                something_actually_changed = True

            # 如果价格改变，更新B+树
            if price_changed:
                self._price_index.delete(old_price, product_id) # 从B+树删除旧价格条目
                self._price_index.insert(new_price, product_id) # 将更新了价格的对象重新插入B+树
                something_actually_changed = True
            
            # 更新热度 (如果提供了且有变化)
            if new_heat is not None and abs(product_to_update.heat - new_heat) > 1e-9:
                product_to_update.heat = new_heat
                something_actually_changed = True

        except Exception as e: 
            return False 
            
        return something_actually_changed


    def search_by_price_range(self, min_price: float, max_price: float) -> list[Product]:
        """按价格范围搜索商品，返回商品"""
        if not (isinstance(min_price, (int, float)) and isinstance(max_price, (int, float))):
            return []
        range_id = self._price_index.search_range(min_price, max_price)
        product = []
        for id in range_id:
            product.append(self._product_id_index.search(id))
        return product

    def search_by_exact_price(self, price: float, product_id_to_find: str = None) -> list[Product]:
        """按精确价格搜索商品（可选具体ID）"""
        if not isinstance(price, (int, float)):
            return []
        exact_id = self._price_index.search_exact(price, product_id_to_find)
        product = []
        for id in exact_id:
            product.append(self._product_id_index.search(id))
        return product

    def recommend_products_by_prefix(self, name_prefix: str, k: int) -> list[Product]:
        """
        根据商品名称前缀进行搜索，并按热度推送最高的k个商品，如果k为-1，则返回所有匹配的商品
        """
        if not isinstance(name_prefix, str): 
            return []
        if not isinstance(k, int) or k < -1:
            return []

        matching_product_ids = self._name_prefix_trie.get_product_ids_with_prefix(name_prefix)
        
        candidate_products = []
        for pid in matching_product_ids:
            product = self.get_product_by_id(pid)
            if product:
                candidate_products.append(product)
        
        # 按热度降序排序
        candidate_products.sort(key=lambda p: p.heat, reverse=True)
        
        return candidate_products[:k]
    
    def search_products_name(self, name: str) -> list[Product]:
        """根据商品名称进行搜索，仅返回名称匹配的"""
        candidate_products = self.recommend_products_by_prefix(name, -1)
        search_result = []
        for product in candidate_products:
            if product.name == name:
                search_result.append(product)
        
        return search_result