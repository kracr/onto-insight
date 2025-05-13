from rdflib import URIRef

from verbalizer.patterns import Pattern
from verbalizer.verbalizer import VerbalizationNode, VerbalizationEdge
from verbalizer.vocabulary import Vocabulary


class OwlDisjointWith(Pattern):
    """
    Pattern that handles multiple class disjoints in OWL. It works by combining disjoints of the same object into a
    "collection". This results in having one statement for all disjoints.
    """
    disjoint_relation = 'http://www.w3.org/2002/07/owl#disjointWith'

    def check(self, results) -> bool:
        return self.disjoint_relation in {relation.toPython() for (relation, obj) in results}

    def normalize(self, node: VerbalizationNode, triple_collector):

        # Separate results into two groups: 1) related to disjointness, 2) all other
        query = self.verbalizer.next_step_query_builder(node)
        query_results = self._graph.query(query)

        # create intermediate node
        intermediate_node = VerbalizationNode(
            '_', parent_path=node.get_parent_path() + [(node.concept, URIRef(self.disjoint_relation))]
        )
        intermediate_node.display = ''
        intermediate_edge = VerbalizationEdge(URIRef(self.disjoint_relation), intermediate_node)
        intermediate_edge.display = self.vocab.get_relationship_label(self.disjoint_relation)
        node.add_edge(intermediate_edge)
        for (relation, obj) in query_results:
            if relation != URIRef(self.disjoint_relation):
                continue
            next_node = VerbalizationNode(obj, parent_path=node.get_parent_path() + [(node.concept, relation)])
            next_node.display = self.vocab.get_class_label(obj)
            edge = VerbalizationEdge(URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#collection'), next_node)
            edge.display = '#collection'
            intermediate_node.add_edge(edge)
            triple_collector.append((node.concept, relation, obj))

        # take care of non-disjoint relationships. This basically works the same way as without a pattern.
        for (relation, obj) in query_results:
            if relation == URIRef(self.disjoint_relation):
                continue
            relation_display = self.vocab.get_relationship_label(relation)

            if relation_display == Vocabulary.IGNORE_VALUE:
                if self.vocab.should_keep(relation):
                    triple_collector.append((node.concept, relation, obj))
                continue

            next_node = VerbalizationNode(obj, parent_path=node.get_parent_path() + [(node.concept, relation)])
            edge = VerbalizationEdge(relation, next_node)
            node.add_edge(edge)
            edge.display = relation_display
            triple_collector.append((node.concept, relation, obj))

        return [(reference.relationship, reference.node.concept) for reference in node.references]

    @classmethod
    def guarded_iris(cls) -> set[str]:
        return {cls.disjoint_relation}
