import os
import json
import logging
import pandas as pd
from typing import Tuple, List, Dict
from datetime import datetime
from openai import OpenAI
from pathlib import Path
import sys
import argparse  # Add this import

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Read API key from .env file or environment variable
try:
    from dotenv import load_dotenv
    load_dotenv()
    OPENAI_API_KEY = os.getenv("AI_API_KEY")
    MODEL_NAME = os.getenv("MODEL_NAME")
except ImportError:
    # Fallback if python-dotenv is not installed
    OPENAI_API_KEY = os.getenv("AI_API_KEY")
    MODEL_NAME = os.getenv("MODEL_NAME")

if not OPENAI_API_KEY:
    logger.error("AI API key not found. Please set AI_API_KEY environment variable.")
    sys.exit(1)

class BasicRecommendations:
    def __init__(self, api_key: str = OPENAI_API_KEY, model_name: str = MODEL_NAME):
        """Initialize the analyzer with OpenAI API"""
        logger.info("Initializing BasicRecommendations...")
        try:
            self.client = OpenAI(
                api_key=api_key,
                base_url=os.getenv("AI_URL")
            )
            self.model = model_name
            self.temperature = 0.1
            
            # Get the absolute path to the metrics directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            base_dir = os.path.dirname(current_dir)
            metrics_dir = os.path.join(base_dir, 'metrics')
            
            # Load CSV data with correct paths
            try:
                self.subchars_formulas = pd.read_csv(os.path.join(metrics_dir, 'Subchars_formulas.csv'))
                # Handle column name variations
                if 'Sub-characteristic' in self.subchars_formulas.columns:
                    self.subchars_formulas_key = 'Sub-characteristic'
                elif 'Sub-Characteristic' in self.subchars_formulas.columns:
                    self.subchars_formulas_key = 'Sub-Characteristic'
                else:
                    # Default if neither exists
                    self.subchars_formulas_key = 'Sub-characteristic'
                    logger.warning("Column 'Sub-characteristic' or 'Sub-Characteristic' not found in Subchars_formulas.csv")
                    
                self.char_subchar_rel = pd.read_csv(os.path.join(metrics_dir, 'charaterstic_subcharacterstic_relationship.csv'))
                self.subchar_desc = pd.read_csv(os.path.join(metrics_dir, 'subcharacterstic_descriptions.csv'))
                # Handle column name variations
                if 'Sub-Characteristic' in self.subchar_desc.columns:
                    self.subchar_desc_key = 'Sub-Characteristic'
                else:
                    self.subchar_desc_key = 'Sub-characteristic'
                    logger.warning("Column 'Sub-Characteristic' not found in subcharacterstic_descriptions.csv")
                
                self.framework_metrics = pd.read_csv(os.path.join(metrics_dir, 'framework_metrics_descriptions.csv'))
                self.char_desc = pd.read_csv(os.path.join(metrics_dir, 'characterstics_descriptions.csv'))
                
                # Load metrics ranges for determining worst metrics
                self.metrics_ranges = pd.read_csv(os.path.join(metrics_dir, 'oquare_metrics.csv'))
                
                # Load new simplified glossaries
                self.simplified_metrics_glossary = pd.read_csv(os.path.join(metrics_dir, 'Simplified_OQuaRE_Metric_Glossary_with_Terms.csv'))
                self.simplified_subchar_glossary = pd.read_csv(os.path.join(metrics_dir, 'Simplified_OQuaRE_Sub-Characteristic_Glossary_with_Terms.csv'))
                logger.info("Successfully loaded simplified glossaries")
            except Exception as e:
                logger.error(f"Error loading CSV files: {e}")
                # Create backup default DataFrames with minimal columns
                if not hasattr(self, 'subchars_formulas'):
                    self.subchars_formulas = pd.DataFrame(columns=['Sub-characteristic', 'Formula'])
                    self.subchars_formulas_key = 'Sub-characteristic'
                if not hasattr(self, 'subchar_desc'):
                    self.subchar_desc = pd.DataFrame(columns=['Sub-Characteristic', 'Description'])
                    self.subchar_desc_key = 'Sub-Characteristic'
                if not hasattr(self, 'metrics_ranges'):
                    self.metrics_ranges = pd.DataFrame(columns=['Metric', '1 (Worst)'])
                # Create empty simplified glossaries if loading fails
                if not hasattr(self, 'simplified_metrics_glossary'):
                    self.simplified_metrics_glossary = pd.DataFrame(columns=['Metric Code', 'Term', 'Simplified Meaning'])
                if not hasattr(self, 'simplified_subchar_glossary'):
                    self.simplified_subchar_glossary = pd.DataFrame(columns=['Sub-Characteristic (Code)', 'Term', 'Simplified Meaning'])
            
        except Exception as e:
            logger.error(f"Error initializing OpenAI API: {str(e)}")
            raise

    def _extract_metrics(self, metrics_data: str) -> dict:
        """Extract and categorize metrics from JSON data"""
        try:
            data = json.loads(metrics_data)
            
            # Extract both metrics and subcharacteristics
            metrics = data.get('metrics', {})
            subcharacteristics = data.get('subcharacteristics', {})
            
            # Process base metrics
            valid_metrics = {}
            for k, v in metrics.items():
                if k not in ['name', 'timestamp']:
                    try:
                        valid_metrics[k] = round(float(v), 4)
                    except (ValueError, TypeError):
                        logger.warning(f"Skipping invalid metric: {k}: {v}")
            
            # Process subcharacteristics
            quality_scores = {}
            for k, v in subcharacteristics.items():
                if isinstance(v, (int, float)):
                    quality_scores[k] = round(float(v), 4)
            
            # Calculate absolute deviation from ideal range for each metric
            worst_metrics = self._identify_worst_metrics(valid_metrics)
            
            return {
                "worst_metrics": worst_metrics,
                "quality_scores": quality_scores,
                "all_metrics": valid_metrics
            }
        except Exception as e:
            logger.error(f"Error extracting metrics: {str(e)}")
            raise

    def _identify_worst_metrics(self, metrics: Dict[str, float]) -> List[Tuple[str, float]]:
        """
        Identify the worst metrics based on their absolute deviation from ideal range.
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
        
        # Sort worst metrics by absolute value (most severe first)
        return worst_metrics

    def _create_context_data(self) -> str:
        """Create context information from CSV files for the LLM prompt"""
        context = "\nMetrics Information:\n"
        
        # Add simplified metric glossary first (more user-friendly)
        context += "\nSimplified Metrics Explanation:\n"
        for _, row in self.simplified_metrics_glossary.iterrows():
            context += f"- {row['Metric Code']} ({row['Term']}): {row['Simplified Meaning']}\n"
        
        # Add simplified sub-characteristics glossary
        context += "\nSimplified Sub-characteristics Explanation:\n"
        for _, row in self.simplified_subchar_glossary.iterrows():
            # Extract the code from the sub-characteristic code field (e.g., "Formal Relations Support (C1.2)" -> "C1.2")
            code = row['Sub-Characteristic (Code)']
            code_match = code.split('(')[-1].split(')')[0] if '(' in code and ')' in code else code
            context += f"- {code_match} ({row['Term']}): {row['Simplified Meaning']}\n"
        
        # Add framework metrics descriptions
        context += "\nBase Metrics:\n"
        for _, row in self.framework_metrics.iterrows():
            context += f"- {row['Metric_Name']}: {row['Description']}\n"
            if 'Best_Score' in row and 'Worst_Score' in row:
                context += f"  Best score (5): {row['Best_Score']}, Worst score (1): {row['Worst_Score']}\n"

        # Add characteristics descriptions
        context += "\nCharacteristics:\n"
        for _, row in self.char_desc.iterrows():
            if 'Characteristic' in row and 'Description' in row:
                context += f"- {row['Characteristic']}: {row['Description']}\n"

        # Add subcharacteristics descriptions
        context += "\nSub-characteristics:\n"
        for _, row in self.subchar_desc.iterrows():
            if self.subchar_desc_key in row and 'Description' in row:
                context += f"- {row[self.subchar_desc_key]}: {row['Description']}\n"

        return context

    def format_seed_terms_for_prompt(self, seed_terms_json: Dict) -> str:
        """Format seed terms from JSON for inclusion in the prompt"""
        if not seed_terms_json:
            return "No seed terms available."
            
        seed_terms_text = "Important Ontology Concepts (Seed Terms):\n"
        
        for metric, terms in seed_terms_json.items():
            if terms:
                seed_terms_text += f"- {metric}:\n"
                for term in terms[:5]:  # Limit to 5 terms per metric
                    term_name = term.get('term', 'Unknown')
                    iri = term.get('iri', '')
                    seed_terms_text += f"  * {term_name}\n"
        
        return seed_terms_text

    def generate_basic_recommendations(self, cnl_text: str, metrics_data: str, seed_terms_json_path: str, output_file: str = None) -> Tuple[str, str]:
        """Generate basic, user-friendly recommendations using CNL text, metrics, and seed terms"""
        try:
            logger.info("Starting basic recommendation generation...")
            
            # Load seed terms from JSON file
            with open(seed_terms_json_path, 'r') as f:
                seed_terms_json = json.load(f)
            
            metrics_info = self._extract_metrics(metrics_data)
            context_data = self._create_context_data()
            
            # Format seed terms for prompt
            seed_terms_text = self.format_seed_terms_for_prompt(seed_terms_json)
            
            # Take top 5 worst metrics only for basic mode
            worst_metrics = metrics_info["worst_metrics"][:5]
            
            # Create messages for ChatGPT
            messages = [
                {
                    "role": "system",
                    "content": "You are an Ontology Assistant that helps users understand their ontology quality and provides simple, actionable recommendations."
                },
                {
                    "role": "user",
                    "content": f"""
Analyze this ontology and provide basic, easy-to-understand recommendations for improvement.

Natural Language Description of the Ontology:
{cnl_text[:3000]}

{seed_terms_text}

{context_data}

Current Quality Scores (Sub-characteristics):
{chr(10).join(f"{k}: {v}" for k, v in metrics_info['quality_scores'].items())}

Metrics Needing Improvement (worst scores):
{chr(10).join(f"{m[0]}: {m[1]}" for m in worst_metrics)}

Format your response as follows:

# Basic Ontology Recommendations

## Overview
[Provide a simple 2-3 sentence summary of the ontology's current quality]

## Key Strengths
[List 2-3 areas where the ontology performs well]

## Areas for Improvement
[List 3-4 areas where the ontology needs improvement, focusing on the most important ones]

## Simple Recommendations
1. [First simple recommendation]
   - Why: [Brief explanation in simple terms]
   - How: [1-2 simple steps to implement]
   
2. [Second simple recommendation]
   - Why: [Brief explanation in simple terms]
   - How: [1-2 simple steps to implement]
   
3. [Third simple recommendation]
   - Why: [Brief explanation in simple terms]
   - How: [1-2 simple steps to implement]

## Next Steps
[Brief closing with 1-2 sentences on what to do next]

Remember:
- Use simple, non-technical language that anyone can understand
- Focus on practical, easy-to-implement recommendations
- Mention the seed terms in your recommendations where relevant
- Explain concepts in plain language without jargon
- Keep your explanations brief and to the point
"""
                }
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=2048
            )

            result = response.choices[0].message.content
            
            # Set default path if we don't have a specific output file
            if not output_file:
                # Generate default report path in reports directory
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                # Always prefer ./output/reports if it exists
                if os.path.isdir("./output/reports"):
                    report_dir = "./output/reports"
                else:
                    report_dir = "reports"
                    os.makedirs(report_dir, exist_ok=True)
                
                report_path = os.path.join(report_dir, f"basic_recommendations_{timestamp}.md")
                
                # Save the report to default path
                with open(report_path, 'w', encoding='utf-8') as f:
                    f.write(result)
                logger.info(f"Recommendations saved to default path: {report_path}")
            else:
                # We have a specific output file, don't generate a timestamp-based one
                # Just return the path for the main function to handle
                report_path = output_file
                # Save report to specified output_file
                os.makedirs(os.path.dirname(report_path), exist_ok=True)
                with open(report_path, 'w', encoding='utf-8') as f:
                    f.write(result)
                logger.info(f"Basic recommendations saved to {report_path}")
            
            return result, report_path
            
        except Exception as e:
            logger.error(f"Error in generate_basic_recommendations: {str(e)}")
            raise

def main():
    # Use argparse for better command line argument handling
    parser = argparse.ArgumentParser(description='Generate basic ontology recommendations')
    parser.add_argument('cnl_file', help='Path to the CNL file')
    parser.add_argument('metrics_file', help='Path to the metrics JSON file')
    parser.add_argument('seed_terms_file', help='Path to the seed terms JSON file')
    parser.add_argument('output_file', nargs='?', help='Optional output file path')
    
    args = parser.parse_args()
    
    try:
        # Read CNL file
        with open(args.cnl_file, 'r', encoding='utf-8') as f:
            cnl_text = f.read()
            
        # Read metrics file
        with open(args.metrics_file, 'r', encoding='utf-8') as f:
            metrics_data = f.read()
            
        # If we have a specific output file, prepare it with .md extension
        output_file_path = None
        if args.output_file:
            output_file_path = os.path.splitext(args.output_file)[0] + ".md"
            # Create directory if needed but DON'T write to the file yet
            os.makedirs(os.path.dirname(os.path.abspath(output_file_path)), exist_ok=True)
            
        recommender = BasicRecommendations()
        result, report_path = recommender.generate_basic_recommendations(
            cnl_text, 
            metrics_data, 
            args.seed_terms_file,
            output_file_path  # Pass the prepared output path or None
        )
        
        # If we have a specific output file, save to it ONCE only
        if output_file_path:
            try:
                with open(output_file_path, 'w', encoding='utf-8') as f:
                    f.write(result)
                logger.info(f"Report saved to: {output_file_path}")
            except Exception as write_err:
                logger.error(f"Failed to write to {output_file_path}: {write_err}")
                # Try emergency save in same directory
                emergency_path = os.path.join(os.path.dirname(output_file_path), f"emergency_basic_recommendations.md")
                with open(emergency_path, 'w', encoding='utf-8') as f:
                    f.write(result)
                logger.info(f"Emergency save completed to {emergency_path}")
        else:
            # We already saved to the default path in generate_basic_recommendations
            logger.info(f"Report saved to: {report_path}")
        
        # Double-check that the file was actually written
        check_path = output_file_path if output_file_path else report_path
        if not os.path.exists(check_path):
            logger.error(f"Failed to write recommendations to {check_path}")
            
            # Attempt emergency save
            emergency_path = "./output/reports/emergency_basic_recommendations.md"
            os.makedirs(os.path.dirname(emergency_path), exist_ok=True)
                
            with open(emergency_path, 'w', encoding='utf-8') as f:
                f.write(result)
            logger.info(f"Emergency save completed to {emergency_path}")
            
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        parser.print_usage()
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
