#!/usr/bin/env python3
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def check_metrics_files():
    """
    Check if required metrics files exist in their original locations.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    metrics_dir = os.path.join(script_dir, 'metrics')
    
    required_files = [
        'oquare_metrics.csv',
        'framework_metrics_descriptions.csv',
        'Subchars_formulas.csv',
        'charaterstic_subcharacterstic_relationship.csv',
        'subcharacterstic_descriptions.csv',
        'characterstics_descriptions.csv',
        'Simplified_OQuaRE_Metric_Glossary_with_Terms.csv',
        'Simplified_OQuaRE_Sub-Characteristic_Glossary_with_Terms.csv'
    ]
    
    missing_files = []
    for file in required_files:
        file_path = os.path.join(metrics_dir, file)
        if not os.path.isfile(file_path):
            missing_files.append(file)
    
    if missing_files:
        logger.error(f"The following required metrics files are missing: {', '.join(missing_files)}")
        logger.error(f"Please ensure all files are present in the {metrics_dir} directory.")
        return False
    
    logger.info("All required metrics files are present in their original location.")
    return True

if __name__ == "__main__":
    if not check_metrics_files():
        sys.exit(1)
    sys.exit(0)