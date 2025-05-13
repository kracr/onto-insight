from rdflib import URIRef

from verbalizer.patterns import Pattern
from verbalizer.verbalizer import VerbalizationNode, VerbalizationEdge


class OwlRestrictionPattern(Pattern):
    """
    Pattern that handles restrictions
    """

    def check(self, results) -> bool:
        expected = {
            'http://www.w3.org/2002/07/owl#onProperty',
            'http://www.w3.org/2002/07/owl#someValuesFrom',
            'http://www.w3.org/2002/07/owl#allValuesFrom',
            'http://www.w3.org/2002/07/owl#hasValue',
            'http://www.w3.org/2002/07/owl#cardinality',
            'http://www.w3.org/2002/07/owl#minCardinality',
            'http://www.w3.org/2002/07/owl#maxCardinality',
            'http://www.w3.org/2002/07/owl#qualifiedCardinality',
            'http://www.w3.org/2002/07/owl#minQualifiedCardinality',
            'http://www.w3.org/2002/07/owl#maxQualifiedCardinality',
            'http://www.w3.org/2002/07/owl#onClass'
        }
        actual = {relation.toPython() for (relation, obj) in results}

        return len(expected.intersection(actual)) >= 2

    def normalize(self, node: VerbalizationNode, triple_collector):
        query = self.verbalizer.next_step_query_builder(node)
        results = self._graph.query(query)

        next_node = None
        quantifier_relation = None
        property_relation = None
        literal_value = None
        on_class = None

        for (relation, obj) in results:

            if self.vocab.should_ignore(relation.toPython()):
                triple_collector.append((node.concept, relation, obj))
                continue

            if relation.toPython() == 'http://www.w3.org/2002/07/owl#onProperty':
                property_relation = obj

            if relation.toPython() in {'http://www.w3.org/2002/07/owl#someValuesFrom',
                                       'http://www.w3.org/2002/07/owl#allValuesFrom',
                                       'http://www.w3.org/2002/07/owl#hasValue'}:
                quantifier_relation = relation
                next_node = VerbalizationNode(concept=obj,
                                              parent_path=node.get_parent_path() + [(node.concept, relation)])

            if relation.toPython() in {'http://www.w3.org/2002/07/owl#cardinality',
                                       'http://www.w3.org/2002/07/owl#minCardinality',
                                       'http://www.w3.org/2002/07/owl#maxCardinality',
                                       'http://www.w3.org/2002/07/owl#qualifiedCardinality',
                                       'http://www.w3.org/2002/07/owl#minQualifiedCardinality',
                                       'http://www.w3.org/2002/07/owl#maxQualifiedCardinality'
                                       }:
                quantifier_relation = relation
                literal_value = obj

                # initialize next_node only if it hasn't been initialized yet.
                if next_node is None:
                    next_node = VerbalizationNode(
                        concept='',
                        parent_path=node.get_parent_path() + [(node.concept, relation)]
                    )
                    next_node.display = ''

            if relation.toPython() in {
                'http://www.w3.org/2002/07/owl#onClass'
            }:
                on_class = obj
                next_node = VerbalizationNode(
                    concept=obj,
                    parent_path=node.get_parent_path() + [(node.concept, relation)]
                )
                next_node.display = ''

            triple_collector.append((node.concept, relation, obj))

        edge = VerbalizationEdge(
            relationship=URIRef(quantifier_relation.toPython() + property_relation.toPython()),
            node=next_node
        )

        quantifier_relation_label = self.vocab.get_relationship_label(quantifier_relation)
        property_relation_label = self.vocab.get_class_label(property_relation)

        if quantifier_relation.toPython().endswith('someValuesFrom'):
            edge.display = f'at least {property_relation_label} some'
        elif quantifier_relation.toPython().endswith('allValuesFrom'):
            edge.display = f'only {property_relation_label}'
        elif quantifier_relation.toPython().endswith('hasValue'):
            edge.display = f'must {property_relation_label}'
        elif quantifier_relation.toPython().lower().endswith('cardinality'):
            edge.display = self._handle_cardinality(quantifier_relation, property_relation, literal_value, on_class)
        else:
            edge.display = f'{property_relation_label} {quantifier_relation_label}'

        node.add_edge(edge)

        return [(reference.relationship, reference.node.concept) for reference in node.references]

    def _handle_cardinality(self, quantifier_relation, property_relation, obj_literal, on_class) -> str:
        property_relation_label = self.vocab.get_class_label(property_relation)
        literal_value = obj_literal.toPython()
        on_class_label = ' '

        relation_plural_s = 's' if literal_value > 1 and not property_relation_label.endswith('s') else ''

        if property_relation_label.startswith('has'):
            property_relation_label = property_relation_label.replace('has ', '')

        if on_class:
            on_class_label = f' {self.vocab.get_class_label(on_class)} '

        if quantifier_relation.endswith('cardinality') and literal_value == 0:
            return f'has zero {on_class_label} {property_relation_label}s'
        elif quantifier_relation.endswith('cardinality') or quantifier_relation.endswith('qualifiedCardinality'):
            return f'has exactly {literal_value}{on_class_label}{property_relation_label}{relation_plural_s}'
        elif quantifier_relation.endswith('minCardinality') or quantifier_relation.endswith('minQualifiedCardinality'):
            return f'has at least {literal_value}{on_class_label}{property_relation_label}{relation_plural_s}'
        elif quantifier_relation.endswith('maxCardinality') or quantifier_relation.endswith('maxQualifiedCardinality'):
            return f'has at most {literal_value}{on_class_label}{property_relation_label}{relation_plural_s}'

    @classmethod
    def guarded_iris(cls) -> set[str]:
        return {
            'http://www.w3.org/2002/07/owl#someValuesFrom',
            'http://www.w3.org/2002/07/owl#allValuesFrom',
            'http://www.w3.org/2002/07/owl#hasValue',
            'http://www.w3.org/2002/07/owl#cardinality',
            'http://www.w3.org/2002/07/owl#minCardinality',
            'http://www.w3.org/2002/07/owl#maxCardinality',
            'http://www.w3.org/2002/07/owl#qualifiedCardinality',
            'http://www.w3.org/2002/07/owl#minQualifiedCardinality',
            'http://www.w3.org/2002/07/owl#maxQualifiedCardinality',
            'http://www.w3.org/2002/07/owl#onClass'
        }
