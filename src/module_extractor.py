#!/usr/bin/env python3
import os
import json
import logging
import subprocess
import pandas as pd
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class OntologyModuleExtractor:
    def __init__(self, metrics_ranges_csv: str = "metrics/oquare_metrics.csv"):
        """Initialize the module extractor."""
        self.metrics_ranges = self._load_metrics_ranges(metrics_ranges_csv)
        
    def _load_metrics_ranges(self, csv_path: str) -> pd.DataFrame:
        """Load metrics ranges from CSV file."""
        try:
            metrics_ranges = pd.read_csv(csv_path)
            logger.info(f"Loaded metrics ranges for {len(metrics_ranges)} metrics")
            return metrics_ranges
        except Exception as e:
            logger.error(f"Error loading metrics ranges: {e}")
            # Create a minimal backup DataFrame
            return pd.DataFrame(columns=['Metric', '1 (Worst)', '5 (Best)'])

    def _identify_worst_metrics(self, metrics: Dict[str, float]) -> List[Tuple[str, float]]:
        """
        Identify the worst metrics based on their OQuaRE ranges.
        Returns a list of tuples (metric_name, score) sorted by severity (worst first).
        """
        worst_metrics = []
        
        # For each metric, check if it falls in the worst category
        for metric_name, score in metrics.items():
            # Skip non-metrics
            if metric_name in ['name', 'timestamp']:
                continue
                
            # Check if metric is in our ranges CSV
            metric_with_onto = metric_name
            if not metric_name.endswith('Onto'):
                metric_with_onto = f"{metric_name}Onto"
                
            # Find the row for this metric in the ranges DataFrame
            metric_row = self.metrics_ranges[self.metrics_ranges['Metric'] == metric_with_onto]
            
            if metric_row.empty:
                # Try with the original name
                metric_row = self.metrics_ranges[self.metrics_ranges['Metric'] == metric_name]
                
            if not metric_row.empty:
                worst_range = metric_row['1 (Worst)'].iloc[0]
                
                # Check if the score falls in the worst range
                is_worst = False
                if worst_range.startswith('<'):
                    # Format: "< 0.2"
                    threshold = float(worst_range.split()[1])
                    is_worst = score < threshold
                elif worst_range.startswith('>'):
                    # Format: "> 12" or ">0. 8" (with typo)
                    # Fix any typos in the CSV
                    cleaned = worst_range.replace('>0.', '> 0.').replace('>0 .', '> 0.')
                    threshold = float(cleaned.split()[1])
                    is_worst = score > threshold
                
                if is_worst:
                    worst_metrics.append((metric_name, score))
        
        # Sort worst metrics by severity (worst first)
        return sorted(worst_metrics, key=lambda x: x[1] if x[0].startswith('AN') or x[0].startswith('AR') else -x[1])

    def _get_metric_description(self, metric_name: str, framework_metrics_csv: str = "metrics/framework_metrics_descriptions.csv") -> str:
        """Get description for a metric from the framework metrics CSV."""
        try:
            metrics_df = pd.read_csv(framework_metrics_csv)
            
            # Try to match the metric name exactly or with/without Onto suffix
            search_name = metric_name
            metric_row = metrics_df[metrics_df['Metric_Name'] == search_name]
            
            if metric_row.empty and metric_name.endswith('Onto'):
                # Try without Onto suffix
                search_name = metric_name[:-4]
                metric_row = metrics_df[metrics_df['Metric_Name'] == search_name]
            elif metric_row.empty:
                # Try with Onto suffix
                search_name = f"{metric_name}Onto"
                metric_row = metrics_df[metrics_df['Metric_Name'] == search_name]
                
            if not metric_row.empty and 'Description' in metric_row:
                return metric_row['Description'].iloc[0]
            return "No description available"
        except Exception as e:
            logger.warning(f"Error getting metric description: {e}")
            return "No description available"

    def _get_metric_range_info(self, metric_name: str) -> str:
        """Get the range information for a metric from the ranges DataFrame."""
        try:
            metric_with_onto = metric_name
            if not metric_name.endswith('Onto'):
                metric_with_onto = f"{metric_name}Onto"
                
            # Find the row for this metric in the ranges DataFrame
            metric_row = self.metrics_ranges[self.metrics_ranges['Metric'] == metric_with_onto]
            
            if metric_row.empty:
                # Try with the original name
                metric_row = self.metrics_ranges[self.metrics_ranges['Metric'] == metric_name]
                
            if not metric_row.empty:
                worst = metric_row['1 (Worst)'].iloc[0] if '1 (Worst)' in metric_row else "Unknown"
                best = metric_row['5 (Best)'].iloc[0] if '5 (Best)' in metric_row else "Unknown"
                return f"Best range (5): {best}, Worst range (1): {worst}"
            return "Range information not available"
        except Exception as e:
            logger.warning(f"Error getting metric range info: {e}")
            return "Range information not available"

    def select_worst_metric_for_module(self, metrics_data_path: str, auto_select: bool = False) -> Tuple[str, List[str]]:
        """
        Display the worst metrics and let user select which one to use for creating a module.
        If auto_select is True, automatically selects the worst metric without user interaction.
        Returns the selected metric name and its associated seed terms.
        """
        try:
            # Load metrics data
            with open(metrics_data_path, 'r') as f:
                metrics_data = json.load(f)
            
            metrics = metrics_data.get('metrics', {})
            
            # Identify worst metrics
            worst_metrics = self._identify_worst_metrics(metrics)
            
            # Ensure we have at least some metrics to show
            if not worst_metrics:
                logger.warning("No worst metrics found. Using lowest scoring metrics instead.")
                # Just use the lowest scoring metrics
                metrics_list = [(k, v) for k, v in metrics.items() if k not in ['name', 'timestamp']]
                worst_metrics = sorted(metrics_list, key=lambda x: x[1])[:5]
            
            # Get the top 3 worst metrics (or all if fewer than 3)
            display_metrics = worst_metrics[:min(3, len(worst_metrics))]
            
            # Check if we should auto-select or if stdin is not available (non-interactive mode)
            is_interactive = auto_select == False and sys.stdin.isatty()
            
            if is_interactive:
                print("\n===================================================")
                print("=== TOP 3 WORST PERFORMING METRICS FOR MODULE =====")
                print("===================================================")
                
                for i, (metric, score) in enumerate(display_metrics, 1):
                    description = self._get_metric_description(metric)
                    range_info = self._get_metric_range_info(metric)
                    
                    print(f"\n{i}. {metric}: {score}")
                    print(f"   - Description: {description[:100]}...")
                    print(f"   - {range_info}")
                    
                print("\n===================================================")
                print("Select a metric to use for module extraction (1-3):")
                print("Or press Enter to use the worst metric (option 1)")
                
                selection = input("> ").strip()
                
                # Default to the worst metric if no selection is made
                if not selection:
                    selected_index = 0
                    logger.info(f"No selection made. Using worst metric: {display_metrics[0][0]}")
                else:
                    try:
                        selected_index = int(selection) - 1
                        if selected_index < 0 or selected_index >= len(display_metrics):
                            logger.warning(f"Invalid selection {selection}. Using worst metric.")
                            selected_index = 0
                    except ValueError:
                        logger.warning(f"Invalid input: {selection}. Using worst metric.")
                        selected_index = 0
            else:
                # Auto-select mode or non-interactive mode
                selected_index = 0
                logger.info(f"Auto-selecting worst metric: {display_metrics[0][0]}")
            
            selected_metric = display_metrics[selected_index][0]
            logger.info(f"Selected metric for module extraction: {selected_metric}")
            
            # Check if there are any tied metrics (metrics with the same score)
            tied_metrics = [m[0] for m in display_metrics if m[1] == display_metrics[selected_index][1]]
            if len(tied_metrics) > 1:
                logger.info(f"Found tied metrics with same score: {', '.join(tied_metrics)}")
                if is_interactive:
                    print(f"\nNote: There are {len(tied_metrics)} metrics with the same score.")
                    print(f"Will create modules for all tied metrics: {', '.join(tied_metrics)}")
                return "tied", tied_metrics
            
            return selected_metric, [selected_metric]
            
        except Exception as e:
            logger.error(f"Error selecting worst metric: {e}")
            if worst_metrics:
                # Fall back to the worst metric
                return worst_metrics[0][0], [worst_metrics[0][0]]
            return "error", []

    def get_seed_terms_from_json(self, seed_terms_json_path: str, metric_name: str) -> List[Dict]:
        """
        Extract seed terms for a specific metric from the seed terms JSON file.
        Returns a list of seed term dictionaries with 'term' and 'iri' keys.
        """
        try:
            with open(seed_terms_json_path, 'r') as f:
                seed_terms_json = json.load(f)
            
            if metric_name in seed_terms_json:
                return seed_terms_json[metric_name]
            
            # If no direct match, try with or without 'Onto' suffix
            if metric_name.endswith('Onto'):
                base_name = metric_name[:-4]
                if base_name in seed_terms_json:
                    return seed_terms_json[base_name]
            else:
                onto_name = f"{metric_name}Onto"
                if onto_name in seed_terms_json:
                    return seed_terms_json[onto_name]
            
            # Check if the metric name is part of any key
            for key in seed_terms_json.keys():
                if metric_name in key:
                    return seed_terms_json[key]
            
            logger.warning(f"No seed terms found for metric {metric_name}")
            return []
        except Exception as e:
            logger.error(f"Error getting seed terms from JSON: {e}")
            return []

    def _validate_iri(self, iri: str) -> bool:
        """
        Validate if an IRI is properly formatted.
        """
        # Basic validation: must start with http:// or https:// or urn:
        if not (iri.startswith('http://') or iri.startswith('https://') or iri.startswith('urn:')):
            return False
            
        # Must not contain spaces
        if ' ' in iri:
            return False
            
        return True

    def _fix_iri_formatting(self, iri: str) -> str:
        """
        Fix common IRI formatting issues.
        """
        # Remove surrounding quotes if present
        iri = iri.strip('"\'')
        
        # Ensure proper URI format
        if not (iri.startswith('http://') or iri.startswith('https://') or iri.startswith('urn:')):
            # If IRI uses CURIE format like "obo:GO_0005739"
            if ':' in iri and not iri.startswith('http'):
                prefix, local_id = iri.split(':', 1)
                prefix = prefix.lower()  # Convert prefix to lowercase
                
                # Map common prefixes to their base URIs
                prefix_map = {
                    'obo': 'http://purl.obolibrary.org/obo/',
                    'go': 'http://purl.obolibrary.org/obo/GO_',
                    'owl': 'http://www.w3.org/2002/07/owl#',
                    'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
                    'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
                    'xsd': 'http://www.w3.org/2001/XMLSchema#',
                    'dc': 'http://purl.org/dc/elements/1.1/',
                    'skos': 'http://www.w3.org/2004/02/skos/core#'
                }
                
                if prefix in prefix_map:
                    if prefix == 'obo' and '_' not in local_id:
                        # Handle obo format - add underscore if missing
                        parts = local_id.split(':', 1) if ':' in local_id else [local_id, '']
                        if len(parts) > 1:
                            local_id = f"{parts[0]}_{parts[1]}"
                            
                    iri = prefix_map[prefix] + local_id
                else:
                    # If unknown prefix, use a generic URI
                    iri = f"http://purl.org/ontology/{prefix}/{local_id}"
        
        return iri

    def create_ontology_module(self, ontology_path: str, output_dir: str, metric_name: str, 
                              seed_terms: List[Dict], method: str = "TOP") -> Optional[str]:
        """
        Create an ontology module using ROBOT with the specified method and seed terms.
        
        Args:
            ontology_path: Path to the ontology file
            output_dir: Directory to save the module
            metric_name: Metric name to use in the output file name
            seed_terms: List of seed term dictionaries with 'term' and 'iri' keys
            method: ROBOT extraction method (BOT, TOP, STAR, or MIREOT)
            
        Returns:
            Path to the created module or None if creation failed
        """
        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Get the base name from the original input file, not the converted one
            base_name = Path(ontology_path).stem
            if '_converted' in base_name:
                base_name = base_name.replace('_converted', '')
            module_path = os.path.join(output_dir, f"{base_name}_module.owl")
            
            # Check if we have seed terms with IRIs
            valid_seed_terms = []
            for term in seed_terms:
                if term.get('iri'):
                    # Fix any IRI formatting issues
                    fixed_iri = self._fix_iri_formatting(term['iri'])
                    if self._validate_iri(fixed_iri):
                        valid_seed_terms.append({"term": term.get('term'), "iri": fixed_iri})
            
            if not valid_seed_terms:
                logger.error(f"No valid seed terms with IRIs found for metric {metric_name}")
                
                # Fallback: Try to extract the ontology's top-level classes as seed terms
                logger.info("Attempting to use top-level classes as fallback seed terms")
                try:
                    # Create SPARQL query to get top-level classes
                    sparql_query_file = os.path.join(output_dir, "top_classes.sparql")
                    with open(sparql_query_file, 'w') as f:
                        f.write("""
                        PREFIX owl: <http://www.w3.org/2002/07/owl#>
                        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                        SELECT DISTINCT ?class WHERE {
                            ?class a owl:Class .
                            FILTER NOT EXISTS { ?class rdfs:subClassOf ?parent . 
                                               FILTER(?parent != owl:Thing && ?parent != ?class) }
                            FILTER(!isBlank(?class))
                            FILTER(?class != owl:Thing && ?class != owl:Nothing)
                        }
                        LIMIT 10
                        """)
                    
                    # Run query to get top-level classes
                    sparql_result_file = os.path.join(output_dir, "top_classes.json")
                    query_cmd = [
                        "robot", "query", "--input", ontology_path,
                        "--query", sparql_query_file, sparql_result_file
                    ]
                    result = subprocess.run(query_cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0 and os.path.exists(sparql_result_file):
                        with open(sparql_result_file, 'r') as f:
                            query_results = json.load(f)
                            
                        for binding in query_results.get('results', {}).get('bindings', []):
                            if 'class' in binding and binding['class'].get('value'):
                                class_iri = binding['class']['value']
                                if self._validate_iri(class_iri):
                                    valid_seed_terms.append({"term": Path(class_iri).name, "iri": class_iri})
                                    
                        logger.info(f"Found {len(valid_seed_terms)} top-level classes to use as seed terms")
                        
                        # Clean up temporary files
                        for temp_file in [sparql_query_file, sparql_result_file]:
                            if os.path.exists(temp_file):
                                os.remove(temp_file)
                    else:
                        logger.error("Failed to run SPARQL query for top-level classes")
                        
                except Exception as e:
                    logger.error(f"Error getting top-level classes: {e}")
                
                if not valid_seed_terms:
                    logger.error("No valid seed terms found, even after fallback attempt")
                    return None
            
            # Create temporary term file for ROBOT
            term_file_path = os.path.join(output_dir, f"{metric_name}_terms.txt")
            with open(term_file_path, 'w') as f:
                for term in valid_seed_terms:
                    if term.get('iri'):
                        f.write(f"{term['iri']}\n")
            
            logger.info(f"Running ROBOT extraction with {len(valid_seed_terms)} seed terms")
            
            # List the terms in the term file for debugging
            with open(term_file_path, 'r') as f:
                terms = f.read().strip().split('\n')
                logger.info(f"Terms in term file: {terms}")
            
            # Build ROBOT command with --force flag to prevent errors for terms not found
            robot_cmd = [
                "robot", "extract",
                "--input", ontology_path,
                "--method", method,
                "--term-file", term_file_path,
                "--force", "true",
                "--output", module_path
            ]
            
            logger.info(f"Command: {' '.join(robot_cmd)}")
            
            # Run ROBOT
            result = subprocess.run(robot_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"ROBOT extraction failed: {result.stderr}")
                
                # Try alternate approach with individual terms instead of term file
                logger.info("Trying alternate approach with individual terms...")
                alternate_cmd = ["robot", "extract", "--input", ontology_path, "--method", method]
                
                for term in valid_seed_terms:
                    if term.get('iri'):
                        alternate_cmd.extend(["--term", term['iri']])
                
                alternate_cmd.extend(["--force", "true", "--output", module_path])
                
                logger.info(f"Alternate command: {' '.join(alternate_cmd)}")
                
                result = subprocess.run(alternate_cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    logger.error(f"Alternate ROBOT extraction failed: {result.stderr}")
                    return None
            
            # Verify the module was created and has content
            if os.path.exists(module_path) and os.path.getsize(module_path) > 0:
                logger.info(f"Module created successfully: {module_path}")
                return module_path
            else:
                logger.error(f"Module was not created or is empty: {module_path}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating ontology module: {e}")
            return None

    def process_ontology_modularization(self, ontology_path: str, metrics_json_path: str, 
                                        seed_terms_json_path: str, output_dir: str = "output/ontologies/modules", 
                                        auto_select: bool = True):
        """
        Process ontology modularization workflow:
        1. Select worst metric
        2. Get seed terms for that metric
        3. Create ontology module using ROBOT
        
        Returns a list of created module paths
        """
        try:
            # Select worst metric for module extraction
            selected_metric, metrics_to_process = self.select_worst_metric_for_module(metrics_json_path, auto_select)
            
            created_modules = []
            
            for metric in metrics_to_process:
                # Get seed terms for the selected metric
                seed_terms = self.get_seed_terms_from_json(seed_terms_json_path, metric)
                
                if not seed_terms:
                    logger.warning(f"No seed terms found for metric {metric}. Will try to create module with fallback seed terms.")
                
                # Create module
                module_path = self.create_ontology_module(
                    ontology_path=ontology_path,
                    output_dir=output_dir,
                    metric_name=metric,
                    seed_terms=seed_terms
                )
                
                if module_path:
                    created_modules.append(module_path)
            
            if not created_modules:
                logger.error("No modules were created")
                
                # Fallback: Create a simple extract with owl:Thing as root
                logger.info("Attempting to create a simple extract with owl:Thing as root")
                fallback_seed_terms = [
                    {"term": "Thing", "iri": "http://www.w3.org/2002/07/owl#Thing"}
                ]
                
                fallback_metric = metrics_to_process[0] if metrics_to_process else "fallback"
                
                fallback_module = self.create_ontology_module(
                    ontology_path=ontology_path,
                    output_dir=output_dir,
                    metric_name=fallback_metric,
                    seed_terms=fallback_seed_terms,
                    method="TOP"  # Use TOP for fallback to get the class hierarchy
                )
                
                if fallback_module:
                    created_modules.append(fallback_module)
                    logger.info(f"Created fallback module: {fallback_module}")
                else:
                    logger.error("Fallback module creation failed")
                    
                if not created_modules:
                    return []
            
            return created_modules
            
        except Exception as e:
            logger.error(f"Error in ontology modularization process: {e}")
            return []

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python module_extractor.py <ontology_path> <metrics_json_path> <seed_terms_json_path>")
        sys.exit(1)
    
    try:
        ontology_path = sys.argv[1]
        metrics_json_path = sys.argv[2]
        seed_terms_json_path = sys.argv[3]
        
        extractor = OntologyModuleExtractor()
        modules = extractor.process_ontology_modularization(
            ontology_path=ontology_path,
            metrics_json_path=metrics_json_path,
            seed_terms_json_path=seed_terms_json_path
        )
        
        if modules:
            print(f"Created {len(modules)} modules:")
            for module in modules:
                print(f"- {module}")
        else:
            print("No modules were created")
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1) 
