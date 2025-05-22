#!/bin/bash

# Define colors and formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
UNDERLINE='\033[4m'
RESET='\033[0m'

# Summary tracking variables - use simple variables instead of associative array
CONVERTED_ONTOLOGY=""
METRICS_JSON=""
SEED_TERMS=""
CNL_OUTPUT=""
MODULE=""
MODULE_METRICS=""
MODULE_CNL=""
RECOMMENDATIONS=""

# Functions for formatted output
print_header() {
    echo -e "\n${BOLD}${BLUE}=== $1 ===${RESET}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${RESET}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${RESET}"
}

print_error() {
    echo -e "${RED}✗ $1${RESET}"
}

print_progress() {
    echo -e "${CYAN}→ $1${RESET}"
}

print_step() {
    echo -e "${MAGENTA}[STEP $1]${RESET} $2"
}

print_api_status() {
    echo -e "${CYAN}[API]${RESET} $1"
}

print_table() {
    # Prints a formatted table from key-value pairs
    echo -e "${BOLD}${UNDERLINE}$1:${RESET}"
    shift
    while [ $# -gt 0 ]; do
        key=$1
        value=$2
        printf "  ${BOLD}%-24s${RESET} : %s\n" "$key" "$value"
        shift 2
    done
}

# Keep track of outputs for final summary
track_output() {
    case "$1" in
        "Converted Ontology") CONVERTED_ONTOLOGY="$2" ;;
        "Metrics JSON") METRICS_JSON="$2" ;;
        "Seed Terms") SEED_TERMS="$2" ;;
        "CNL Output") CNL_OUTPUT="$2" ;;
        "Module") MODULE="$2" ;;
        "Module Metrics") MODULE_METRICS="$2" ;;
        "Module CNL") MODULE_CNL="$2" ;;
        "Recommendations") RECOMMENDATIONS="$2" ;;
        *) echo "Unknown output type: $1" ;;
    esac
}

# Check if JAR file path and input ontology are provided
if [ $# -lt 1 ]; then
    print_error "Usage: $0 <path_to_input_ontology> [FULL|MOD] [BASIC|ADVANCED]"
    echo "Examples:"
    echo "  $0 ./my_ontology.owl                          # Interactive mode"
    echo "  $0 ./my_ontology.owl FULL BASIC              # Full ontology evaluation with basic mode"
    echo "  $0 ./my_ontology.owl FULL ADVANCED           # Full ontology evaluation with advanced mode"
    echo "  $0 ./my_ontology.owl MOD BASIC               # Modular evaluation with basic mode"
    echo "  $0 ./my_ontology.owl MOD ADVANCED            # Modular evaluation with advanced mode"
    exit 1
fi

JAR_FILE="target/calculation_engine-1.0-SNAPSHOT-jar-with-dependencies.jar"
INPUT_ONTOLOGY="$1"
OUTPUT_DIR="./output"  # Fixed output directory

# Handle command line evaluation options if provided
if [ $# -eq 3 ]; then
    # Convert to uppercase using tr instead of ${var^^}
    EVAL_OPTION=$(echo "$2" | tr '[:lower:]' '[:upper:]')
    MODE=$(echo "$3" | tr '[:lower:]' '[:upper:]')
    
    # Validate evaluation option
    if [ "$EVAL_OPTION" != "FULL" ] && [ "$EVAL_OPTION" != "MOD" ]; then
        print_error "Invalid evaluation option. Use FULL or MOD"
        exit 1
    fi
    
    # Validate mode
    if [ "$MODE" != "BASIC" ] && [ "$MODE" != "ADVANCED" ]; then
        print_error "Invalid mode. Use BASIC or ADVANCED"
        exit 1
    fi
    
    # Set choice based on evaluation option
    case "$EVAL_OPTION" in
        "FULL") choice="1" ;;
        "MOD")  choice="2" ;;
    esac
    
    # Set recommendation choice based on mode
    case "$MODE" in
        "BASIC")    rec_choice="1" ;;
        "ADVANCED") rec_choice="2" ;;
    esac
fi

# Validate inputs
if [ ! -f "$JAR_FILE" ]; then
    print_error "JAR file not found at $JAR_FILE"
    exit 1
fi

if [ ! -f "$INPUT_ONTOLOGY" ]; then
    print_error "Input ontology file not found at $INPUT_ONTOLOGY"
    exit 1
fi

# Set up absolute paths to metrics files
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
export OQUARE_METRICS_PATH="$SCRIPT_DIR/metrics/oquare_metrics.csv"
export METRICS_DESCRIPTIONS_PATH="$SCRIPT_DIR/metrics/framework_metrics_descriptions.csv"

# Validate metrics files
if [ ! -f "$OQUARE_METRICS_PATH" ]; then
    print_error "OQuaRE metrics file not found at $OQUARE_METRICS_PATH"
    exit 1
fi

if [ ! -f "$METRICS_DESCRIPTIONS_PATH" ]; then
    print_error "Metrics descriptions file not found at $METRICS_DESCRIPTIONS_PATH"
    exit 1
fi

# Create output directory structure
mkdir -p "$OUTPUT_DIR/ontologies"
mkdir -p "$OUTPUT_DIR/ontologies/seed_terms"
mkdir -p "$OUTPUT_DIR/ontologies/modules"
mkdir -p "$OUTPUT_DIR/cnl"
mkdir -p "$OUTPUT_DIR/reports"

# Get base name of input file without extension
BASE_NAME=$(basename "$INPUT_ONTOLOGY" | sed 's/\.[^.]*$//')

# Define standardized paths for all output files
CONVERTED_ONTOLOGY="$OUTPUT_DIR/ontologies/${BASE_NAME}_converted.owl"
METRICS_JSON="$OUTPUT_DIR/ontologies/${BASE_NAME}_metrics.json"
SEED_TERMS_JSON="$OUTPUT_DIR/ontologies/seed_terms/${BASE_NAME}_seed_terms.json"
CNL_OUTPUT="$OUTPUT_DIR/cnl/${BASE_NAME}.txt"

# Set environment variables for output locations
export OQUARE_OUTPUT_DIR="$OUTPUT_DIR"
export PYTHONPATH="$PYTHONPATH:$SCRIPT_DIR"

# Copy input file to output directory if it's already an OWL file
if [[ "$INPUT_ONTOLOGY" == *.owl ]]; then
    print_progress "Input file is already in OWL format. Copying to output directory..."
    cp "$INPUT_ONTOLOGY" "$CONVERTED_ONTOLOGY"
else
    print_progress "Converting input file to OWL format..."
    cp "$INPUT_ONTOLOGY" "$CONVERTED_ONTOLOGY"
fi
track_output "Converted Ontology" "$CONVERTED_ONTOLOGY"

# Add cleanup function
cleanup_and_move_files() {
    # Move ONLY metrics and CNL files to their proper directories
    # Don't move recommendation files as they should be directly saved to output/reports
    find . -maxdepth 1 -type f -name "*metrics.json" ! -path "./output/*" -exec mv {} "$OUTPUT_DIR/ontologies/" \;
    find . -maxdepth 1 -type f -name "*.txt" ! -name "*recommendation*" ! -name "requirements.txt" ! -path "./output/*" -exec mv {} "$OUTPUT_DIR/cnl/" \;
    find . -maxdepth 1 -type f -name "*.owl" ! -path "./output/*" -exec mv {} "$OUTPUT_DIR/ontologies/" \;
    
    # Clean up any remaining JSON files in the root directory
    find . -maxdepth 1 -type f -name "*.json" ! -path "./output/*" -exec mv {} "$OUTPUT_DIR/" \;
}

# Add trap to ensure cleanup happens on exit
trap cleanup_and_move_files EXIT

# Checking file size
FILE_SIZE=$(stat -f%z "$INPUT_ONTOLOGY" 2>/dev/null || stat -c%s "$INPUT_ONTOLOGY")
MAX_SIZE=$((25 * 1024 * 1024))

if [ "$FILE_SIZE" -gt "$MAX_SIZE" ]; then
    print_warning "Input ontology is larger than 25MB. Processing may take longer."
fi

# Only show options and ask for input if choice wasn't set via command line
if [ -z "$choice" ]; then
    print_header "ONTOLOGY EVALUATION OPTIONS"
    echo -e "${BOLD}1.${RESET} Evaluate full ontology"
    echo -e "${BOLD}2.${RESET} Modularize ontology (for large ontologies)"
    read -p "$(echo -e "${BOLD}Enter your choice (1 or 2):${RESET} ")" choice
fi

case $choice in
    1)
        print_step "1" "Running OQuaRE scoring on full ontology"
        java -cp "$JAR_FILE" com.calculation_engine.Main "$CONVERTED_ONTOLOGY" > /dev/null 2>&1
        
        # Check if metrics file was created
        ACTUAL_METRICS_JSON="${CONVERTED_ONTOLOGY}_metrics.json"
        if [ -f "$ACTUAL_METRICS_JSON" ]; then
            # Copy metrics file to standardized location if needed
            if [ "$ACTUAL_METRICS_JSON" != "$METRICS_JSON" ]; then
                cp "$ACTUAL_METRICS_JSON" "$METRICS_JSON"
            fi
            print_success "Metrics generated successfully"
            track_output "Metrics JSON" "$METRICS_JSON"
            
            # Generate seed terms based on worst metrics and save to JSON
            print_step "2" "Extracting seed terms from ontology based on worst metrics"
            python3 src/seed_terms_selector.py "$CONVERTED_ONTOLOGY" "$METRICS_JSON" "$SEED_TERMS_JSON" > /dev/null 2>&1
            
            if [ -f "$SEED_TERMS_JSON" ]; then
                print_success "Seed terms extracted successfully"
                track_output "Seed Terms" "$SEED_TERMS_JSON"
                
                # Generate CNL
                print_step "3" "Generating controlled natural language (CNL) representation"
                mkdir -p "$OUTPUT_DIR/cnl"  # Ensure CNL directory exists
                python3 src/owl_to_cnl.py "$CONVERTED_ONTOLOGY" > /dev/null 2>&1
                
                # Check if CNL file exists in expected location
                GENERATED_CNL="${CONVERTED_ONTOLOGY%.*}.txt"
                if [ -f "$GENERATED_CNL" ]; then
                    # Copy to standard location
                    cp "$GENERATED_CNL" "$CNL_OUTPUT"
                    # Optionally remove the original if it's not in the output directory
                    if [[ "$GENERATED_CNL" != "$CNL_OUTPUT" ]]; then
                        rm "$GENERATED_CNL"
                    fi
                    print_success "CNL generated successfully"
                    track_output "CNL Output" "$CNL_OUTPUT"
                else
                    print_warning "CNL file not generated at expected location. Creating fallback."
                    # Try to generate a basic CNL file for fallback
                    echo "# Simple Ontology Description" > "$CNL_OUTPUT"
                    echo "" >> "$CNL_OUTPUT"
                    echo "This is a basic description of the ontology." >> "$CNL_OUTPUT"
                    echo "" >> "$CNL_OUTPUT"
                    
                    # Extract some content from the ontology file
                    echo "## Sample Terms" >> "$CNL_OUTPUT"
                    echo "" >> "$CNL_OUTPUT"
                    
                    # Extract class names or terms using grep
                    grep -o 'Class rdf:about="[^"]*"' "$CONVERTED_ONTOLOGY" | sed 's/.*about="\([^"]*\)".*/\1/' | head -n 20 | while read -r line; do
                        local_name=$(echo "$line" | awk -F'[/#]' '{print $NF}')
                        echo "- $local_name" >> "$CNL_OUTPUT"
                    done
                    
                    track_output "CNL Output (Fallback)" "$CNL_OUTPUT"
                fi
                
                # Only show options and ask for input if rec_choice wasn't set via command line
                if [ -z "$rec_choice" ]; then
                    print_header "RECOMMENDATION MODE"
                    echo -e "${BOLD}1.${RESET} BASIC - Easy to understand overview recommendations"
                    echo -e "${BOLD}2.${RESET} ADVANCED - Detailed technical recommendations for ontology experts"
                    read -p "$(echo -e "${BOLD}Enter your choice (1 or 2):${RESET} ")" rec_choice
                fi
                
                case $rec_choice in
                    1)
                        print_step "4" "Generating basic recommendations"
                        print_progress "Starting to generate basic recommendations..."
                        REPORT_FILE="$OUTPUT_DIR/reports/${BASE_NAME}_basic_recommendations.md"
                        python3 src/basic_recom.py "$CNL_OUTPUT" "$METRICS_JSON" "$SEED_TERMS_JSON" "$REPORT_FILE" > /dev/null 2>&1
                        
                        # Verify the file exists
                        if [ -f "$REPORT_FILE" ]; then
                            print_success "Basic recommendations generated"
                            track_output "Recommendations" "$REPORT_FILE"
                        else
                            # Check for .md extension as the scripts now save with .md
                            MD_REPORT_FILE="${REPORT_FILE%.txt}.md"
                            if [ -f "$MD_REPORT_FILE" ]; then
                                print_success "Basic recommendations generated"
                                track_output "Recommendations" "$MD_REPORT_FILE"
                                REPORT_FILE="$MD_REPORT_FILE"
                            else
                                print_error "Report was not saved to $REPORT_FILE, check for errors"
                                track_output "ERROR: Recommendations" "Failed to generate"
                            fi
                        fi
                        ;;
                    2)
                        print_step "4" "Generating advanced technical recommendations"
                        print_progress "Starting API request to generate recommendations..."
                        REPORT_FILE="$OUTPUT_DIR/reports/${BASE_NAME}_advanced_recommendations.md"
                        
                        # Run the Python script and capture its output
                        API_OUTPUT=$(python3 src/adv_recom.py "$CNL_OUTPUT" "$METRICS_JSON" "$SEED_TERMS_JSON" --output-dir "$OUTPUT_DIR/reports" --output-file "$REPORT_FILE" < /dev/null 2>&1)
                        API_STATUS=$?

                        if [ $API_STATUS -eq 0 ]; then
                            print_api_status "API request completed successfully"
                            if [ -f "$REPORT_FILE" ]; then
                                print_success "Advanced recommendations generated"
                                track_output "Recommendations" "$REPORT_FILE"
                            else
                                # Check for .md extension as the scripts now save with .md
                                MD_REPORT_FILE="${REPORT_FILE%.txt}.md"
                                if [ -f "$MD_REPORT_FILE" ]; then
                                    print_success "Advanced recommendations generated" 
                                    track_output "Recommendations" "$MD_REPORT_FILE"
                                    REPORT_FILE="$MD_REPORT_FILE"
                                else
                                    print_error "Report was not saved to $REPORT_FILE"
                                    print_error "API Output: $API_OUTPUT"
                                    track_output "ERROR: Recommendations" "Failed to generate"
                                fi
                            fi
                        else
                            print_error "API request failed with status $API_STATUS"
                            print_error "API Output: $API_OUTPUT"
                            track_output "ERROR: Recommendations" "Failed to generate"
                        fi
                        ;;
                    *)
                        print_warning "Invalid choice, generating basic recommendations by default"
                        print_progress "Starting to generate default basic recommendations..."
                        REPORT_FILE="$OUTPUT_DIR/reports/${BASE_NAME}_basic_recommendations.md"
                        python3 src/basic_recom.py "$CNL_OUTPUT" "$METRICS_JSON" "$SEED_TERMS_JSON" "$REPORT_FILE" > /dev/null 2>&1
                        if [ -f "$REPORT_FILE" ]; then
                            print_success "Basic recommendations generated"
                            track_output "Recommendations" "$REPORT_FILE"
                        else
                            track_output "Recommendations" "Failed to generate"
                        fi
                        ;;
                esac
            else
                print_error "Seed terms file was not created at $SEED_TERMS_JSON"
                exit 1
            fi
        else
            print_error "Metrics file was not created"
            exit 1
        fi
        ;;
    2)
        print_step "1" "Running OQuaRE scoring and preparing for modularization"
        java -cp "$JAR_FILE" com.calculation_engine.Main "$CONVERTED_ONTOLOGY" > /dev/null 2>&1
        
        # Java outputs the metrics file with a _metrics.json suffix
        ACTUAL_METRICS_JSON="${CONVERTED_ONTOLOGY}_metrics.json"
        
        # Copy metrics file to standardized location if needed
        if [ -f "$ACTUAL_METRICS_JSON" ] && [ "$ACTUAL_METRICS_JSON" != "$METRICS_JSON" ]; then
            cp "$ACTUAL_METRICS_JSON" "$METRICS_JSON"
        fi

        # Check if metrics file was created
        if [ ! -f "$METRICS_JSON" ]; then
            print_error "Metrics file was not created at $METRICS_JSON"
            exit 1
        fi
        print_success "Metrics generated successfully"
        track_output "Metrics JSON" "$METRICS_JSON"

        # Generate seed terms based on worst metrics and save to JSON
        print_step "2" "Extracting seed terms from ontology based on worst metrics"
        python3 src/seed_terms_selector.py "$CONVERTED_ONTOLOGY" "$METRICS_JSON" "$SEED_TERMS_JSON" > /dev/null 2>&1

        if [ -f "$METRICS_JSON" ] && [ -f "$SEED_TERMS_JSON" ]; then
            print_success "Seed terms extracted successfully"
            track_output "Seed Terms" "$SEED_TERMS_JSON"
            
            # Create modules directory
            MODULES_DIR="$OUTPUT_DIR/ontologies/modules"
            mkdir -p "$MODULES_DIR"
            
            # Extract module using ROBOT
            print_step "3" "Extracting ontology module"
            BASE_NAME=$(basename "$INPUT_ONTOLOGY" | sed 's/\.[^.]*$//' | sed 's/_converted//')
            MODULE_PATH="$MODULES_DIR/${BASE_NAME}_module.owl"
            python3 src/module_extractor.py "$CONVERTED_ONTOLOGY" "$METRICS_JSON" "$SEED_TERMS_JSON" > /dev/null 2>&1

            if [ ! -f "$MODULE_PATH" ]; then
                print_error "Module extraction failed. Module file not found at $MODULE_PATH"
                exit 1
            fi
            print_success "Module extracted successfully"
            track_output "Module" "$MODULE_PATH"
            
            # Recalculate metrics on the extracted module
            print_step "4" "Calculating metrics for the extracted module"
            java -cp "$JAR_FILE" com.calculation_engine.Main "$MODULE_PATH" > /dev/null 2>&1
            MODULE_METRICS="${MODULE_PATH}_metrics.json"
            
            if [ ! -f "$MODULE_METRICS" ]; then
                print_error "Module metrics calculation failed"
                exit 1
            fi
            print_success "Module metrics calculated successfully"
            track_output "Module Metrics" "$MODULE_METRICS"
            
            # Generate CNL for the module
            print_step "5" "Generating CNL for the module"
            python3 src/owl_to_cnl.py "$MODULE_PATH" > /dev/null 2>&1
            MODULE_CNL="${MODULE_PATH%.*}.txt"
            print_success "Module CNL generated successfully"
            track_output "Module CNL" "$MODULE_CNL"
            
            # Only show options and ask for input if rec_choice wasn't set via command line
            if [ -z "$rec_choice" ]; then
                print_header "RECOMMENDATION MODE"
                echo -e "${BOLD}1.${RESET} BASIC - Easy to understand overview recommendations"
                echo -e "${BOLD}2.${RESET} ADVANCED - Detailed technical recommendations for ontology experts"
                read -p "$(echo -e "${BOLD}Enter your choice (1 or 2):${RESET} ")" rec_choice
            fi
            
            # Generate recommendations based on the module
            case $rec_choice in
                1)
                    print_step "6" "Generating basic recommendations for module"
                    print_progress "Starting to generate basic recommendations for module..."
                    REPORT_FILE="$OUTPUT_DIR/reports/module_basic_recommendations.md"
                    python3 src/basic_recom.py "$MODULE_CNL" "$MODULE_METRICS" "$SEED_TERMS_JSON" "$REPORT_FILE" > /dev/null 2>&1
                    if [ -f "$REPORT_FILE" ]; then
                        print_success "Basic recommendations for module generated"
                        track_output "Recommendations" "$REPORT_FILE"
                    else
                        print_error "Failed to generate basic recommendations for module"
                        track_output "ERROR: Recommendations" "Failed to generate"
                    fi
                    ;;
                2)
                    print_step "6" "Generating advanced recommendations for module"
                    print_progress "Starting to generate advanced recommendations for module..."
                    REPORT_FILE="$OUTPUT_DIR/reports/module_advanced_recommendations.md"
                    python3 src/adv_recom.py "$MODULE_CNL" "$MODULE_METRICS" "$SEED_TERMS_JSON" --output-dir "$OUTPUT_DIR/reports" --output-file "$REPORT_FILE" > /dev/null 2>&1
                    if [ -f "$REPORT_FILE" ]; then
                        print_success "Advanced recommendations for module generated"
                        track_output "Recommendations" "$REPORT_FILE"
                    else
                        print_error "Failed to generate advanced recommendations for module"
                        track_output "ERROR: Recommendations" "Failed to generate"
                    fi
                    ;;
                *)
                    print_warning "Invalid choice, generating basic recommendations by default"
                    print_progress "Starting to generate default basic recommendations for module..."
                    REPORT_FILE="$OUTPUT_DIR/reports/module_basic_recommendations.md"
                    python3 src/basic_recom.py "$MODULE_CNL" "$MODULE_METRICS" "$SEED_TERMS_JSON" "$REPORT_FILE" > /dev/null 2>&1
                    if [ -f "$REPORT_FILE" ]; then
                        print_success "Basic recommendations for module generated"
                        track_output "Recommendations" "$REPORT_FILE"
                    else 
                        print_error "Failed to generate basic recommendations for module"
                        track_output "ERROR: Recommendations" "Failed to generate"
                    fi
                    ;;
            esac
        else
            print_error "Required files not found."
            exit 1
        fi
        ;;
    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac

# Final summary
print_header "ONTOLOGY EVALUATION SUMMARY"

# Process the collected file paths and display in a nice table
print_table "Generated Files" \
    "Input Ontology" "$INPUT_ONTOLOGY" \
    "Converted Ontology" "$CONVERTED_ONTOLOGY" \
    "Metrics JSON" "$METRICS_JSON" \
    "Seed Terms" "$SEED_TERMS" \
    "CNL Output" "${CNL_OUTPUT:-$MODULE_CNL}" \
    "Module" "${MODULE:-Not applicable}" \
    "Module Metrics" "${MODULE_METRICS:-Not applicable}" \
    "Recommendations" "$RECOMMENDATIONS"

print_success "Process completed successfully."
echo -e "${BOLD}${GREEN}All results saved in:${RESET} $OUTPUT_DIR"
echo ""
