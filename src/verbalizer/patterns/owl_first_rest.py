from verbalizer.patterns import Pattern
from rdflib import URIRef

from verbalizer.verbalizer import VerbalizationNode, VerbalizationEdge


class OwlFirstRestPattern(Pattern):
    """
    Pattern that handles ordered lists (first-rest) in OWL.
    """

    def check(self, results) -> bool:
        expected = {'http://www.w3.org/1999/02/22-rdf-syntax-ns#first',
                    'http://www.w3.org/1999/02/22-rdf-syntax-ns#rest'}
        return {relation.toPython() for (relation, obj) in results} == expected

    def normalize(self, node: VerbalizationNode, triple_collector):
        current = node
        while current.concept != URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#nil'):
            query = self.verbalizer.next_step_query_builder(current)
            results = self._graph.query(query)
            rest_node = None
            for (relation, obj) in results:
                next_node = VerbalizationNode(
                    obj, parent_path=current.get_parent_path() + [(current.concept, relation)]
                )
                if relation == URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#first'):
                    # first
                    edge = VerbalizationEdge(URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#collection'), next_node)
                    node.add_edge(edge)
                    edge.display = '#collection'
                else:
                    # rest
                    rest_node = next_node
                triple_collector.append((current.concept, relation, obj))

            current = rest_node

        return [(reference.relationship, reference.node.concept) for reference in node.references]

    @classmethod
    def guarded_iris(cls) -> set[str]:
        return set()
