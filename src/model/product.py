class Product:
    """
    表示一个商品及其相关属性
    """
    __slots__ = ('_product_id', '_name', '_price', '_heat')

    def __init__(self, product_id: str, name: str = "test", price: float = 1.0, heat: float = 1.0):
        """
        初始化一个商品对象

        参数:
            product_id (str): 商品的唯一标识符
            name (str): 商品的名称
            price (float): 商品的价格
            heat (float): 商品的热度
        """
        if not isinstance(product_id, str) or not product_id.strip():
            raise ValueError("product_id必须是一个非空的字符串")
        self._product_id = product_id
        self.name = name
        self.price = price
        self.heat = heat

    @property
    def product_id(self) -> str:
        """获取商品ID"""
        return self._product_id

    @property
    def name(self) -> str:
        """获取商品名称"""
        return self._name

    @name.setter
    def name(self, value: str):
        """设置商品名称"""
        if not isinstance(value, str) or not value.strip():
            raise ValueError("商品名称必须是一个非空的字符串")
        self._name = value

    @property
    def price(self) -> float:
        """获取商品价格"""
        return self._price

    @price.setter
    def price(self, value: float):
        """设置商品价格"""
        if not isinstance(value, (int, float)) or value <= 0:
            raise ValueError("商品价格必须是一个正数")
        self._price = float(value)

    @property
    def heat(self) -> float:
        """获取商品热度"""
        return self._heat

    @heat.setter
    def heat(self, value: float):
        """设置商品热度"""
        if not isinstance(value, (int, float)) or value < 0:
            raise ValueError("商品热度必须是一个非负数字")
        self._heat = float(value)

    def __repr__(self) -> str:
        return (f"Product(id='{self.product_id}', name='{self.name}', "
                f"price={self.price:.2f}, heat={self.heat:.2f})")

    def __str__(self) -> str:
        return self.__repr__()

    def __hash__(self) -> int:
        return hash(self.product_id)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Product):
            return self.product_id == other.product_id
        return False