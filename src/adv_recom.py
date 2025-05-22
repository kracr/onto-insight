import os
import json
import logging
import pandas as pd
from typing import Tuple, List, Dict
from datetime import datetime
from openai import OpenAI  # Changed from Google's Gemini API to OpenAI client
from pathlib import Path
import sys
import argparse

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
    MODEL_NAME = os.getenv("MODEL_NAME")  # Updated default model
except ImportError:
    # Fallback if python-dotenv is not installed
    OPENAI_API_KEY = os.getenv("AI_API_KEY") 
    MODEL_NAME = os.getenv("MODEL_NAME")  # Updated default model

if not OPENAI_API_KEY:
    logger.error("AI API key not found. Please set AI_API_KEY environment variable.")
    sys.exit(1)

class AdvancedRecommendations:
    def __init__(self, api_key: str = OPENAI_API_KEY, model_name: str = MODEL_NAME):
        """Initialize the analyzer with OpenAI API"""
        logger.info("Initializing AdvancedRecommendations...")
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
            logger.error(f"Error initializing OpenAI API: {str(e)}")  # Changed from Gemini to OpenAI
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
            
            # Identify worst metrics based on OQuaRE ranges
            worst_metrics = self._identify_worst_metrics(valid_metrics)
            
            # Get top 5 highest scoring metrics for comparison
            highest_metrics = sorted(valid_metrics.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Get sorted subcharacteristics by value (low to high)
            sorted_subchar = sorted(quality_scores.items(), key=lambda x: x[1])
            lowest_subchars = sorted_subchar[:5]
            
            return {
                "worst_metrics": worst_metrics,
                "highest_metrics": highest_metrics,
                "lowest_subchars": lowest_subchars,
                "quality_scores": quality_scores,
                "all_metrics": valid_metrics
            }
        except Exception as e:
            logger.error(f"Error extracting metrics: {str(e)}")
            raise

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
                    try:
                        threshold = float(worst_range.split()[1])
                        is_worst = score < threshold
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Error parsing threshold from '{worst_range}': {e}")
                elif worst_range.startswith('>'):
                    # Format: "> 12" or ">0. 8" (with typo)
                    try:
                        # Fix any typos in the CSV
                        cleaned = worst_range.replace('>0.', '> 0.').replace('>0 .', '> 0.')
                        cleaned = cleaned.replace('>', '').strip()
                        threshold = float(cleaned)
                        is_worst = score > threshold
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Error parsing threshold from '{worst_range}': {e}")
                
                if is_worst:
                    worst_metrics.append((metric_name, score))
        
        # Sort worst metrics by absolute value (most severe first)
        return worst_metrics

    def _get_metric_description(self, metric_name: str) -> str:
        """Get the description of a metric from the framework metrics CSV or simplified glossary"""
        try:
            # First try to get from simplified glossary
            search_name = metric_name
            if metric_name.endswith('Onto'):
                search_name = metric_name[:-4]  # Remove 'Onto' suffix
                
            metric_row = self.simplified_metrics_glossary[self.simplified_metrics_glossary['Metric Code'] == search_name]
            
            if not metric_row.empty and 'Simplified Meaning' in metric_row.columns:
                term = metric_row['Term'].iloc[0]
                meaning = metric_row['Simplified Meaning'].iloc[0]
                return f"{term}: {meaning}"
                
            # Fallback to original framework metrics
            search_name = metric_name
            metric_row = self.framework_metrics[self.framework_metrics['Metric_Name'] == search_name]
            
            if metric_row.empty:
                # Try with Onto suffix
                if not metric_name.endswith('Onto'):
                    metric_row = self.framework_metrics[self.framework_metrics['Metric_Name'] == f"{metric_name}Onto"]
                    
            if not metric_row.empty and 'Description' in metric_row:
                return metric_row['Description'].iloc[0]
            return "No description available"
        except Exception as e:
            logger.warning(f"Error getting metric description: {e}")
            return "No description available"

    def _get_metric_range_info(self, metric_name: str) -> str:
        """Get the range information for a metric from the oquare_metrics CSV"""
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

    def _create_detailed_context_data(self) -> str:
        """Create detailed context information from CSV files for the LLM prompt"""
        context = "\nDetailed Metrics Information:\n"
        
        try:
            # Add simplified metric glossary
            context += "\nSimplified Metrics Glossary:\n"
            for _, row in self.simplified_metrics_glossary.iterrows():
                context += f"- {row['Metric Code']} ({row['Term']}): {row['Simplified Meaning']}\n"
            
            # Add simplified sub-characteristic glossary
            context += "\nSimplified Sub-characteristics Glossary:\n"
            for _, row in self.simplified_subchar_glossary.iterrows():
                context += f"- {row['Sub-Characteristic (Code)']} ({row['Term']}): {row['Simplified Meaning']}\n"
                
            # Then add the original detailed context
            # Add framework metrics descriptions with formulas and interpretation guidelines
            context += "\nBase Metrics with Interpretation Guidelines:\n"
            for _, row in self.framework_metrics.iterrows():
                if 'Metric_Name' in row and 'Description' in row:
                    context += f"- {row['Metric_Name']}:\n"
                    context += f"  Description: {row['Description']}\n"
                    if 'Best_Score' in row:
                        context += f"  Best score (5): {row['Best_Score']}\n"
                    if 'Worst_Score' in row:
                        context += f"  Worst score (1): {row['Worst_Score']}\n"
                    if 'Formula' in row and not pd.isna(row['Formula']):
                        context += f"  Formula: {row['Formula']}\n"

            # Add characteristics descriptions with related subcharacteristics
            context += "\nCharacteristics with Related Sub-characteristics:\n"
            for _, char_row in self.char_desc.iterrows():
                if 'Characteristic' in char_row and 'Description' in char_row:
                    char_name = char_row['Characteristic']
                    context += f"- {char_name}:\n"
                    context += f"  Description: {char_row['Description']}\n"
                    
                    # Find related subcharacteristics - safely access column
                    try:
                        if 'Sub-Characteristic' in self.char_subchar_rel.columns:
                            related_subchars = self.char_subchar_rel[
                                self.char_subchar_rel['Characteristic'] == char_name
                            ]['Sub-Characteristic'].tolist()
                            
                            if related_subchars:
                                context += f"  Related Sub-characteristics: {', '.join(related_subchars)}\n"
                    except Exception as e:
                        logger.warning(f"Error getting related subcharacteristics: {e}")
            
            # Add detailed subcharacteristics descriptions with their formulas
            context += "\nDetailed Sub-characteristics Information:\n"
            for _, row in self.subchar_desc.iterrows():
                try:
                    # Use the correct column name based on what we detected in __init__
                    if self.subchar_desc_key in row:
                        subchar_name = row[self.subchar_desc_key]
                        context += f"- {subchar_name}:\n"
                        if 'Description' in row:
                            context += f"  Description: {row['Description']}\n"
                        
                        # Get formula
                        try:
                            if self.subchars_formulas_key in self.subchars_formulas.columns:
                                formula_row = self.subchars_formulas[
                                    self.subchars_formulas[self.subchars_formulas_key] == subchar_name
                                ]
                                if not formula_row.empty and 'Formula' in formula_row:
                                    formula = formula_row['Formula'].iloc[0]
                                    context += f"  Formula: {formula}\n"
                                    
                                    # Get related metrics
                                    if not pd.isna(formula):
                                        metrics_in_formula = [m.strip() for m in formula.replace('+', ',').replace('*', ',').replace('/', ',').replace('-', ',').split(',') if m.strip()]
                                        context += f"  Related Metrics: {', '.join(metrics_in_formula)}\n"
                        except Exception as e:
                            logger.warning(f"Error getting formula for {subchar_name}: {e}")
                except Exception as e:
                    logger.warning(f"Error processing subcharacteristic row: {e}")
        except Exception as e:
            logger.error(f"Error creating detailed context data: {e}")
            context += "\nError generating complete metrics information. Using limited data.\n"

        return context

    def format_seed_terms_for_prompt(self, seed_terms_json: Dict) -> str:
        """Format seed terms from JSON for detailed technical prompt"""
        if not seed_terms_json:
            return "No seed terms available."
            
        seed_terms_text = "### Important Ontology Concepts (Seed Terms) by Metric:\n"
        
        for metric, terms in seed_terms_json.items():
            if terms:
                seed_terms_text += f"#### {metric}:\n"
                for i, term in enumerate(terms, 1):
                    term_name = term.get('term', 'Unknown')
                    iri = term.get('iri', '')
                    seed_terms_text += f"{i}. {term_name}"
                    if iri:
                        seed_terms_text += f" ({iri})"
                    seed_terms_text += "\n"
        
        return seed_terms_text

    def display_worst_metrics(self, metrics_info: Dict) -> List[str]:
        """Display the worst metrics and let user select which ones to focus on"""
        worst_metrics = metrics_info.get("worst_metrics", [])
        if not worst_metrics:
            logger.warning("No worst metrics found!")
            return []

        # Ensure we have at least 5 metrics to show or show all available
        display_metrics = worst_metrics[:min(5, len(worst_metrics))]
            
        print("\n===================================================")
        print("=== TOP 5 WORST PERFORMING METRICS ================")
        print("===================================================")
        
        for i, (metric, score) in enumerate(display_metrics, 1):
            description = self._get_metric_description(metric)
            range_info = self._get_metric_range_info(metric)
            
            print(f"\n{i}. {metric}: {score}")
            print(f"   - Description: {description[:100]}...")
            print(f"   - {range_info}")
            
        print("\n===================================================")
        # Automatically select all worst metrics without prompting
        logger.info("Auto-selecting all worst metrics")
        return [m[0] for m in display_metrics]

    def generate_advanced_recommendations(self, cnl_text: str, metrics_data: str, seed_terms_json_path: str, output_dir: str = None, output_file: str = None) -> Tuple[str, str]:
        """Generate advanced, technical recommendations using CNL text, metrics, and seed terms"""
        try:
            logger.info("Starting advanced recommendation generation...")
            
            # Load seed terms from JSON file
            with open(seed_terms_json_path, 'r') as f:
                seed_terms_json = json.load(f)
            
            metrics_info = self._extract_metrics(metrics_data)
            
            # Auto-select the top worst metrics without prompting
            worst_list = metrics_info.get("worst_metrics", [])
            selected_metrics = [m[0] for m in worst_list[:min(5, len(worst_list))]]
            logger.info(f"Auto-selected worst metrics: {', '.join(selected_metrics)}")
            
            # Filter worst metrics to only include selected ones
            filtered_worst_metrics = [m for m in metrics_info.get("worst_metrics", []) if m[0] in selected_metrics]
            
            # If somehow we ended up with no metrics after filtering, use original list
            if not filtered_worst_metrics:
                logger.warning("Filtering resulted in no metrics. Using original worst metrics.")
                filtered_worst_metrics = metrics_info.get("worst_metrics", [])[:5]
                
            metrics_info["worst_metrics"] = filtered_worst_metrics
            
            context_data = self._create_detailed_context_data()
            
            # Format seed terms for prompt
            seed_terms_text = self.format_seed_terms_for_prompt(seed_terms_json)
            
            # Changed from Gemini's prompt format to OpenAI's message format
            messages = [
                {
                    "role": "system",
                    "content": "You are an Advanced Ontology Engineering Specialist with expertise in ontology quality evaluation, metrics, and optimization."
                },
                {
                    "role": "user",
                    "content": f"""
Your task is to analyze an ontology's natural language description, metrics, and key concepts (seed terms)
and provide detailed, technical recommendations for improvement focusing specifically on the selected metrics.
Your audience is ontology engineers who understand ontology engineering principles and terminology.

Natural Language Description of the Ontology:
{cnl_text[:4000]}  # Limit text size

{seed_terms_text}

{context_data}

Quality Scores (Sub-characteristics):
{chr(10).join(f"{k}: {v}" for k, v in metrics_info['quality_scores'].items())}

Selected Metrics to Focus On:
{chr(10).join(f"{m[0]}: {m[1]}" for m in filtered_worst_metrics)}

These metrics were specifically selected by the user for focused improvement.

Highest Scoring Metrics (Strengths):
{chr(10).join(f"{m[0]}: {m[1]}" for m in metrics_info['highest_metrics'])}

Lowest Scoring Subcharacteristics:
{chr(10).join(f"{s[0]}: {s[1]}" for s in metrics_info['lowest_subchars'])}

Format your response as follows:

# Advanced Ontology Analysis and Recommendations

## 1. Comprehensive Assessment
[Provide a detailed assessment of the ontology's quality, mentioning specific strengths and weaknesses with reference to metrics and subcharacteristics]

## 2. Technical Analysis by Key Quality Dimensions

### Structural Dimension
- Metrics assessment: [Analyze relevant metrics]
- Identified issues: [List specific structural issues]
- Technical recommendations: [Provide detailed recommendations]

### Functional Dimension
- Metrics assessment: [Analyze relevant metrics]
- Identified issues: [List specific functional issues]
- Technical recommendations: [Provide detailed recommendations]

### Semantic Dimension
- Metrics assessment: [Analyze relevant metrics]
- Identified issues: [List specific semantic issues]
- Technical recommendations: [Provide detailed recommendations]

## 3. Critical Metrics Improvement Plan

For each of the user-selected metrics:

### [Metric Name] (Current score: [value])
- Technical explanation: [Explain what this metric measures and why it's low]
- Impact on subcharacteristics: [Explain how improving this metric will affect subcharacteristics]
- Seed terms involved: [List relevant seed terms identified]
- Detailed improvement approach:
  * [Step 1 with technical details]
  * [Step 2 with technical details]
  * [Expected improvement calculation/estimate]

## 4. Implementation Roadmap

### Immediate Technical Improvements
[List specific technical changes with implementation details]

### Medium-term Refactoring
[List architectural or structural changes]

### Long-term Quality Strategy
[Provide strategic recommendations for maintaining quality]

Remember:
- Provide technically precise language that ontology engineers will understand
- Reference specific metrics and their mathematical relationships
- Mention specific seed terms in your recommendations where relevant
- Include expected numerical improvements when possible
- Focus on mathematical/technical aspects rather than business value
- Prioritize recommendations based on impact on metrics
- Pay special attention to the metrics specifically selected by the user
"""
                }
            ]

            # Changed from Gemini to OpenAI API call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=4096
            )

            # Extract text from the response (different for OpenAI vs Gemini)
            result = response.choices[0].message.content
            
            # Set default report path only if no specific output file is provided
            if output_file:
                report_path = output_file
                # Save report to specified output_file
                os.makedirs(os.path.dirname(report_path), exist_ok=True)
                with open(report_path, 'w', encoding='utf-8') as f:
                    f.write(result)
                logger.info(f"Advanced recommendations saved to {report_path}")
            else:
                # Only create a timestamp-based path if no output file is specified
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                if output_dir:
                    # Make sure output directory exists
                    os.makedirs(output_dir, exist_ok=True)
                    report_path = os.path.join(output_dir, f"advanced_recommendations_{timestamp}.md")
                elif os.path.isdir("./output/reports"):
                    # Prefer ./output/reports if it exists and no output_dir is specified
                    os.makedirs("./output/reports", exist_ok=True)
                    report_path = os.path.join("./output/reports", f"advanced_recommendations_{timestamp}.md")
                else:
                    # Fallback to reports directory in current location
                    os.makedirs("reports", exist_ok=True)
                    report_path = os.path.join("reports", f"advanced_recommendations_{timestamp}.md")
            
            return result, report_path
            
        except Exception as e:
            logger.error(f"Error in generate_advanced_recommendations: {str(e)}")
            raise

if __name__ == "__main__":
    # Add argument parsing
    parser = argparse.ArgumentParser(description='Generate advanced recommendations for ontology improvement')
    parser.add_argument('cnl_file', help='Path to the CNL text file')
    parser.add_argument('metrics_file', help='Path to the metrics JSON file')
    parser.add_argument('seed_terms_file', help='Path to the seed terms JSON file')
    parser.add_argument('--output-dir', help='Output directory for the recommendations report')
    parser.add_argument('--output-file', help='Specific output file path for the report')
    
    args = parser.parse_args()
    
    try:
        # Read CNL file
        with open(args.cnl_file, 'r', encoding='utf-8') as f:
            cnl_text = f.read()
            
        # Read metrics file
        with open(args.metrics_file, 'r', encoding='utf-8') as f:
            metrics_data = f.read()
        
        # If output_file is specified, use its directory as output_dir
        output_dir = args.output_dir
        output_file_path = None
        
        # If we have a specific output file, prepare it
        if args.output_file:
            output_file_path = os.path.splitext(args.output_file)[0] + ".md"
        
        recommender = AdvancedRecommendations()
        result, report_path = recommender.generate_advanced_recommendations(
            cnl_text, 
            metrics_data, 
            args.seed_terms_file,
            output_dir,  
            output_file_path  # Pass the output file path to the function
        )
        
        # If specific output file was requested, save directly to it
        if output_file_path:
            try:
                # Ensure directory exists
                os.makedirs(os.path.dirname(os.path.abspath(output_file_path)), exist_ok=True)
                with open(output_file_path, 'w', encoding='utf-8') as f:
                    f.write(result)
                logger.info(f"Report saved to: {output_file_path}")
            except Exception as write_error:
                logger.error(f"Failed to write to {output_file_path}: {write_error}")
                # Try emergency save
                emergency_path = os.path.join(os.path.dirname(output_file_path) or "./output/reports", 
                                            "emergency_advanced_recommendations.md")
                os.makedirs(os.path.dirname(emergency_path), exist_ok=True)
                with open(emergency_path, 'w', encoding='utf-8') as f:
                    f.write(result)
                logger.info(f"Emergency save completed to {emergency_path}")
        # No else needed, as we've already saved the file in generate_advanced_recommendations if 
        # output_file_path was None
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)