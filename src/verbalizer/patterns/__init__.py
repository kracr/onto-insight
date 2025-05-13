from abc import ABC, abstractmethod

from rdflib import Graph
from rdflib.term import Node

from verbalizer.vocabulary import Vocabulary


class Pattern(ABC):
    """
    A patterns is a class used to identify patterns within the graph based on all the out going relations from a
    specific concept.
    """

    def __init__(self, graph: Graph, verbalizer: 'Verbalizer', vocabulary: Vocabulary):
        self._graph = graph
        self.verbalizer = verbalizer
        self.vocab = vocabulary

    @abstractmethod
    def check(self, results) -> bool:
        """
        The check function is used to determine whether a patterns was detected or not. The "results" argument
        includes the first-degree related objects to the subject. If more triples are needed to be fetched to
        identify the patterns, self.graph.query can be used.
        """
        return False

    @abstractmethod
    def normalize(self, node: 'VerbalizationNode', triple_collector) -> list[tuple[Node, Node]]:
        """
        The normalize function is called only if the check returned True. It is used to simplify the patterns. This
        means that the patterns must re-arrange the connected nodes in an order that would be different from the
        regular order. In addition to that, the implementation must also collect all the RDF triples observed
        regardless of whether they were used or not in the construction of the nodes and edges.
        """
        return []

    @classmethod
    def guarded_iris(cls) -> set[str]:
        return set()
