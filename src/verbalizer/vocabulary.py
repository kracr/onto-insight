import re
import logging
from rdflib import URIRef, Graph
from tqdm import tqdm

logger = logging.getLogger(__name__)


class Vocabulary:
    """
    Vocabulary class, used as a URI to term lookup.
    """

    IGNORE_VALUE = object()

    RELATIONSHIP_QUERY = """
    SELECT DISTINCT ?p ?relation
    WHERE {
        ?o1 ?p ?o2 .
        OPTIONAL {
            ?p rdfs:label ?pLabel
        }
        BIND (
          COALESCE(
            ?pLabel,
            ?p
          ) AS ?relation
        )
    }
    """

    OBJECTS_QUERY = """
    SELECT DISTINCT ?o1 ?o1Label
    WHERE {
        {
            SELECT ?o1 ?o1Label WHERE {
                ?o1 ?p ?o2 .
                ?o1 rdfs:label ?o1Label
            }
        }
        UNION
        {
            SELECT ?o1 ?o1Label WHERE {
                ?o1 a owl:Class .
                OPTIONAL {
                    ?o1 rdfs:label ?optionalLabel
                }
                BIND (
                  COALESCE(
                    ?optionalLabel,
                    ?o1
                  ) AS ?o1Label
                )
            }
        }    
    }
    """

    def __init__(self, graph: Graph, ignore: set[str] = None, guard: set[str] = None, rephrased: dict[str, str] = None):
        """
        :param graph: The ontology.
        :param ignore: URIs to ignore.
        :param guard: URIs to keep in the fragment even if they are in the ignore list.
        :param rephrased: URIs to rephrase/rename
        """
        logger.info('Initializing vocabulary')
        self.graph = graph
        self.relationship_labels = self._get_ontology_relationship_labels()
        self.object_labels = self._get_ontology_object_labels()
        self._load_imports()
        self.rephrased = rephrased or dict()
        self._ignore_list = ignore or {}
        self._guard_list = guard or {
            'http://www.w3.org/1999/02/22-rdf-syntax-ns#type',
            'http://www.w3.org/2000/01/rdf-schema#label',
            'http://www.w3.org/2002/07/owl#onDatatype'
        }

    def should_ignore(self, uri: str | URIRef) -> bool:
        """
        Check if URI should be ignored or not.
        """
        if isinstance(uri, URIRef):
            uri = uri.toPython()
        return uri in self._ignore_list

    def should_keep(self, uri: str | URIRef) -> bool:
        """
        Check if URI should be kept in the fragment or not.
        """
        if isinstance(uri, URIRef):
            uri = uri.toPython()
        return uri in self._guard_list

    def get_relationship_label(self, val, default=None) -> str:
        """
        Get relationship label.
        :param val: The URI to lookup with.
        :param default: Default value if not found.
        :return: string.
        """
        return self._util_lookup(self.relationship_labels, val) or default

    def get_class_label(self, val, default=None) -> str:
        """
        Get class label.
        :param val: The URI to lookup with.
        :param default: Default value if not found.
        :return: string.
        """
        return self._util_lookup(self.object_labels, val) or default

    def _get_ontology_relationship_labels(self) -> dict[str, str]:
        """
        Returns a IRI (URI) to label dictionary.
        """
        results = self.graph.query(self.RELATIONSHIP_QUERY)
        ontology_relations = {}

        for result in tqdm(results, desc='Loading Ontology Relationship Labels'):
            iri, label = result
            iri_str = iri.toPython()
            label_str = label.toPython()

            # if the label is also the URI then try to parse it.
            if label_str.startswith('http'):
                label_str = self._from_uri_to_text(label_str)

            label_str = re.sub('[^0-9a-zA-Z]+', ' ', label_str)

            ontology_relations[iri_str] = label_str

        return ontology_relations

    def _get_ontology_object_labels(self) -> dict[str, str]:
        """
        Returns a IRI (URI) to label dictionary.
        """
        results = self.graph.query(self.OBJECTS_QUERY)
        object_labels = {}
        for result in tqdm(results, desc='Loading Ontology Object Labels'):
            iri, label = result
            iri_str = iri.toPython()
            label_str = label.toPython()

            if iri_str == label_str and not label_str.startswith('http'):
                # skip BNodes
                continue

            # if the label is also the URI then try to parse it.
            if label_str.startswith('http'):
                label_str = self._from_uri_to_text(label_str)
            # Convert label to lower case snake case and remove spaces.
            label_str = self._camel_to_snake(label_str)
            label_str = re.sub('[^0-9a-zA-Z]+', ' ', label_str)

            object_labels[iri_str] = label_str

        return object_labels

    def _util_lookup(self, dictionary, val):
        """
        Helper function used to perform lookup in a given dictionary using a key.

        If the value is found, it is returned.
        If the value is in the ignore list, a `IGNORE_VALUE` object is returned.
        If a rephrase configuration is set of the key, it is returned.
        If not found, text extraction is attempt from the key URI.

        :param dictionary: The dictionary to look in.
        :param val: The key to lookup with.
        :return: The value.
        """
        if isinstance(val, URIRef):
            val = val.toPython()

        if not isinstance(val, str):
            return None

        if val in self._ignore_list:
            return self.__class__.IGNORE_VALUE

        # try get from overrides first
        if result := self.rephrased.get(val):
            return result

        result = dictionary.get(val)
        if result:
            return result

        # result is none, try to verbalize from URI
        return self._from_uri_to_text(val)

    def _from_uri_to_text(self, uri: str):
        """
        Attempt to extract phrases from the URI by taking the suffix and converting it into snake-case.
        """
        if '#' in uri:
            text = uri.split('#')[1]
        else:
            text = uri.split('/')[-1]

        # convert underscore or camel case notation into regular text
        text = self._camel_to_snake(text)
        return text.replace('_', ' ')

    @staticmethod
    def _camel_to_snake(name):
        """
        Convert camelCase into snake_case.
        e.g. MyPhrase -> my_phrase
        """
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

    def _load_imports(self):
        """
        Loads concepts from imports. This is done by creating a new instance of Vocabulary, using the imported graph.
        """
        owl_imports = {o[0].toPython() for o in self.graph.query("SELECT DISTINCT ?o WHERE { ?s owl:imports ?o }")}
        for owl_import in owl_imports:
            logging.info(f'LOADING IMPORT: {owl_import}')
            graph = Graph()
            graph.parse(owl_import, format='xml')
            sub_vocab = self.__class__(graph)
            self.object_labels.update(sub_vocab.object_labels)
            self.relationship_labels.update(sub_vocab.relationship_labels)
