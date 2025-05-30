#!/usr/bin/env python3
import os
import sys
import logging
import argparse
import shutil
from pathlib import Path
from module_extractor import OntologyModuleExtractor
from cnl_generator import CNLGenerator
from adv_recom import AdvancedRecommendations
from basic_recom import BasicRecommendations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def setup_directories():
    """Create necessary directories for the workflow."""
    os.makedirs("output/ontologies/modules", exist_ok=True)
    os.makedirs("output/cnl", exist_ok=True)
    os.makedirs("output/reports", exist_ok=True)
    
    # Check if simplified glossaries exist
    metrics_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'metrics')
    simplified_metrics_path = os.path.join(metrics_dir, 'Simplified_OQuaRE_Metric_Glossary_with_Terms.csv')
    simplified_subchar_path = os.path.join(metrics_dir, 'Simplified_OQuaRE_Sub-Characteristic_Glossary_with_Terms.csv')
    
    if os.path.exists(simplified_metrics_path) and os.path.exists(simplified_subchar_path):
        logger.info("Simplified glossaries detected - recommendations will include user-friendly explanations")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Generate modular recommendations for ontologies based on worst metrics")
    
    parser.add_argument("ontology_path", help="Path to the ontology file (.owl)")
    parser.add_argument("metrics_path", help="Path to the metrics JSON file")
    parser.add_argument("seed_terms_path", help="Path to the seed terms JSON file")
    parser.add_argument("--mode", choices=["basic", "advanced", "both"], default="both",
                      help="Recommendation mode: basic, advanced, or both (default: both)")
    parser.add_argument("--output-dir", default="output/reports",
                      help="Directory to save recommendation reports (default: output/reports)")
    
    return parser.parse_args()

def generate_modular_recommendations(ontology_path, metrics_path, seed_terms_path, mode="both", output_dir="output/reports"):
    """
    Generate recommendations for an ontology using modularization based on worst metrics.
    
    Workflow:
    1. Extract modules from the ontology based on the worst metrics
    2. Convert modules to CNL
    3. Generate recommendations based on the CNL and metrics
    
    Args:
        ontology_path: Path to the ontology file
        metrics_path: Path to the metrics JSON file
        seed_terms_path: Path to the seed terms JSON file
        mode: Recommendation mode - 'basic', 'advanced', or 'both'
        output_dir: Directory to save recommendation reports
    """
    try:
        # Set up directories
        setup_directories()
        
        # Initialize components
        module_extractor = OntologyModuleExtractor()
        cnl_generator = CNLGenerator()
        
        # Step 1: Extract modules based on worst metrics
        logger.info("Step 1: Extracting modules based on worst metrics...")
        module_paths = module_extractor.process_ontology_modularization(
            ontology_path=ontology_path,
            metrics_json_path=metrics_path,
            seed_terms_json_path=seed_terms_path
        )
        
        if not module_paths:
            logger.error("No modules were created. Cannot proceed.")
            return False
            
        # Step 2: Generate CNL from modules
        logger.info("Step 2: Generating CNL from modules...")
        cnl_files = cnl_generator.process_modules_to_cnl(module_paths, os.path.join("output", "cnl"))
        
        # If no CNL files were generated by the generator, check if owl_to_cnl.py may have
        # created them directly with .txt extension
        if not cnl_files:
            logger.warning("No CNL files were generated by CNLGenerator, checking for direct outputs from owl_to_cnl.py")
            for module_path in module_paths:
                txt_path = Path(module_path).with_suffix('.txt')
                if os.path.exists(txt_path) and os.path.getsize(txt_path) > 0:
                    # Copy to the cnl directory
                    cnl_dir = "output/cnl"
                    os.makedirs(cnl_dir, exist_ok=True)
                    cnl_file = os.path.join(cnl_dir, f"{Path(module_path).stem}_cnl.txt")
                    
                    # Copy the file
                    shutil.copy2(txt_path, cnl_file)
                    logger.info(f"Found and copied CNL file: {txt_path} -> {cnl_file}")
                    cnl_files.append(cnl_file)
        
        if not cnl_files:
            logger.error("Failed to generate CNL from modules. Cannot proceed.")
            
            # Last resort: Try to use the full ontology's CNL if it exists
            ont_txt_path = Path(ontology_path).with_suffix('.txt')
            if os.path.exists(ont_txt_path) and os.path.getsize(ont_txt_path) > 0:
                logger.warning(f"Using full ontology CNL as fallback: {ont_txt_path}")
                cnl_files = [ont_txt_path]
            else:
                logger.error("No fallback CNL available. Cannot proceed.")
                return False
            
        # Step 3: Generate recommendations based on CNL and metrics
        logger.info("Step 3: Generating recommendations...")
        
        for cnl_file in cnl_files:
            # Get base name for reporting
            base_name = Path(cnl_file).stem.replace('_cnl', '')
            
            # Read CNL content
            try:
                with open(cnl_file, 'r', encoding='utf-8') as f:
                    cnl_content = f.read()
            except UnicodeDecodeError:
                # Try with Latin-1 encoding if UTF-8 fails
                with open(cnl_file, 'r', encoding='latin-1') as f:
                    cnl_content = f.read()
                    
            # Skip if the CNL file is empty
            if not cnl_content.strip():
                logger.warning(f"CNL file {cnl_file} is empty, skipping...")
                continue
                
            # Generate recommendations based on mode, for each module
            # Save reports with module-specific filenames
            if mode in ["basic", "both"]:
                logger.info(f"Generating basic recommendations for {base_name}...")
                try:
                    basic_recommender = BasicRecommendations()
                    with open(metrics_path, 'r') as f:
                        metrics_data = f.read()
                    # Save to output_dir with module name
                    basic_report_path = os.path.join(
                        output_dir,
                        f"{base_name}_basic_recommendations.md"
                    )
                    basic_result, _ = basic_recommender.generate_basic_recommendations(
                        cnl_text=cnl_content,
                        metrics_data=metrics_data,
                        seed_terms_json_path=seed_terms_path,
                        output_file=basic_report_path
                    )
                    logger.info(f"Basic recommendations saved to {basic_report_path}")
                except Exception as e:
                    logger.error(f"Error generating basic recommendations: {e}")
            if mode in ["advanced", "both"]:
                logger.info(f"Generating advanced recommendations for {base_name}...")
                try:
                    adv_recommender = AdvancedRecommendations()
                    with open(metrics_path, 'r') as f:
                        metrics_data = f.read()
                    adv_report_path = os.path.join(
                        output_dir,
                        f"{base_name}_advanced_recommendations.md"
                    )
                    adv_result, _ = adv_recommender.generate_advanced_recommendations(
                        cnl_text=cnl_content,
                        metrics_data=metrics_data,
                        seed_terms_json_path=seed_terms_path,
                        output_file=adv_report_path
                    )
                    logger.info(f"Advanced recommendations saved to {adv_report_path}")
                except Exception as e:
                    logger.error(f"Error generating advanced recommendations: {e}")
        
        logger.info("All recommendations generated successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error generating modular recommendations: {e}")
        return False

if __name__ == "__main__":
    try:
        args = parse_arguments()
        
        logger.info("Starting modular recommendation process...")
        logger.info(f"Input ontology: {args.ontology_path}")
        logger.info(f"Metrics data: {args.metrics_path}")
        logger.info(f"Seed terms: {args.seed_terms_path}")
        logger.info(f"Mode: {args.mode}")
        
        success = generate_modular_recommendations(
            ontology_path=args.ontology_path,
            metrics_path=args.metrics_path,
            seed_terms_path=args.seed_terms_path,
            mode=args.mode,
            output_dir=args.output_dir
        )
        
        if success:
            logger.info("Modular recommendation process completed successfully!")
            sys.exit(0)
        else:
            logger.error("Modular recommendation process failed.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)