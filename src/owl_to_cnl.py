import logging
from pathlib import Path
from typing import Optional

from verbalizer.process import Processor
from verbalizer.vocabulary import Vocabulary
from verbalizer import Verbalizer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Standard URI configurations
IGNORE_URIS = {
    'http://www.w3.org/2002/07/owl#onDatatype',
    'http://www.w3.org/2000/01/rdf-schema#seeAlso',
    'http://www.w3.org/2000/01/rdf-schema#label',
    'http://www.w3.org/2000/01/rdf-schema#comment',
    'http://www.w3.org/1999/02/22-rdf-syntax-ns#type',
    'http://www.w3.org/2000/01/rdf-schema#isDefinedBy',
}

REPHRASE_URIS = {
    'http://www.w3.org/2002/07/owl#equivalentClass': 'is same as',
    'http://www.w3.org/2000/01/rdf-schema#subClassOf': 'is a type of',
    'http://www.w3.org/2002/07/owl#intersectionOf': 'all of',
    'http://www.w3.org/2002/07/owl#unionOf': 'any of',
    'http://www.w3.org/2002/07/owl#disjointWith': 'is different from',
    'http://www.w3.org/2002/07/owl#withRestrictions': 'must be'
}

def convert_owl_to_cnl(owl_file_path: str, output_file: Optional[str] = None) -> str:
    """
    Convert an OWL file to CNL and save it to a text file.
    
    Args:
        owl_file_path: Path to the input OWL file
        output_file: Optional path for the output text file. If not provided,
                    will use the same name as input file with .txt extension
    
    Returns:
        Path to the generated text file
    """
    if not Path(owl_file_path).exists():
        raise FileNotFoundError(f"OWL file not found: {owl_file_path}")
    
    if output_file is None:
        output_file = str(Path(owl_file_path).with_suffix('.txt'))
    
    logger.info(f"Loading ontology from {owl_file_path}")
    ontology = Processor.from_file(owl_file_path)
    
    vocab = Vocabulary(ontology, ignore=IGNORE_URIS, rephrased=REPHRASE_URIS)
    verbalizer = Verbalizer(vocab)
    
    classes = Processor._get_classes(ontology)
    individuals = Processor._get_individuals(ontology)
    
    logger.info(f"Found {len(classes)} classes and {len(individuals)} individuals")
    
    all_statements = []
    total_concepts = len(classes) + len(individuals)
    
    logger.info("Converting to CNL...")
    for i, concept in enumerate(classes + individuals, 1):
        _, cnl_text, _, stats = verbalizer.verbalize(concept)
        
        if stats.statements > 0:
            all_statements.append(cnl_text)
        
        if i % 100 == 0:
            logger.info(f"Processed {i}/{total_concepts} concepts")
    
    logger.info(f"Writing CNL to {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(all_statements))
    
    logger.info("Conversion completed successfully")
    return output_file

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python owl_to_cnl.py <path_to_owl_file>")
        sys.exit(1)
    
    try:
        output_file = convert_owl_to_cnl(sys.argv[1])
        print(f"CNL text has been saved to: {output_file}")
    except Exception as e:
        logger.error(f"Error during conversion: {str(e)}")
        sys.exit(1)