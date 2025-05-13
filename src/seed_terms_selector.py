#!/usr/bin/env python3
import os
import sys
import json
import csv
import logging
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class SeedTermSelector:
    def __init__(self, metrics_ranges_csv: str = "metrics/oquare_metrics.csv"):
        """Initialize the selector with metrics ranges."""
        self.metrics_ranges = self._load_metrics_ranges(metrics_ranges_csv)
        self.java_class_path = "target/calculation_engine-1.0-SNAPSHOT-jar-with-dependencies.jar"
        
    def _load_metrics_ranges(self, csv_path: str) -> Dict[str, Dict[str, Any]]:
        """Load metrics ranges from CSV file."""
        metrics_ranges = {}
        try:
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    metric_name = row['Metric']
                    # Store the worst score range (column "1 (Worst)")
                    worst_range = row['1 (Worst)']
                    
                    # Parse the worst range
                    if worst_range.startswith('<'):
                        # Format: "< 0.2"
                        upper_bound = float(worst_range.split()[1])
                        range_type = 'less_than'
                        threshold = upper_bound
                    elif worst_range.startswith('>'):
                        # Format: "> 12" or ">0. 8" (with typo)
                        # Fix any typos in the CSV
                        cleaned = worst_range.replace('>0.', '> 0.').replace('>0 .', '> 0.')
                        lower_bound = float(cleaned.split()[1])
                        range_type = 'greater_than'
                        threshold = lower_bound
                    else:
                        # This shouldn't happen with the current CSV
                        logger.warning(f"Unknown range format: {worst_range} for {metric_name}")
                        continue
                    
                    metrics_ranges[metric_name] = {
                        'type': range_type,
                        'threshold': threshold
                    }
            logger.info(f"Loaded metrics ranges for {len(metrics_ranges)} metrics")
            return metrics_ranges
        except Exception as e:
            logger.error(f"Error loading metrics ranges: {e}")
            raise

    def is_worst_score(self, metric_name: str, value: float) -> bool:
        """Check if a metric value falls in the worst range."""
        if metric_name not in self.metrics_ranges:
            logger.warning(f"Unknown metric: {metric_name}")
            return False
            
        metric_range = self.metrics_ranges[metric_name]
        range_type = metric_range['type']
        threshold = metric_range['threshold']
        
        if range_type == 'less_than':
            return value < threshold
        elif range_type == 'greater_than':
            return value > threshold
        return False

    def select_worst_metrics(self, metrics_data: Dict) -> List[str]:
        """
        Select metrics that fall in the worst range.
        Returns a list of metric names (without 'Onto' suffix for compatibility with extractors).
        """
        worst_metrics = []
        
        for metric_name, value in metrics_data.items():
            # Skip non-metrics fields
            if metric_name in ['name', 'timestamp'] or not isinstance(value, (int, float)):
                continue
                
            # Check if the metric is in our ranges
            # Some metrics in the data might have 'Onto' suffix already, some might not
            clean_metric = metric_name
            if not metric_name.endswith('Onto'):
                clean_metric = f"{metric_name}Onto"
            
            # Try with both original name and name with Onto suffix
            if clean_metric in self.metrics_ranges:
                if self.is_worst_score(clean_metric, float(value)):
                    # Store the metric name without 'Onto' suffix for extractor compatibility
                    if clean_metric.endswith('Onto'):
                        base_metric = clean_metric[:-4]  # Remove 'Onto' suffix
                    else:
                        base_metric = clean_metric
                    worst_metrics.append(base_metric)
            elif metric_name in self.metrics_ranges:
                if self.is_worst_score(metric_name, float(value)):
                    if metric_name.endswith('Onto'):
                        base_metric = metric_name[:-4]  # Remove 'Onto' suffix
                    else:
                        base_metric = metric_name
                    worst_metrics.append(base_metric)
                    
        logger.info(f"Found {len(worst_metrics)} metrics in the worst range: {', '.join(worst_metrics)}")
        return worst_metrics

    def extract_seed_terms(self, ontology_path: str, metrics_data_path: str, output_json_path: str) -> Dict:
        """
        Extract seed terms for the worst metrics and save to JSON.
        
        Args:
            ontology_path: Path to the ontology file (.owl/.rdf)
            metrics_data_path: Path to the metrics JSON file
            output_json_path: Path to save the seed terms JSON file
            
        Returns:
            Dict containing the extracted seed terms
        """
        try:
            # Load metrics data
            with open(metrics_data_path, 'r') as f:
                metrics_data = json.load(f)
            
            # Select worst metrics
            worst_metrics = self.select_worst_metrics(metrics_data.get('metrics', {}))
            
            if not worst_metrics:
                logger.warning("No worst metrics found. Using all metrics.")
                # If no worst metrics found, call the extractor for all metrics
                command = [
                    "mvn", "exec:java",
                    "-Dexec.mainClass=com.calculation_engine.seedTermsExtraction.RunGenericExtractor",
                    f"-Dexec.args={ontology_path}"
                ]
            else:
                # Join worst metrics with comma for the Java program
                metrics_arg = ",".join(worst_metrics)
                command = [
                    "mvn", "exec:java",
                    "-Dexec.mainClass=com.calculation_engine.seedTermsExtraction.RunGenericExtractor",
                    f"-Dexec.args={ontology_path} {metrics_arg}"
                ]
            
            logger.info(f"Running command: {' '.join(command)}")
            result = subprocess.run(command, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Error extracting seed terms: {result.stderr}")
                raise Exception(f"Seed term extraction failed with code {result.returncode}")
            
            # Parse the output into a structured format
            seed_terms = self._parse_seed_terms_output(result.stdout)
            
            # Save to JSON
            with open(output_json_path, 'w') as f:
                json.dump(seed_terms, f, indent=2)
                
            logger.info(f"Seed terms saved to {output_json_path}")
            return seed_terms
            
        except Exception as e:
            logger.error(f"Error in extract_seed_terms: {e}")
            raise

    def _parse_seed_terms_output(self, output: str) -> Dict:
        """Parse the output of the Java seed term extractor into a structured format."""
        seed_terms = {}
        current_metric = None
        
        # Regular expressions for parsing the output
        metric_re = re.compile(r'Metric: (\w+)')
        seed_term_re = re.compile(r'Seed term: (.+)')
        iri_re = re.compile(r'Full IRI: (.+)')
        
        lines = output.strip().split('\n')
        current_terms = []
        
        for line in lines:
            line = line.strip()
            
            # Match metric line
            metric_match = metric_re.match(line)
            if metric_match:
                # If we were processing a previous metric, store its terms
                if current_metric:
                    seed_terms[current_metric] = current_terms
                
                # Start a new metric
                current_metric = metric_match.group(1)
                current_terms = []
                continue
            
            # Match seed term line
            seed_term_match = seed_term_re.match(line)
            if seed_term_match and current_metric:
                term = seed_term_match.group(1)
                current_terms.append({
                    "term": term,
                    "iri": None  # Will be updated when we find the IRI
                })
                continue
            
            # Match IRI line
            iri_match = iri_re.match(line)
            if iri_match and current_metric and current_terms:
                # Update the most recently added term with its IRI
                iri = iri_match.group(1)
                current_terms[-1]["iri"] = iri
        
        # Don't forget to store the last metric
        if current_metric:
            seed_terms[current_metric] = current_terms
        
        return seed_terms

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python seed_terms_selector.py <ontology_path> <metrics_json_path> <output_json_path>")
        sys.exit(1)
        
    try:
        ontology_path = sys.argv[1]
        metrics_json_path = sys.argv[2]
        output_json_path = sys.argv[3]
        
        selector = SeedTermSelector()
        seed_terms = selector.extract_seed_terms(ontology_path, metrics_json_path, output_json_path)
        print(f"Successfully extracted seed terms for the worst metrics.")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1) 