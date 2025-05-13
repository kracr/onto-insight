import datetime
import logging
from pathlib import Path
from typing import Optional
from xml.sax import SAXParseException

import pandas
from rdflib import Graph, URIRef
from tqdm import tqdm

from verbalizer.nlp import ParaphraseLanguageModel
from verbalizer.sampler import Sampler
from verbalizer.verbalizer import Verbalizer

logger = logging.getLogger(__name__)


class Processor:
    """
    The processor that starts the verbalization process and outputs the results.
    """

    @classmethod
    def verbalize_with(cls,
                       verbalizer: Verbalizer,
                       *,
                       namespace: str,
                       output_dir: Optional[str] = None,
                       chunk_size: int = 1000,
                       sampler: Optional[Sampler] = None,
                       as_generator: bool = False):
        gen = cls.verbalize_with_stream(
            verbalizer,
            namespace=namespace,
            output_dir=output_dir,
            chunk_size=chunk_size,
            sampler=sampler,
            as_generator=as_generator
        )
        if as_generator:
            return gen

        return next(gen)

    @classmethod
    def verbalize_with_stream(
            cls,
            verbalizer: Verbalizer,
            *,
            namespace: str,
            output_dir: Optional[str] = None,
            chunk_size: int = 1000,
            sampler: Optional[Sampler] = None,
            as_generator: bool = False):
        """
        Start the verbalization process.
        :param verbalizer: The verbalizer to use.
        :param namespace: Name of the directory to create under the output directory.
        :param output_dir: Name of the output directory.
        :param chunk_size: Number of entries (rows) per file. default = 1000
        :param sampler: A sampling configuration, use to sample large ontologies.
        :param as_generator: If True, returns a generator instead of a list.
        """

        # current timestamp
        now = datetime.datetime.now(datetime.UTC)
        timestamp = int(now.timestamp())
        llm: ParaphraseLanguageModel = verbalizer.llm

        # make output directory
        if output_dir:
            if llm:
                out = f'{output_dir}/{namespace}/{llm.name}/{timestamp}'
            else:
                out = f'{output_dir}/{namespace}/{timestamp}'
        else:
            out = None

        classes = cls._get_classes(verbalizer.graph)
        individuals = cls._get_individuals(verbalizer.graph)

        if sampler := sampler:
            samples = sampler.get_sample({'classes': classes, 'individuals': individuals})
            classes, individuals = samples['classes'], samples['individuals']
        full_dataset = []
        chunk_dataset = []

        partition = 0
        for entry in tqdm(classes + individuals, desc='Verbalizing'):
            fragment, text, llm_text, stats = verbalizer.verbalize(entry)

            if stats.statements == 0:
                continue

            element = {
                'ontology': namespace,
                'root': entry,
                'fragment': fragment,
                'text': text,
                'llm_text': llm_text,
                'model': llm.name if llm else 'None',
                'statements': stats.statements,
                'unique_concepts': len(stats.concepts),
                'unique_relationships': len(stats.relationship_counter),
                'total_relationships': sum(stats.relationship_counter.values()),
                **stats.relationship_counter
            }

            chunk_dataset.append(element)

            if as_generator:
                yield element

            if len(chunk_dataset) != chunk_size:
                continue

            full_dataset.extend(chunk_dataset)

            if out:
                Path(out).mkdir(parents=True, exist_ok=True)
                pandas.DataFrame(chunk_dataset).to_csv(f'{out}/file_{partition}.csv', index=False)

            partition += 1
            chunk_dataset = []

        # handle leftovers
        if chunk_dataset:
            full_dataset.extend(chunk_dataset)
            if out:
                Path(out).mkdir(parents=True, exist_ok=True)
                pandas.DataFrame(chunk_dataset).to_csv(f'{out}/file_{partition}.csv', index=False)

        logger.info('Finished verbalizing')
        if llm:
            logger.info(f'LLM usage cost: ${llm.cost}')

        if not as_generator:
            yield full_dataset

    @staticmethod
    def _get_classes(graph):
        """
        Get all owl:Class and their labels.
        :param graph: The ontology.
        :return: A list of URIRef objects.
        """
        query = """
                SELECT ?o ?label
                WHERE {
                    ?o a owl:Class .
                    OPTIONAL {
                        ?o rdfs:label ?label
                    }
                    FILTER NOT EXISTS {
                        ?o owl:deprecated true
                    }
                }
            """
        return [result[0] for result in
                tqdm(graph.query(query), desc='Loading Classes') if isinstance(result[0], URIRef)]

    @staticmethod
    def _get_individuals(graph):
        """
        Get all owl:NamedIndividual and their labels.
        :param graph: The ontology.
        :return: A list of URIRef objects.
        """
        query = """
                        SELECT ?o ?label
                        WHERE {
                            ?o a owl:NamedIndividual .
                            OPTIONAL {
                                ?o rdfs:label ?label
                            }
                            FILTER NOT EXISTS {
                                ?o owl:deprecated true
                            }
                        }
                    """
        return [result[0] for result in
                tqdm(graph.query(query), desc='Loading Instances') if isinstance(result[0], URIRef)]

    @staticmethod
    def from_file(file_path: str) -> Graph:
        """
        Helper function to load graph from file.
        """
        graph = Graph()
        formats = ['xml', 'n3']
        logger.info(f'Loading File {file_path}')
        for file_format in formats:
            try:
                graph.parse(file_path, format=file_format)
                break
            except SAXParseException:
                pass
        logger.info(f'Done Loading.')
        return graph
