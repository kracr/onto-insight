#!/bin/bash

# Check if Python dependencies are installed
pip3 install -r requirements_api.txt

# Set up directories
mkdir -p output
mkdir -p output/ontologies
mkdir -p output/ontologies/seed_terms
mkdir -p output/ontologies/modules
mkdir -p output/cnl
mkdir -p output/reports
mkdir -p temp

# Run path fix script to ensure all directories exist
echo "Running path check and fix..."
python3 fix_paths.py

# Set environment variables
export PYTHONPATH="$PYTHONPATH:$(pwd)"

# Check if JAR file exists
JAR_FILE="target/calculation_engine-1.0-SNAPSHOT-jar-with-dependencies.jar"
if [ ! -f "$JAR_FILE" ]; then
    echo "Error: JAR file not found at $JAR_FILE"
    exit 1
fi

# Check for API key
if [ -z "$OPENAI_API_KEY" ] && [ ! -f .env ]; then
    echo "Warning: OPENAI_API_KEY not found in environment or .env file"
    echo "You will need to add this to use the recommendation features."
    echo "Creating sample .env file..."
    echo "OPENAI_API_KEY=your_key_here" > .env
fi

# Start the Flask API
echo "Starting the Ontology Evaluation API server..."
flask --app api run --host=0.0.0.0 --port=8000
