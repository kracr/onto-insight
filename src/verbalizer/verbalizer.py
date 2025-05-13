import dataclasses
import re
import typing
from collections import Counter
from dataclasses import dataclass
from typing import Type

from rdflib import Graph
from rdflib import RDFS, RDF, OWL
from rdflib import URIRef, Literal, BNode
from rdflib.term import Node

from verbalizer.nlp import ParaphraseLanguageModel
from verbalizer.patterns import Pattern
from verbalizer.vocabulary import Vocabulary

_RE_COMBINE_WHITESPACE = re.compile(r"\s+")

default_patterns = []


class VerbalizationError(Exception):
    pass


class VerbalizationInitError(Exception):
    pass


class VerbalizationEdge:

    def __init__(self, relationship, node: 'VerbalizationNode'):
        self.relationship = relationship
        self.node = node
        self._display = None

    @property
    def display(self):
        """
        Get the edge display (relationship label)
        """
        return self._display

    @display.setter
    def display(self, value):
        """
        Set the edge display. Can be set only if not set already. Otherwise the value is ignored.
        :param value: The value.
        """
        if not self._display:
            self._display = value

    def __repr__(self):
        return self.display

    def verbalize(self) -> str:
        """
        Traverse the edge to the next node to perform verbalization. This is a recursive operation.
        :return The verbalized text.
        """
        display = self.display

        if not isinstance(display, str):
            display = ''

        if display.startswith('#'):
            display = ''

        node = self.node.verbalize().strip()
        if node:
            next_text = f' {node}'
        else:
            next_text = ''

        return f'{display}{next_text}'


class VerbalizationNode:
    def __init__(self, concept, parent_path=None):
        self.concept = concept
        if parent_path is None:
            self._true_path = [(concept, None)]
        else:
            self._true_path = parent_path + [(concept, None)]
        self.references: list[VerbalizationEdge] = []
        self._display = None

    def add_edge(self, edge: VerbalizationEdge):
        """
        Add a new edge to the node.
        :param edge: New edge.
        """
        self.references.append(edge)

    def get_path(self):
        """
        Get the full path including the current node.
        :return: List of tuple (URIRef, URIRef)
        """
        return list(self._true_path)

    def get_parent_path(self):
        """
        Get the full path excluding the current node.
        :return: List of tuple (URIRef, URIRef)
        """
        return list(self._true_path[:-1])

    def get_next_node(self, relationship, concept):
        for reference in self.references:
            if reference.relationship == relationship and reference.node.concept == concept:
                return reference.node
        return None

    @property
    def display(self):
        """
        Get the node display (concept label)
        """
        return self._display

    @display.setter
    def display(self, value):
        """
        Set the node display. Can be set only if not set already. Otherwise the value is ignored.
        :param value: The value.
        """
        if self._display is None:
            self._display = value

    def __repr__(self):
        return self.display

    def verbalize(self) -> str:
        """
        Traverse the node to the next node via the edges to perform verbalization. This is a recursive operation.
        :return The verbalized text.
        """
        # Resolve sentences from edges
        sentences = [edge.verbalize().strip() for edge in self.references]

        display = self.display

        # For Blank Nodes, remove the display.
        if isinstance(self.concept, BNode):
            display = ''

        # Group multiple sentences together using `and`.
        if len(sentences) >= 2:
            next_text = f' ({", and ".join(sentences)})'
        elif len(sentences) == 1:
            next_text = f' {sentences[0]}'
        else:
            next_text = ''

        # Add indefinite articles
        if not isinstance(display, str) or not display:
            indefinite_article = ''
        elif display[0] in {'a', 'e', 'i', 'o', 'u'}:
            indefinite_article = 'an '
        else:
            indefinite_article = 'a '

        return f'{indefinite_article}{display}{next_text}'


@dataclass
class VerbalizerModelUsageConfig:
    """
    Object used to configure when and how LLM shall be used.
    """
    min_patterns_evaluated: int = 0
    min_statements: int = 1
    extra_context: str = ""


@dataclass
class VerbalizerInstanceStats:
    """
    Object used to collect statistics.
    """
    patterns_evaluated = 0
    statements = 0
    relationship_counter: Counter = dataclasses.field(default_factory=Counter)
    concepts: set = dataclasses.field(default_factory=set)


class Verbalizer:
    prefix = 'https://zaitoun.dev/onto/'

    def __init__(
            self,
            vocabulary: Vocabulary,
            patterns: list[Type[Pattern]] = None,
            language_model: ParaphraseLanguageModel = None,
            usage_config: VerbalizerModelUsageConfig = None
    ):
        self.graph = vocabulary.graph
        self.vocab = vocabulary
        self.llm = language_model
        self.llm_config = usage_config or VerbalizerModelUsageConfig(0, 2, "")
        self.patterns = [pattern(self.graph, self, vocabulary) for pattern in patterns or default_patterns]
        self._check_conflicts()

    def verbalize(self, starting_concept: typing.Union[str, URIRef]) -> (str, str, str, VerbalizerInstanceStats):
        """
        Returns the Turtle fragment, CNL statement, LLM verbalized textual description, and stats.
        :param starting_concept: The URI of the concept to verbalize.
        :return: (fragment, CNL text, LLM text, stats)
        """
        sentences = set()
        triples = []
        stats = VerbalizerInstanceStats()

        if isinstance(starting_concept, str):
            starting_concept = URIRef(starting_concept)

        node = VerbalizationNode(starting_concept)
        self._verbalize_as_text_from(node, self.vocab, triples, stats)

        for ref in node.references:
            sentences.add(_RE_COMBINE_WHITESPACE.sub(" ", f'{node.display} {ref.verbalize().strip()}.').strip())

        text = '\n'.join(sorted(sentences))
        onto_fragment: str = self.generate_fragment(triples)

        # update stats
        for triple in triples:
            subject, predicate, obj = triple
            stats.relationship_counter[predicate] += 1

            if isinstance(subject, URIRef):
                stats.concepts.add(subject)

            if isinstance(obj, URIRef):
                stats.concepts.add(obj)

        stats.statements = len(sentences)

        # convert the pseudo text into proper English.
        use_llm = bool(self.llm and self._check_llm_usage_policy(stats))
        llm_text = None
        if use_llm:
            llm_text = self.llm.pseudo_to_text(text, extra=self.llm_config.extra_context)

        return onto_fragment, text, llm_text, stats

    def _verbalize_as_text_from(self,
                                node: VerbalizationNode,
                                vocab: Vocabulary,
                                triple_collector: list[tuple[Node, Node, Node]],
                                stats: VerbalizerInstanceStats):
        """
        Receives an input node which holds information about some concept. The node is then expanded into a tree-like
        graph by making queries against the knowledge base. Each time the function is called, the neighbours of the
        most recent nodes are queried and are used to expand the "graph". This results in an expanded node object which
        can then be used for verbalization by walking over all the different paths created.

        :param node: The starting node to verbalize from
        :param vocab: Used as a lookup vocabulary
        :param triple_collector: Used to collect triples
        :param stats: used to collect statistics
        :return: None
        """
        query = self.next_step_query_builder(node)
        results = self.graph.query(query)

        results_normalized = False
        required_iris = set()

        # check patterns
        for pattern in self.patterns:
            if not pattern.check(results):
                continue

            results = pattern.normalize(node, triple_collector)
            required_iris = pattern.guarded_iris()
            results_normalized = True
            stats.patterns_evaluated += 1
            break

        # set node display
        node.display = vocab.get_class_label(node.concept)

        for result in results:
            relation, obj_2 = result

            relation_display = vocab.get_relationship_label(relation)

            if str(relation) in required_iris and relation_display == Vocabulary.IGNORE_VALUE:
                raise VerbalizationError(f'Cannot perform verbalization because required IRI {relation} is ignored.')

            if relation_display == Vocabulary.IGNORE_VALUE:
                if self.vocab.should_keep(relation):
                    triple_collector.append((node.concept, relation, obj_2))
                continue

            if not results_normalized:
                # Continue to expand the graph
                next_node = VerbalizationNode(obj_2, parent_path=node.get_parent_path() + [(node.concept, relation)])
                edge = VerbalizationEdge(relation, next_node)
                node.add_edge(edge)
                edge.display = relation_display

                # collect triple
                triple_collector.append((node.concept, relation, next_node.concept))
            else:
                # we already built this part of the graph so we just need to fetch it out.
                next_node = node.get_next_node(relation, obj_2)

            if isinstance(obj_2, URIRef):
                obj_display_2 = vocab.get_class_label(obj_2)
            elif isinstance(obj_2, Literal):
                obj_display_2 = obj_2.toPython()
            elif isinstance(obj_2, BNode):
                self._verbalize_as_text_from(next_node, vocab, triple_collector, stats)
                continue
            else:
                obj_display_2 = None

            next_node.display = obj_display_2

    @classmethod
    def next_step_query_builder(cls, node: VerbalizationNode) -> str:
        """
        Given a list of RDF Nodes, where each node is somehow connected to the next node in the list,
        return a SPARQL query expression to get all the relationships of the last node.
        This is needed in order to traverse over Blank Nodes.

        Consider the following graph:
        A -[rel]-> B
        B -[rel]-> C
        B -[rel]-> D

        If the input is:
        A-[rel]->B (The path)
        Then the output is query that would return:
        B -[rel]-> C
        B -[rel]-> D
        """

        trail = node.get_path()
        expressions = []
        filters = []
        for i, (t, p) in enumerate(trail):
            is_last = i == len(trail) - 1
            ref = cls._get_reference_expression(t, index=i)
            if is_last:
                exp = f'{ref} ?p ?o'
            else:
                next_t, _ = trail[i + 1]
                next_ref = cls._get_reference_expression(next_t, index=i + 1)
                exp = f'{ref} <{p.toPython()}> {next_ref}'

            if isinstance(t, BNode):
                filters.append(f"filter(str(?o{i}) = '{t.toPython()}')")

            expressions.append(exp)

        query = f"SELECT ?p ?o WHERE {{ {' . '.join(expressions)} . {' '.join(filters)} }}"
        return query

    def generate_fragment(self, triples: list[tuple[Node, URIRef, Node]], add_labels=False) -> str:
        """
        Return a string that represents the triples as an ontology fragment in turtle format.
        """

        def display_to_uri(display: str) -> URIRef:
            if display.startswith('http'):
                return URIRef(display)
            identifier = re.sub('[^a-zA-Z0-9 \n]', ' ', display).lower().replace(' ', '_')
            return URIRef(self.prefix + identifier)

        g = Graph()
        g.bind(prefix='', namespace=self.prefix)
        for triple in triples:
            subject, predicate, obj = triple

            subject_node = subject
            predicate_node = predicate
            object_node = obj

            if isinstance(subject, URIRef):
                subject_vocab_rep = self.vocab.get_class_label(subject, default=subject.toPython())
                if subject_vocab_rep == Vocabulary.IGNORE_VALUE:
                    continue
                subject_node = display_to_uri(subject_vocab_rep)

            if isinstance(obj, URIRef) and not obj.toPython().startswith(str(OWL)):
                object_vocab_rep = self.vocab.get_class_label(obj, default=obj.toPython())
                if object_vocab_rep == Vocabulary.IGNORE_VALUE:
                    continue
                object_node = display_to_uri(object_vocab_rep)

            if not self._starts_with_one_of(predicate_node.toPython(), [OWL, RDF, RDFS]):
                label = self.vocab.get_relationship_label(predicate)
                if label == Vocabulary.IGNORE_VALUE:
                    continue
                predicate_node = display_to_uri(label)

            g.add((subject_node, predicate_node, object_node))

            # If subject or object have labels - add them as rdfs:label
            if add_labels:
                if isinstance(subject, URIRef) and self.vocab.get_class_label(subject):
                    g.add((subject_node, RDFS.label, Literal(self.vocab.get_class_label(subject))))

                if isinstance(obj, URIRef) and \
                        self.vocab.get_class_label(obj) and \
                        not obj.toPython().startswith(str(OWL)):
                    g.add((object_node, RDFS.label, Literal(self.vocab.get_class_label(obj))))

        fragment = g.serialize(format='turtle')
        return '\n'.join(fragment.split("\n")[1:])

    @staticmethod
    def _starts_with_one_of(val: str, items: list):
        """
        Helper function to check if list contains an element that starts with the provided value.
        :param val: The value to check.
        :param items: The list
        :return: True if at least one item begins with the provided string.
        """
        return any([val.startswith(str(e)) for e in items])

    def _check_llm_usage_policy(self, stats: VerbalizerInstanceStats) -> bool:
        """
        Helper function used to check if LLM should be invoked.
        :param stats: Stats collected.
        :return: True if met.
        """
        return all([
            stats.patterns_evaluated >= self.llm_config.min_patterns_evaluated,
            stats.statements >= self.llm_config.min_statements
        ])

    @classmethod
    def _get_reference_expression(cls, t: Node, index: int):
        """
        Util function, used to convert Node t to a queryable expression.
        """
        if isinstance(t, URIRef):
            return f'<{t.toPython()}>'
        if isinstance(t, BNode):
            return f'?o{index}'

        return None

    def _check_conflicts(self):
        """
        Check if vocabulary and patterns have any conflicts.
        """
        for pattern in self.patterns:
            for iri in pattern.guarded_iris():
                if not self.vocab.should_ignore(iri):
                    continue

                raise VerbalizationInitError(f'The IRI {iri} should not be ignored because it is used in a pattern.')
