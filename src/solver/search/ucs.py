from loguru import logger

from search_problem import SearchProblem

logger.info("Hello World")


class UniformCostSearch:
    """Uniform-Cost Search 

    Uniform-Cost Search is a graph search algorithm

    """    

    def __init__(self, problem: SearchProblem):
        """initialize Uniform-Cost Search

        Args:
            problem (SearchProblem): _description_
        """        
        self.problem = problem
        logger.info("Uniform-Cost Search Initialized")
