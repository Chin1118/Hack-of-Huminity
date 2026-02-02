from typing import List, Dict

def init_pheromone_matrix(drivers: List, tasks: List, init_value: float = 1.0) -> Dict[str, Dict[str, float]]:
    """
    Pheromone matrix initialization

    Args:
        drivers: List of Driver objects
        tasks: List of Task objects
        init_value: Initial pheromone value, default 1.0
    
    Returns:
        Pheromone matrix dictionary, formatted as {start node: {end node: pheromone value}}
    
    Node naming:
    - D_<driver_id>       : Driver's starting point
    - T_<task_id>         : Pick up point
    - T_<task_id>_D       : Drop off point
    """
    nodes = []
    
    #Add driver nodes
    for driver in drivers:
        node_id = f"D_{driver.id}"
        nodes.append(node_id)
    
    #Add task nodes
    for task in tasks:
        pickup_node = f"T_{task.id}"      
        dropoff_node = f"T_{task.id}_D"   
        nodes.append(pickup_node)
        nodes.append(dropoff_node)
    
    #Initialize pheromone matrix
    tau = {}
    for i in nodes:
        tau[i] = {}
        for j in nodes:
            if i != j:  #if start nodes not equal to end nodes, no self-loops
                tau[i][j] = init_value
    
    return tau

#for ACO
def get_pheromone_value(tau: Dict[str, Dict[str, float]], 
                        from_node: str, 
                        to_node: str, 
                        default: float = 0.0) -> float:
    """
    Obtain pheromone values safely
    """
    if from_node in tau and to_node in tau[from_node]:
        return tau[from_node][to_node]
    return default

def update_pheromone_matrix(tau: Dict[str, Dict[str, float]], 
                           evaporation_rate: float = 0.1):
    """
    Pheromones evaporate (in preparation for subsequent algorithms)
    """
    for i in tau:
        for j in tau[i]:
            tau[i][j] *= (1.0 - evaporation_rate)
    return tau