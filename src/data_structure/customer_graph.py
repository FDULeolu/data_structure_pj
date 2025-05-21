class CustomerGraph:
    """
    一个用于表示客户关系网络的加权有向图 
    客户是图中的节点，客户之间的影响力是带权重的有向边 
    使用邻接列表的方式存储图 
    """

    def __init__(self):
        """
        初始化一个空的客户关系图 
        self._adj_list 是一个字典，用于存储邻接列表 
        键是客户名称 (str)，值是另一个字典 
        内部字典的键是该客户直接影响的目标客户名称 (str)，
        值是影响力权重 (float) 
        """
        self._adj_list = {}

    def add_customer(self, customer_name: str):
        """
        向图中添加一个新客户（节点） 
        如果客户已存在，则不执行任何操作 

        参数:
            customer_name (str): 要添加的客户的名称 
        """
        if not isinstance(customer_name, str):
            raise TypeError(f"错误: 客户名称 '{customer_name}' 必须是字符串，但收到了{type(customer_name)}")
            return
        if customer_name not in self._adj_list:
            self._adj_list[customer_name] = {}

    def get_all_customers(self) -> list:
        """
        返回图中所有客户名称的列表 

        返回:
            list: 包含所有客户名称的列表 
        """
        return list(self._adj_list.keys())

    def add_influence(self, from_customer: str, to_customer: str, weight: float):
        """
        在两个客户之间添加一条有向的影响力关系（边） 
        如果 'from_customer' 或 'to_customer' 不在图中，会先将它们添加进来 

        参数:
            from_customer (str): 施加影响的客户名称（边的起始节点） 
            to_customer (str): 受到影响的客户名称（边的结束节点） 
            weight (float): 影响力权重 应为数字 
        """
        if not isinstance(from_customer, str) or not isinstance(to_customer, str):
            raise TypeError(f"错误: 客户名称 '{from_customer}' 以及 '{to_customer}' 必须是字符串，但收到了{type(from_customer)}以及{type(to_customer)}")
            return
        if not isinstance(weight, (int, float)):
            raise TypeError(f"错误: 影响力权重 '{weight}' 必须是数字，但收到了{type(weight)}")
            return
        if weight < 0:
            raise ValueError(f"警告: 影响力权重 '{weight}' 不允许为负数")
        if weight > 1:
            raise ValueError(f"警告: 影响力权重 '{weight}' 不允许大于1")


        # 确保起始客户和目标客户都在图中
        self.add_customer(from_customer)
        self.add_customer(to_customer)

        # 添加有向边和权重
        self._adj_list[from_customer][to_customer] = weight

    def get_direct_influencees(self, customer_name: str) -> dict:
        """
        获取一个客户直接影响的所有其他客户及其对应的影响力权重 

        参数:
            customer_name (str): 要查询的客户名称 

        返回:
            dict: 一个字典，键是该客户直接影响的目标客户名称，值是影响力权重 
                  如果客户不存在或没有影响其他任何人，则返回空字典
        """
        if not isinstance(customer_name, str):
            raise TypeError(f"错误: 客户名称 '{customer_name}' 必须是字符串，但收到了{type(customer_name)}")
            return {}
        if customer_name in self._adj_list:
            return self._adj_list[customer_name].copy() # 禁止通过这个方法修改图
        else:
            return {}

    def get_influence_weight(self, from_customer: str, to_customer: str) -> float | None:
        """
        获取从 from_customer 到 to_customer 的直接影响力权重 

        参数:
            from_customer (str): 施加影响的客户名称 
            to_customer (str): 受到影响的客户名称 

        返回:
            float: 如果存在直接影响，则返回影响力权重 
            None: 如果 from_customer 不存在，或者 from_customer 没有直接影响 to_customer 
        """
        if not isinstance(from_customer, str) or not isinstance(to_customer, str):
            raise TypeError(f"错误: 客户名称 '{from_customer}' 以及 '{to_customer}' 必须是字符串，但收到了{type(from_customer)}以及{type(to_customer)}")
            return None
        if from_customer in self._adj_list:
            return self._adj_list[from_customer].get(to_customer)
        else:
            return None

