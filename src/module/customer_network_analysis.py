from src.data_structure.customer_graph import CustomerGraph


# --------------------- 加权度中心性 ---------------------
def calculate_weighted_out_degree_centrality(graph: CustomerGraph) -> dict:
    """
    计算图中每个客户的加权出度中心性

    参数:
        graph (CustomerGraph): `CustomerGraph`对象

    返回:
        dict: 字典，键是客户名称 (str), 值是其加权出度中心性得分 (float)
    """
    if not isinstance(graph, CustomerGraph):
        raise TypeError("输入必须是一个 CustomerGraph 对象")

    centrality_scores = {}
    all_customers = graph.get_all_customers()

    if not all_customers:
        return {} 

    for customer_name in all_customers:
        weighted_out_degree = 0.0
        direct_influencees = graph.get_direct_influencees(customer_name)
        for _, weight in direct_influencees.items():
                weighted_out_degree += weight
        centrality_scores[customer_name] = weighted_out_degree
    
    return centrality_scores


def calculate_weighted_in_degree_centrality(graph: CustomerGraph) -> dict:
    """
    计算图中每个客户的加权入度中心性

    参数:
        graph (CustomerGraph): `CustomerGraph`对象

    返回:
        dict: 字典，键是客户名称 (str), 值是其加权入度中心性得分 (float)
    """
    if not isinstance(graph, CustomerGraph):
        raise TypeError("输入必须是一个 CustomerGraph 对象")

    centrality_scores = {}
    all_customers = graph.get_all_customers()

    if not all_customers:
        return {}

    for customer_name in all_customers:
        centrality_scores[customer_name] = 0.0

    for source_customer in all_customers:
        direct_influencees = graph.get_direct_influencees(source_customer)
        for target_customer, weight in direct_influencees.items():
            centrality_scores[target_customer] += weight
    return centrality_scores


# --------------------- PageRank ---------------------
def _preprocess_for_pagerank(graph: CustomerGraph) -> tuple[dict, dict]:
    """
    为PageRank算法进行预处理:
    1. 构建入链字典 (target_node -> {source_node: weight})
    2. 获取所有节点的加权出度

    参数:
        graph (CustomerGraph): `CustomerGraph`对象

    返回:
        tuple: (incoming_links_map, weighted_out_degrees)
               incoming_links_map: dict, {节点: {来源节点1: 权重1, 来源节点2: 权重2, ...}}
               weighted_out_degrees: dict, {节点: 加权出度}
    """
    all_customers = graph.get_all_customers()
    incoming_links_map = {customer: {} for customer in all_customers}

    # 计算加权出度
    weighted_out_degrees = calculate_weighted_out_degree_centrality(graph)

    # 计算入边及权重
    for source_node in all_customers:
        direct_influencees = graph.get_direct_influencees(source_node)
        for target_node, weight in direct_influencees.items():
            incoming_links_map[target_node][source_node] = weight
    
    return incoming_links_map, weighted_out_degrees


def calculate_pagerank(graph: CustomerGraph, 
                       damping_factor: float = 0.85,
                       max_iterations: int = 10000,
                       epsilon: float = 1e-6) -> dict:
    """
    计算每个客户网络中每个节点的PageRank分数

    参数:
        graph (CustomerGraph): `CustomerGraph`对象
        damping_factor (float): 阻尼因子
        max_iterations (int): 最大迭代次数
        epsilon (float): 收敛阈值

    返回:
        dict: {客户名称: PageRank得分}, 若图为空，则返回空字典
    """
    if not isinstance(graph, CustomerGraph):
        raise TypeError("输入必须是一个 CustomerGraph 对象")
    if not (0 < damping_factor < 1):
        raise ValueError("阻尼因子必须在 0 和 1 之间")
    if not max_iterations > 0:
        raise ValueError("最大迭代次数必须大于 0")
    if not epsilon > 0:
        raise ValueError("Epsilon 必须大于 0")
    
    all_customers = graph.get_all_customers()
    num_customers = len(all_customers)

    if num_customers == 0:
        return {}
    
    incoming_links_map, weighted_out_degrees = _preprocess_for_pagerank(graph)

    pagerank_scores = {customer: 1 / num_customers for customer in all_customers}

    for _ in range(max_iterations):
        new_pagerank_scores = {}
        total_change = 0.0

        # 处理出度为0的节点，将他们的PageRank score均分到所有的节点上
        dangling_nodes_pagerank_sum = 0.0
        for customer in all_customers:
            if weighted_out_degrees.get(customer) == 0:
                dangling_nodes_pagerank_sum += pagerank_scores[customer]
        
        pagerank_from_dangling_nodes = damping_factor * (dangling_nodes_pagerank_sum / num_customers)

        # 计算每个节点新的PageRank score
        for customer in all_customers:
            # 计算随机跳转带来的PageRank
            pagerank_from_teleport = (1 - damping_factor) / num_customers

            # 计算从入链传递的PageRank
            pagerank_from_incoming_links = 0.0
            if customer in incoming_links_map:
                for incoming_customer, weight in incoming_links_map[customer].items():
                    pagerank_incoming_customer = pagerank_scores[incoming_customer]
                    weighted_out_incoming_customer = weighted_out_degrees.get(incoming_customer)
                    if weighted_out_incoming_customer > 0: # 为了防止权重为0的边导致div0错误
                        pagerank_from_incoming_links += (pagerank_incoming_customer * weight) / weighted_out_incoming_customer
        
            # 合并所有的PageRank Score
            new_pagerank_scores[customer] = pagerank_from_teleport + (damping_factor * pagerank_from_incoming_links) + pagerank_from_dangling_nodes
        
        # 检查是否收敛
        for customer in all_customers:
            total_change += abs(new_pagerank_scores[customer] - pagerank_scores[customer])
        
        pagerank_scores = new_pagerank_scores

        if total_change < epsilon:
            break
    
    return pagerank_scores


# --------------------- 影响客户分析 ---------------------
def _dfs_explore_influence(graph: CustomerGraph,
                           original_node: str,
                           the_first_node: str,
                           min_influence: float,
                           influenced_set: set):
    """
    DFS寻找影响力的传播路径, 使用Stack来迭代搜索, 不设返回值，通过传入的`influenced_set`记录搜索路径

    参数:
        graph (CustomerGraph): `CustomerGraph`对象
        original_node (str): 记录每次调用dfs时的起始节点
        the_first_node (str): 记录起始节点后一个节点
        min_influence (float): 影响力阈值，当两节点间影响力小于该阈值，就停止搜索
        influenced_set (set): 作为传入的可变对象，记录探索到的节点
    
    返回:
        None
    """

    # 初始化搜索栈，栈内每个元素均为三元组，包含当前节点，路径影响力和节点路径集合
    initial_edge_weight = graph.get_influence_weight(original_node, the_first_node)

    initial_path_nodes = {original_node, the_first_node}
    
    stack = [(the_first_node, initial_edge_weight, initial_path_nodes)]
    
    while stack:
        current_node, current_path_influence, current_path = stack.pop()
        next_nodes = graph.get_direct_influencees(current_node)

        for next_node, weight in next_nodes.items():
            if next_node in current_path: # 如果形成环，跳过
                continue

            new_path_influence = current_path_influence * weight

            if new_path_influence >= min_influence:
                if next_node != original_node:
                    influenced_set.add(next_node)
                
                next_path = current_path.copy()
                next_path.add(next_node)

                stack.append((next_node, new_path_influence, next_path))


def _calculate_influenced_nodes_for_single_customer(graph: CustomerGraph,
                                                    start_node: str,
                                                    min_influence: float) -> set:
    """
    寻找某个customer能影响的节点，当影响力过小的时候，对节点进行剪枝

    参数:
        graph (CustomerGraph): `CustomerGraph`对象
        start_node (str): 目标节点
        min_influence (float): 影响力阈值，当两节点间影响力小于该阈值，就剪枝
    
    返回:
        set: {被影响的节点}
    """
    if not isinstance(graph, CustomerGraph):
        raise TypeError("输入图必须是 CustomerGraph 对象")
    if not isinstance(start_node, str) or start_node not in graph.get_all_customers():
        raise ValueError(f"起始节点 '{start_node}' 无效或不在图中")
    if not isinstance(min_influence, (int, float)) or min_influence < 0 or min_influence > 1:
        raise ValueError("min_influence 必须属于0和1之间")
    
    influenced_nodes = set()
    next_nodes = graph.get_direct_influencees(start_node)

    for next_node, weight in next_nodes.items():
        if weight >= min_influence and next_node != start_node:
            influenced_nodes.add(next_node)

            _dfs_explore_influence(graph, start_node, next_node, min_influence, influenced_nodes)
    
    return influenced_nodes

def analyze_all_customer_influence_nodes(graph: CustomerGraph, min_influence: float) -> dict:
    """
    分析图中每一位客户能影响到的其他客户，如果相距过远以至于他们之间的影响小于`min_influence`，即不计入影响范围

    参数:
        graph (CustomerGraph): `CustomerGraph`对象
        min_influence (float): 允许的最小路径影响力
    
    返回:
        dict: {客户名称 (str): 影响的节点: (set)}
    """
    if not isinstance(graph, CustomerGraph):
        raise TypeError("输入图必须是 CustomerGraph 对象")
    if not isinstance(min_influence, (int, float)) or min_influence < 0 or min_influence > 1:
        raise ValueError("min_influence 必须属于0和1之间")

    all_influence_results = {}
    all_customers = graph.get_all_customers()

    if not all_customers:
        return {}
    
    for customer in all_customers:
        try:
            influence_set = _calculate_influenced_nodes_for_single_customer(graph, customer, min_influence)
            all_influence_results[customer] = influence_set
        except ValueError as e:
            print(f"分析客户'{customer}'时出错: {e}")
            all_influence_results[customer] = set()

    return all_influence_results



