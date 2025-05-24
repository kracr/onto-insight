# Onto-Insight

A metric and LLM-based tool that provides recommendations to improve the quality of ontologies. This tool combines structural analysis, modular evaluation, and AI-powered suggestions to help ontology engineers enhance their ontologies.

## Features

- **Comprehensive Quality Analysis**: Evaluates ontologies using 16 OQuaRE-based metrics across structural, functional, semantic, and modular dimensions
- **Modular Evaluation**: Supports both full ontology analysis and targeted modular evaluation
- **AI-Powered Recommendations**: Leverages LLMs for intelligent improvement suggestions
- **Controlled Natural Language**: Converts OWL syntax to human-readable format for better LLM understanding
- **Dockerized Environment**: Fully containerized for easy deployment and reproducibility
- **Two Analysis Modes**: Basic (for simple understanding) and Advanced (for technically deep insights)

## Prerequisites

- Docker and Docker Compose
- Git
- Unix-like environment (Linux/MacOS) or Windows with WSL

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/onto-insight.git
cd onto-insight
```

2. Configure the environment:
   Create a `.env` file in the root directory with the following options:

```env
# AI Configuration
AI_API_KEY=your_api_key_here
AI_URL=https://api.openai.com/v1  # OpenAI-compatible API endpoint
MODEL_NAME=gpt-4  # Model to use for analysis
```

3. Build the Docker image:

```bash
docker compose build
```

4. Start the containerized environment:

```bash
docker compose up -d
```

## Usage

Run the tool using the provided script:

```bash
./run.sh {ONTOLOGY_FILE_PATH} {EVALUATION_TYPE} {MODE}
```

### Parameters:

- `ONTOLOGY_FILE_PATH`: Path to your OWL ontology file
- `EVALUATION_TYPE`:
  - `FULL`: Complete ontology evaluation
  - `MOD`: Modular analysis focusing on problematic areas
- `MODE`:
  - `BASIC`: Simplified explanations and non-technical suggestions
  - `ADVANCED`: Detailed technical analysis with OWL-compliant improvements

### Example:

```bash
./run.sh ./ontologies/example.owl FULL ADVANCED
```
### HELP:

Please press 'enter' if stuck on the CLI

## Pipeline Overview

The tool automatically performs the following steps:

1. **Format Validation**: Checks and converts ontology format to OWL/XML if necessary
2. **Metric Computation**: Calculates OQuaRE-based quality metrics and sub-characteristics
3. **Problem Identification**: Identifies worst-performing metrics
4. **Seed Term Extraction**: Extracts relevant terms based on problematic metrics
5. **Modularization**: Uses ROBOT to create focused modules around seed terms
6. **CNL Generation**: Converts ontology modules to Controlled Natural Language
7. **LLM Analysis**: Processes the CNL with selected LLM for recommendations
8. **Report Generation**: Produces markdown-formatted recommendation reports

## Output

All outputs are saved to the `output/` directory and include:

- Quality metrics (JSON)
- Extracted seed terms (JSON)
- CNL representation (TXT)
- Final recommendations (Markdown)

## Evaluation Metrics and Subcharacteristic Description

For metrics related documentation refer [metrics_documentation](./metrics_documentation.md)

## Tool Testing Reports

Our team has done extensive perturbation testing on different ontologies of varying sizes in order to validate outcomes. For results, refer [Tool_Perturbation_Evaluation_Report](./Tool_Perturbation_Evaluation_Report.md)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## Citation

Citation information will be added in a future update.

## Support

For issues and feature requests, please use the GitHub issue tracker.

## Any Reviews?

We are currently conducting a user study to gather feedback and identify opportunities for improving future versions of the tool. If you found the tool helpful or have suggestions for enhancement, we would greatly appreciate it if you could take just 2 minutes to fill out our short feedback form:
https://forms.gle/S2WpcXCf7mHar2D39

Thank You!
