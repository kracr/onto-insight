#!/bin/bash

if [ $# -eq 0 ]; then
    echo "Error: Please provide the path to the input ontology file (.owl/.rdf) as an argument."
    exit 1
fi

INPUT_ONTOLOGY="$1"
JAR_FILE="target/calculation_engine-1.0-SNAPSHOT-jar-with-dependencies.jar"

if [ ! -f "$INPUT_ONTOLOGY" ]; then
    echo "Error: The specified input ontology file does not exist: $INPUT_ONTOLOGY"
    exit 1
fi

if [ ! -f "$JAR_FILE" ]; then
    echo "Error: JAR file not found. Please run './compile.sh' first."
    exit 1
fi

# Get base name of input file without extension
BASE_NAME=$(basename "$INPUT_ONTOLOGY" | sed 's/\.[^.]*$//')

# Checking file size and prompting user for choice
FILE_SIZE=$(stat -f%z "$INPUT_ONTOLOGY" 2>/dev/null || stat -c%s "$INPUT_ONTOLOGY")
MAX_SIZE=$((25 * 1024 * 1024))

echo "Please choose an option:"
echo "1. Evaluate full ontology (must be under 25MB)"
echo "2. Modularize ontology using ROBOT extraction"
read -p "Enter your choice (1 or 2): " choice

case $choice in
    1)
        if [ "$FILE_SIZE" -gt "$MAX_SIZE" ]; then
            echo "Error: Input ontology is larger than 25MB. Please use option 2 for large ontologies."
            exit 1
        fi
        # Converting to OFN format with consistent naming
        CONVERTED_OUTPUT="ontologies/${BASE_NAME}_converted.ofn"
        echo "Converting ontology to ofn format..."
        robot convert -i "$INPUT_ONTOLOGY" -o "$CONVERTED_OUTPUT"

        echo "Running Main (OQuaRE scoring) on full ontology..."
        java -cp "$JAR_FILE" com.calculation_engine.Main "$CONVERTED_OUTPUT"

        METRICS_JSON="${CONVERTED_OUTPUT}_metrics.json"

        if [ -f "$METRICS_JSON" ]; then
            echo "Generating verbalized axioms..."
            python3 verbal.py "$CONVERTED_OUTPUT"
            VERBALIZED_OUTPUT="${CONVERTED_OUTPUT%.*}_verbalized.txt"
            
            if [ -f "$VERBALIZED_OUTPUT" ]; then
                echo "Running LLM analysis with verbalized axioms..."
                python3 src/llm/app.py "$CONVERTED_OUTPUT" "$METRICS_JSON" "$VERBALIZED_OUTPUT"
            else
                echo "Error: Verbalized output not found at $VERBALIZED_OUTPUT"
                exit 1
            fi
        else
            echo "Error: Metrics file not found at $METRICS_JSON"
            exit 1
        fi
        ;;
    2)
        # Get extraction parameters from user
        echo "The seed term is the term you want to extract modules from the ontology."
        read -p "Enter the IRI for your seed term: " TERM_IRI

        echo "Available extraction methods:"
        echo "1. TOP (upper module) - Default"
        echo "2. BOT (lower module)"
        echo "3. STAR (star module)"
        echo "4. MIREOT"
        read -p "Choose extraction method (1-4) [Press Enter for default TOP]: " METHOD_CHOICE

        if [ -z "$METHOD_CHOICE" ]; then
            METHOD="top"
            echo "Using default TOP extraction method"
        else
            case $METHOD_CHOICE in
                1) METHOD="top";;
                2) METHOD="bot";;
                3) METHOD="star";;
                4) METHOD="mireot";;
                *)
                    echo "Invalid choice, using default TOP extraction method"
                    METHOD="top"
                    ;;
            esac
        fi

        # Use consistent naming for modular output
        ROBOT_OUTPUT="ontologies/${BASE_NAME}_module.owl"
        CONVERTED_OUTPUT="ontologies/${BASE_NAME}_module_converted.ofn"

        echo "Starting ROBOT module extraction..."
        robot extract --method "$METHOD" \
            --input "$INPUT_ONTOLOGY" \
            --term "$TERM_IRI" \
            --output "$ROBOT_OUTPUT"
        echo "ROBOT extraction complete."

        echo "Converting ontology to ofn format..."
        robot convert -i "$ROBOT_OUTPUT" -o "$CONVERTED_OUTPUT"

        echo "Running Main (OQuaRE scoring)..."
        java -cp "$JAR_FILE" com.calculation_engine.Main "$CONVERTED_OUTPUT"

        # Use the correct metrics file name that matches the converted module
        METRICS_JSON="${CONVERTED_OUTPUT}_metrics.json"

        if [ -f "$METRICS_JSON" ]; then
            echo "Generating verbalized axioms..."
            python3 verbal.py "$CONVERTED_OUTPUT"
            VERBALIZED_OUTPUT="${CONVERTED_OUTPUT%.*}_verbalized.txt"
            
            if [ -f "$VERBALIZED_OUTPUT" ]; then
                echo "Running LLM analysis with verbalized axioms..."
                python3 src/llm/app.py "$CONVERTED_OUTPUT" "$METRICS_JSON" "$VERBALIZED_OUTPUT"
            else
                echo "Error: Verbalized output not found at $VERBALIZED_OUTPUT"
                exit 1
            fi
        else
            echo "Error: Metrics file not found at $METRICS_JSON"
            exit 1
        fi
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo "Process completed..."