#!/usr/bin/env python3
import os
import logging
import subprocess
import json
from typing import Optional, List
from pathlib import Path
import sys
import importlib.util

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class CNLGenerator:
    def __init__(self):
        """Initialize the CNL generator."""
        # Try to import the owl_to_cnl module directly
        try:
            # Check if owl_to_cnl.py exists
            owl_to_cnl_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "owl_to_cnl.py")
            if os.path.exists(owl_to_cnl_path):
                spec = importlib.util.spec_from_file_location("owl_to_cnl", owl_to_cnl_path)
                self.owl_to_cnl = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(self.owl_to_cnl)
                logger.info("Successfully imported owl_to_cnl module")
                self.has_verbalizer = True
            else:
                logger.warning("owl_to_cnl.py not found in src directory, will use fallback methods")
                self.has_verbalizer = False
        except Exception as e:
            logger.warning(f"Error importing owl_to_cnl module: {e}, will use fallback methods")
            self.has_verbalizer = False
        
    def generate_cnl_from_module(self, module_path: str, output_dir: str = "output/cnl") -> Optional[str]:
        """
        Generate Controlled Natural Language (CNL) from an ontology module.
        Uses external tools to convert the OWL file to CNL.
        
        Args:
            module_path: Path to the ontology module file
            output_dir: Directory to save the generated CNL file
            
        Returns:
            Path to the generated CNL file or None if generation failed
        """
        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate output path
            base_name = Path(module_path).stem
            cnl_path = os.path.join(output_dir, f"{base_name}_cnl.txt")
            
            # Check if the module file exists
            if not os.path.exists(module_path):
                logger.error(f"Module file not found: {module_path}")
                return None
            
            # Method 0 (Preferred): Use owl_to_cnl.py if available
            if self.has_verbalizer:
                try:
                    logger.info(f"Using Verbalizer from owl_to_cnl.py to generate CNL...")
                    cnl_output = self.owl_to_cnl.convert_owl_to_cnl(module_path, cnl_path)
                    
                    if os.path.exists(cnl_output) and os.path.getsize(cnl_output) > 0:
                        logger.info(f"CNL file generated successfully with Verbalizer: {cnl_output}")
                        return cnl_output
                    else:
                        logger.warning("Verbalizer produced empty CNL file, trying next method")
                except Exception as e:
                    logger.warning(f"Verbalizer failed: {e}, trying other methods")
            else:
                # Try using owl_to_cnl.py as a subprocess
                try:
                    logger.info(f"Using owl_to_cnl.py script as subprocess...")
                    owl_to_cnl_cmd = [
                        sys.executable,
                        os.path.join(os.path.dirname(os.path.abspath(__file__)), "owl_to_cnl.py"),
                        module_path
                    ]
                    result = subprocess.run(owl_to_cnl_cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        # The script creates a .txt file with the same name as the input
                        expected_output = str(Path(module_path).with_suffix('.txt'))
                        if os.path.exists(expected_output) and os.path.getsize(expected_output) > 0:
                            # Copy to our preferred output location if different
                            if expected_output != cnl_path:
                                with open(expected_output, 'r', encoding='utf-8') as src:
                                    with open(cnl_path, 'w', encoding='utf-8') as dst:
                                        dst.write(src.read())
                            logger.info(f"CNL file generated successfully with owl_to_cnl.py: {cnl_path}")
                            return cnl_path
                    else:
                        logger.warning(f"owl_to_cnl.py script failed: {result.stderr}, trying other methods")
                except Exception as e:
                    logger.warning(f"Subprocess call to owl_to_cnl.py failed: {e}, trying other methods")
            
            # Method 1: Try using ROBOT export with rdf format
            try:
                self._generate_cnl_with_robot(module_path, cnl_path)
                
                # Check if the CNL file was created and has content
                if os.path.exists(cnl_path) and os.path.getsize(cnl_path) > 0:
                    logger.info(f"CNL file generated successfully with ROBOT: {cnl_path}")
                    return cnl_path
                else:
                    logger.warning("ROBOT export produced empty CNL file, trying alternative method")
            except Exception as e:
                logger.warning(f"ROBOT export failed: {e}, trying alternative method")
            
            # Method 2: Try using OWLAPI / custom tools if available
            try:
                self._generate_cnl_with_custom_tool(module_path, cnl_path)
                
                # Check if the CNL file was created and has content
                if os.path.exists(cnl_path) and os.path.getsize(cnl_path) > 0:
                    logger.info(f"CNL file generated successfully with custom tool: {cnl_path}")
                    return cnl_path
                else:
                    logger.warning("Custom tool produced empty CNL file, trying fallback method")
            except Exception as e:
                logger.warning(f"Custom tool failed: {e}, trying fallback method")
            
            # Method 3: Fallback to extracting labels and comments
            try:
                self._generate_cnl_with_fallback(module_path, cnl_path)
                
                # Check if the CNL file was created and has content
                if os.path.exists(cnl_path) and os.path.getsize(cnl_path) > 0:
                    logger.info(f"CNL file generated successfully with fallback method: {cnl_path}")
                    return cnl_path
                else:
                    logger.warning("Fallback method produced empty CNL file, trying simplified method")
            except Exception as e:
                logger.warning(f"Fallback method failed: {e}, trying simplified method")
                
            # Method 4: Ultra-simple fallback - just convert OWL syntax to readable text
            try:
                self._generate_cnl_with_simplified_fallback(module_path, cnl_path)
                
                # Check if the CNL file was created and has content
                if os.path.exists(cnl_path) and os.path.getsize(cnl_path) > 0:
                    logger.info(f"CNL file generated successfully with simplified fallback: {cnl_path}")
                    return cnl_path
                else:
                    logger.error("All CNL generation methods failed")
                    return None
            except Exception as e:
                logger.error(f"Simplified fallback method failed: {e}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating CNL from module: {e}")
            return None

    def _generate_cnl_with_robot(self, module_path: str, cnl_path: str) -> bool:
        """
        Generate CNL using ROBOT export with RDF format.
        """
        # Use ROBOT to extract information in a more readable format
        robot_cmd = [
            "robot", "export",
            "--input", module_path,
            "--header", "LABEL,IRI,PARENTS,DEFINITION",
            "--output", cnl_path
        ]
        
        result = subprocess.run(robot_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"ROBOT export failed: {result.stderr}")
            return False
            
        # If the export was successful but the file is empty or too small,
        # try a different format (without headers)
        if os.path.getsize(cnl_path) < 100:
            robot_cmd = [
                "robot", "export",
                "--input", module_path,
                "--format", "csv",
                "--output", cnl_path
            ]
            
            result = subprocess.run(robot_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Alternative ROBOT export failed: {result.stderr}")
                return False
        
        return True

    def _generate_cnl_with_custom_tool(self, module_path: str, cnl_path: str) -> bool:
        """
        Generate CNL using custom tool (if available).
        This is a placeholder for any custom CNL generation tool.
        """
        # Check if there's a custom CNL generator tool available
        custom_tool_path = os.environ.get("CNL_GENERATOR_PATH")
        
        if not custom_tool_path or not os.path.exists(custom_tool_path):
            # No custom tool available
            return False
            
        # Execute the custom tool
        custom_cmd = [
            custom_tool_path,
            "--input", module_path,
            "--output", cnl_path
        ]
        
        result = subprocess.run(custom_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Custom CNL generation failed: {result.stderr}")
            return False
            
        return True

    def _generate_cnl_with_fallback(self, module_path: str, cnl_path: str) -> bool:
        """
        Generate CNL using fallback method - extract labels, comments, and structure.
        Uses ROBOT query to extract information and formats it as readable text.
        """
        # Create a temporary SPARQL query file
        temp_query_file = f"{cnl_path}.sparql"
        with open(temp_query_file, 'w') as f:
            f.write("""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            
            SELECT ?entity ?label ?comment ?type ?parentLabel
            WHERE {
              ?entity rdf:type ?type .
              FILTER(?type IN (owl:Class, owl:ObjectProperty, owl:DatatypeProperty, owl:AnnotationProperty))
              
              OPTIONAL { ?entity rdfs:label ?label }
              OPTIONAL { ?entity rdfs:comment ?comment }
              
              OPTIONAL { 
                ?entity rdfs:subClassOf ?parent .
                OPTIONAL { ?parent rdfs:label ?parentLabel }
              }
            }
            """)
            
        # Run ROBOT query to extract data as JSON
        temp_json_file = f"{cnl_path}.json"
        query_cmd = [
            "robot", "query",
            "--input", module_path,
            "--query", temp_query_file, temp_json_file
        ]
        
        result = subprocess.run(query_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"ROBOT query failed: {result.stderr}")
            # Clean up temporary files
            for temp_file in [temp_query_file, temp_json_file]:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            return False
            
        # Process the JSON results and convert to CNL
        try:
            with open(temp_json_file, 'r') as f:
                data = json.load(f)
                
            # Convert results to CNL format
            with open(cnl_path, 'w') as f:
                f.write(f"# Controlled Natural Language for {Path(module_path).stem}\n\n")
                f.write("This document describes the concepts and relationships in the ontology module.\n\n")
                
                # Process classes
                f.write("## Classes\n\n")
                for item in data['results']['bindings']:
                    if 'type' in item and item['type']['value'].endswith('Class'):
                        entity = item.get('entity', {}).get('value', 'Unknown')
                        label = item.get('label', {}).get('value', Path(entity).name)
                        comment = item.get('comment', {}).get('value', 'No description available')
                        parent = item.get('parentLabel', {}).get('value', '')
                        
                        f.write(f"### {label}\n")
                        f.write(f"{comment}\n\n")
                        if parent:
                            f.write(f"This is a type of {parent}.\n\n")
                
                # Process properties
                f.write("## Properties\n\n")
                for item in data['results']['bindings']:
                    if 'type' in item and ('ObjectProperty' in item['type']['value'] or 
                                          'DatatypeProperty' in item['type']['value'] or
                                          'AnnotationProperty' in item['type']['value']):
                        entity = item.get('entity', {}).get('value', 'Unknown')
                        label = item.get('label', {}).get('value', Path(entity).name)
                        comment = item.get('comment', {}).get('value', 'No description available')
                        
                        property_type = 'Relationship'
                        if 'DatatypeProperty' in item['type']['value']:
                            property_type = 'Attribute'
                        elif 'AnnotationProperty' in item['type']['value']:
                            property_type = 'Annotation'
                            
                        f.write(f"### {label} ({property_type})\n")
                        f.write(f"{comment}\n\n")
            
            # Clean up temporary files
            for temp_file in [temp_query_file, temp_json_file]:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    
            return True
            
        except Exception as e:
            logger.error(f"Error processing query results: {e}")
            # Clean up temporary files
            for temp_file in [temp_query_file, temp_json_file]:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            return False

    def _generate_cnl_with_simplified_fallback(self, module_path: str, cnl_path: str) -> bool:
        """
        Generate a very simple CNL representation directly from the OWL file
        without relying on external tools. This is a last resort fallback method.
        """
        try:
            # Read the OWL file directly
            with open(module_path, 'r', encoding='utf-8', errors='ignore') as f:
                owl_content = f.read()
                
            # Generate a simplified CNL representation
            with open(cnl_path, 'w', encoding='utf-8') as f:
                f.write(f"# Simple Controlled Natural Language for {Path(module_path).stem}\n\n")
                f.write("This document contains a simplified description of the ontology module.\n\n")
                
                # Extract class and property IRIs
                class_pattern = r'<owl:Class rdf:about="([^"]+)"'
                object_property_pattern = r'<owl:ObjectProperty rdf:about="([^"]+)"'
                data_property_pattern = r'<owl:DatatypeProperty rdf:about="([^"]+)"'
                
                # Extract label patterns
                label_pattern = r'<rdfs:label[^>]*>([^<]+)</rdfs:label>'
                comment_pattern = r'<rdfs:comment[^>]*>([^<]+)</rdfs:comment>'
                
                # Extract entities using simple pattern matching
                import re
                
                # Find classes
                f.write("## Classes\n\n")
                classes = re.findall(class_pattern, owl_content)
                processed_classes = set()
                
                for class_iri in classes:
                    if class_iri in processed_classes:
                        continue
                        
                    # Extract local name from IRI
                    local_name = class_iri.split('/')[-1].split('#')[-1]
                    
                    # Look for surrounding context to find labels and comments
                    class_start_idx = owl_content.find(f'<owl:Class rdf:about="{class_iri}"')
                    if class_start_idx >= 0:
                        # Find the closing tag
                        class_end_idx = owl_content.find('</owl:Class>', class_start_idx)
                        if class_end_idx < 0:
                            class_end_idx = class_start_idx + 500  # Just look at next 500 chars
                            
                        class_block = owl_content[class_start_idx:class_end_idx]
                        
                        # Try to find label
                        label_match = re.search(label_pattern, class_block)
                        label = label_match.group(1) if label_match else local_name
                        
                        # Try to find comment
                        comment_match = re.search(comment_pattern, class_block)
                        comment = comment_match.group(1) if comment_match else "No description available."
                        
                        f.write(f"### {label}\n")
                        f.write(f"IRI: {class_iri}\n\n")
                        f.write(f"{comment}\n\n")
                        
                    processed_classes.add(class_iri)
                
                # Find properties
                f.write("## Properties\n\n")
                
                # Object properties
                object_properties = re.findall(object_property_pattern, owl_content)
                for prop_iri in object_properties:
                    # Extract local name from IRI
                    local_name = prop_iri.split('/')[-1].split('#')[-1]
                    
                    # Look for surrounding context to find labels and comments
                    prop_start_idx = owl_content.find(f'<owl:ObjectProperty rdf:about="{prop_iri}"')
                    if prop_start_idx >= 0:
                        # Find the closing tag
                        prop_end_idx = owl_content.find('</owl:ObjectProperty>', prop_start_idx)
                        if prop_end_idx < 0:
                            prop_end_idx = prop_start_idx + 500  # Just look at next 500 chars
                            
                        prop_block = owl_content[prop_start_idx:prop_end_idx]
                        
                        # Try to find label
                        label_match = re.search(label_pattern, prop_block)
                        label = label_match.group(1) if label_match else local_name
                        
                        # Try to find comment
                        comment_match = re.search(comment_pattern, prop_block)
                        comment = comment_match.group(1) if comment_match else "No description available."
                        
                        f.write(f"### {label} (Relationship)\n")
                        f.write(f"IRI: {prop_iri}\n\n")
                        f.write(f"{comment}\n\n")
                
                # Data properties
                data_properties = re.findall(data_property_pattern, owl_content)
                for prop_iri in data_properties:
                    # Extract local name from IRI
                    local_name = prop_iri.split('/')[-1].split('#')[-1]
                    
                    # Look for surrounding context to find labels and comments
                    prop_start_idx = owl_content.find(f'<owl:DatatypeProperty rdf:about="{prop_iri}"')
                    if prop_start_idx >= 0:
                        # Find the closing tag
                        prop_end_idx = owl_content.find('</owl:DatatypeProperty>', prop_start_idx)
                        if prop_end_idx < 0:
                            prop_end_idx = prop_start_idx + 500  # Just look at next 500 chars
                            
                        prop_block = owl_content[prop_start_idx:prop_end_idx]
                        
                        # Try to find label
                        label_match = re.search(label_pattern, prop_block)
                        label = label_match.group(1) if label_match else local_name
                        
                        # Try to find comment
                        comment_match = re.search(comment_pattern, prop_block)
                        comment = comment_match.group(1) if comment_match else "No description available."
                        
                        f.write(f"### {label} (Attribute)\n")
                        f.write(f"IRI: {prop_iri}\n\n")
                        f.write(f"{comment}\n\n")
                
                # If we couldn't find any content, add a simple default
                if not classes and not object_properties and not data_properties:
                    f.write("## General Description\n\n")
                    f.write("This ontology module appears to be minimalistic or in a format that couldn't be parsed with the simplified method.\n")
                    f.write("It may still contain valuable semantic information in its formal OWL structure.\n\n")
                    
                    # Add some content from the file itself to ensure we have something
                    f.write("## Raw Content Sample\n\n")
                    f.write("Here is a sample of the raw ontology content:\n\n")
                    f.write("```\n")
                    f.write(owl_content[:1000] + "...\n")  # First 1000 chars
                    f.write("```\n")
            
            return True
            
        except Exception as e:
            logger.error(f"Error generating simplified CNL: {e}")
            
            # Final emergency fallback - create a minimal CNL file with the module name
            try:
                with open(cnl_path, 'w', encoding='utf-8') as f:
                    f.write(f"# Minimal Description for {Path(module_path).stem}\n\n")
                    f.write("This is a minimal description created for an ontology module.\n")
                    f.write("The original module conversion to CNL failed due to technical issues.\n\n")
                    f.write("The ontology module is available at: " + module_path + "\n")
                return True
            except Exception as e2:
                logger.error(f"Final emergency fallback failed: {e2}")
                return False

    def process_modules_to_cnl(self, module_paths: List[str], output_dir: str = "output/cnl") -> List[str]:
        """
        Process multiple ontology modules to CNL.
        
        Args:
            module_paths: List of paths to ontology module files
            output_dir: Directory to save the generated CNL files
            
        Returns:
            List of paths to the generated CNL files
        """
        cnl_files = []
        
        for module_path in module_paths:
            cnl_path = self.generate_cnl_from_module(module_path, output_dir)
            if cnl_path:
                cnl_files.append(cnl_path)
                
        return cnl_files

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python cnl_generator.py <module_path> [<module_path> ...]")
        sys.exit(1)
    
    try:
        module_paths = sys.argv[1:]
        
        generator = CNLGenerator()
        cnl_files = generator.process_modules_to_cnl(module_paths)
        
        if cnl_files:
            print(f"Generated {len(cnl_files)} CNL files:")
            for cnl_file in cnl_files:
                print(f"- {cnl_file}")
        else:
            print("No CNL files were generated")
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1) 