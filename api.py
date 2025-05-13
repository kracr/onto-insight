import os
import json
import tempfile
import logging
import subprocess
from pathlib import Path
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from src.basic_recom import BasicRecommendations
from src.adv_recom import AdvancedRecommendations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("ontology-api")

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024  # 25MB max file size

# Configure paths
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR = BASE_DIR / "temp"
JAR_FILE = BASE_DIR / "target" / "calculation_engine-1.0-SNAPSHOT-jar-with-dependencies.jar"
METRICS_DIR = BASE_DIR / "metrics"

# Create necessary directories
OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)
(OUTPUT_DIR / "ontologies").mkdir(exist_ok=True)
(OUTPUT_DIR / "ontologies" / "seed_terms").mkdir(exist_ok=True)
(OUTPUT_DIR / "ontologies" / "modules").mkdir(exist_ok=True)
(OUTPUT_DIR / "cnl").mkdir(exist_ok=True)
(OUTPUT_DIR / "reports").mkdir(exist_ok=True)

# Set environment variables
os.environ['OQUARE_METRICS_PATH'] = str(METRICS_DIR / "oquare_metrics.csv")
os.environ['METRICS_DESCRIPTIONS_PATH'] = str(METRICS_DIR / "framework_metrics_descriptions.csv")
os.environ['OQUARE_OUTPUT_DIR'] = str(OUTPUT_DIR)

# Utility functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'owl', 'rdf', 'ttl'}

def preprocess_ontology(file_path):
    """Preprocess the ontology file and return the paths to the converted ontology"""
    try:
        # Get base name of input file without extension
        base_name = os.path.basename(file_path).rsplit('.', 1)[0]
        
        # Define standardized paths for all output files
        converted_ontology = str(OUTPUT_DIR / "ontologies" / f"{base_name}_converted.owl")
        
        # Copy input file to output directory if it's already an OWL file
        if file_path.endswith('.owl'):
            logger.info("Input file is already in OWL format. Copying to output directory...")
            subprocess.run(['cp', file_path, converted_ontology], check=True)
        else:
            logger.info("Converting input file to OWL format...")
            subprocess.run(['cp', file_path, converted_ontology], check=True)
            
        return {
            'converted_ontology': converted_ontology,
            'base_name': base_name
        }
    except Exception as e:
        logger.error(f"Error preprocessing ontology: {str(e)}")
        raise

def run_oquare_scoring(ontology_path):
    """Run OQuaRE scoring on the ontology"""
    try:
        logger.info(f"Running OQuaRE scoring on {ontology_path}")
        result = subprocess.run(
            ['java', '-cp', str(JAR_FILE), 'com.calculation_engine.Main', ontology_path],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(f"OQuaRE scoring output: {result.stdout}")
        
        # The metrics file should be created with a _metrics.json suffix
        metrics_file = f"{ontology_path}_metrics.json"
        
        if not os.path.exists(metrics_file):
            logger.error(f"Metrics file not created at {metrics_file}")
            raise FileNotFoundError(f"Metrics file not created at {metrics_file}")
        
        return metrics_file
    except subprocess.CalledProcessError as e:
        logger.error(f"OQuaRE scoring failed: {e.stderr}")
        raise
    except Exception as e:
        logger.error(f"Error running OQuaRE scoring: {str(e)}")
        raise

def extract_seed_terms(ontology_path, metrics_file, base_name):
    """Extract seed terms from ontology based on metrics"""
    try:
        seed_terms_json = str(OUTPUT_DIR / "ontologies" / "seed_terms" / f"{base_name}_seed_terms.json")
        
        logger.info(f"Extracting seed terms from ontology based on worst metrics...")
        subprocess.run(
            ['python3', str(BASE_DIR / 'src' / 'seed_terms_selector.py'), 
             ontology_path, metrics_file, seed_terms_json],
            check=True
        )
        
        if not os.path.exists(seed_terms_json):
            logger.error(f"Seed terms file not created at {seed_terms_json}")
            raise FileNotFoundError(f"Seed terms file not created at {seed_terms_json}")
        
        return seed_terms_json
    except Exception as e:
        logger.error(f"Error extracting seed terms: {str(e)}")
        raise

def generate_cnl(ontology_path, base_name):
    """Generate controlled natural language representation"""
    try:
        logger.info(f"Generating CNL for {ontology_path}")
        subprocess.run(
            ['python3', str(BASE_DIR / 'src' / 'owl_to_cnl.py'), ontology_path],
            check=True
        )
        
        # Check if CNL file exists in expected location
        cnl_file = f"{os.path.splitext(ontology_path)[0]}.txt"
        cnl_output = str(OUTPUT_DIR / "cnl" / f"{base_name}.txt")
        
        if os.path.exists(cnl_file):
            # Copy to standard location
            subprocess.run(['cp', cnl_file, cnl_output], check=True)
            
            # Optionally remove the original if it's not in the output directory
            if cnl_file != cnl_output:
                os.remove(cnl_file)
        else:
            # Generate a basic fallback CNL
            logger.warning(f"CNL file not generated at {cnl_file}. Creating fallback CNL.")
            with open(cnl_output, 'w') as f:
                f.write("# Simple Ontology Description\n\n")
                f.write("This is a basic description of the ontology.\n\n")
                f.write("## Sample Terms\n\n")
                
                # Extract some content from the ontology file
                with open(ontology_path, 'r') as onto_file:
                    content = onto_file.read()
                    import re
                    classes = re.findall(r'Class rdf:about="([^"]*)"', content)
                    for i, class_uri in enumerate(classes[:20]):
                        local_name = class_uri.split('/')[-1].split('#')[-1]
                        f.write(f"- {local_name}\n")
        
        return cnl_output
    except Exception as e:
        logger.error(f"Error generating CNL: {str(e)}")
        raise

# API endpoints
@app.route('/api/health', methods=['GET'])
def health_check():
    """API health check endpoint"""
    return jsonify({
        'status': 'ok',
        'message': 'Ontology evaluation API is running'
    })

@app.route('/api/evaluate-full', methods=['POST'])
def evaluate_full_ontology():
    """Evaluate a full ontology with either basic or advanced recommendations"""
    try:
        # Check if ontology file was uploaded
        if 'ontology' not in request.files:
            return jsonify({'error': 'No ontology file provided'}), 400
            
        file = request.files['ontology']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
            
        if not allowed_file(file.filename):
            return jsonify({'error': 'File format not supported. Use .owl, .rdf, or .ttl'}), 400
        
        # Get recommendation mode
        mode = request.form.get('mode', 'basic')
        if mode not in ['basic', 'advanced']:
            return jsonify({'error': 'Invalid mode. Use "basic" or "advanced"'}), 400
        
        # Save uploaded file to temporary location
        temp_file_path = os.path.join(TEMP_DIR, secure_filename(file.filename))
        file.save(temp_file_path)
        
        # Process the ontology
        process_result = preprocess_ontology(temp_file_path)
        converted_ontology = process_result['converted_ontology']
        base_name = process_result['base_name']
        
        # Run OQuaRE scoring
        metrics_file = run_oquare_scoring(converted_ontology)
        
        # Extract seed terms
        seed_terms_file = extract_seed_terms(converted_ontology, metrics_file, base_name)
        
        # Generate CNL
        cnl_file = generate_cnl(converted_ontology, base_name)
        
        # Read the necessary files
        with open(cnl_file, 'r', encoding='utf-8') as f:
            cnl_text = f.read()
            
        with open(metrics_file, 'r', encoding='utf-8') as f:
            metrics_data = f.read()
        
        # Generate recommendations based on mode
        if mode == 'basic':
            try:
                recommender = BasicRecommendations()
                result, report_path = recommender.generate_basic_recommendations(cnl_text, metrics_data, seed_terms_file)
            except Exception as rec_error:
                logger.error(f"Basic recommendation generation error: {str(rec_error)}")
                return jsonify({
                    'status': 'error',
                    'message': f"Error generating basic recommendations: {str(rec_error)}"
                }), 500
        else:
            try:
                recommender = AdvancedRecommendations()
                result, report_path = recommender.generate_advanced_recommendations(cnl_text, metrics_data, seed_terms_file)
            except Exception as rec_error:
                logger.error(f"Advanced recommendation generation error: {str(rec_error)}")
                return jsonify({
                    'status': 'error',
                    'message': f"Error generating advanced recommendations: {str(rec_error)}"
                }), 500
        
        # Read the generated report
        with open(report_path, 'r', encoding='utf-8') as f:
            report_content = f.read()
        
        # Read metrics and seed terms for response
        with open(metrics_file, 'r', encoding='utf-8') as f:
            metrics_content = json.load(f)
        
        with open(seed_terms_file, 'r', encoding='utf-8') as f:
            seed_terms_content = json.load(f)
        
        # Clean up temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        return jsonify({
            'status': 'success',
            'mode': mode,
            'base_name': base_name,
            'report': report_content,
            'metrics': metrics_content,
            'seed_terms': seed_terms_content,
            'cnl': cnl_text
        })
    
    except Exception as e:
        logger.error(f"Error in evaluate_full_ontology: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/evaluate-modular', methods=['POST'])
def evaluate_modular_ontology():
    """Evaluate an ontology with modularization approach"""
    try:
        # Check if ontology file was uploaded
        if 'ontology' not in request.files:
            return jsonify({'error': 'No ontology file provided'}), 400
            
        file = request.files['ontology']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
            
        if not allowed_file(file.filename):
            return jsonify({'error': 'File format not supported. Use .owl, .rdf, or .ttl'}), 400
        
        # Get recommendation mode
        mode = request.form.get('mode', 'basic')
        if mode not in ['basic', 'advanced']:
            return jsonify({'error': 'Invalid mode. Use "basic" or "advanced"'}), 400
        
        # Save uploaded file to temporary location
        temp_file_path = os.path.join(TEMP_DIR, secure_filename(file.filename))
        file.save(temp_file_path)
        
        # Process the ontology
        process_result = preprocess_ontology(temp_file_path)
        converted_ontology = process_result['converted_ontology']
        base_name = process_result['base_name']
        
        # Run OQuaRE scoring
        metrics_file = run_oquare_scoring(converted_ontology)
        
        # Extract seed terms
        seed_terms_file = extract_seed_terms(converted_ontology, metrics_file, base_name)
        
        # Generate CNL for backup/reference
        cnl_file = generate_cnl(converted_ontology, base_name)
        
        # Run the modular recommendation workflow
        logger.info(f"Running modular recommendation workflow with mode: {mode}")
        result = subprocess.run(
            ['python3', str(BASE_DIR / 'src' / 'modular_recommendation.py'),
             converted_ontology, metrics_file, seed_terms_file, '--mode', mode],
            capture_output=True,
            text=True
        )
        
        # Check for modules
        modules_dir = OUTPUT_DIR / "ontologies" / "modules"
        module_files = list(modules_dir.glob("*.owl"))
        
        # Collect all recommendation files
        recommendation_files = list((OUTPUT_DIR / "reports").glob(f"*{base_name}*recommendations*.txt"))
        recommendation_files.extend(list((OUTPUT_DIR / "reports").glob(f"*{base_name}*recommendations*.md")))
        
        # Read all recommendation files
        recommendations = []
        for rec_file in recommendation_files:
            with open(rec_file, 'r', encoding='utf-8') as f:
                recommendations.append({
                    'filename': rec_file.name,
                    'content': f.read()
                })
        
        # Read metrics and seed terms for response
        with open(metrics_file, 'r', encoding='utf-8') as f:
            metrics_content = json.load(f)
        
        with open(seed_terms_file, 'r', encoding='utf-8') as f:
            seed_terms_content = json.load(f)
            
        with open(cnl_file, 'r', encoding='utf-8') as f:
            cnl_text = f.read()
        
        # Clean up temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        return jsonify({
            'status': 'success',
            'mode': mode,
            'base_name': base_name,
            'modules_created': len(module_files) > 0,
            'module_count': len(module_files),
            'module_names': [m.name for m in module_files],
            'recommendations': recommendations,
            'metrics': metrics_content,
            'seed_terms': seed_terms_content,
            'cnl': cnl_text
        })
    
    except Exception as e:
        logger.error(f"Error in evaluate_modular_ontology: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
