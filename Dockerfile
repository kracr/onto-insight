FROM openjdk:11-slim

# Install basic tools
RUN apt-get update && \
    apt-get install -y curl wget gnupg2 lsb-release build-essential libssl-dev zlib1g-dev \
    libncurses5-dev libncursesw5-dev libreadline-dev libsqlite3-dev libgdbm-dev \
    libdb5.3-dev libbz2-dev libexpat1-dev liblzma-dev tk-dev libffi-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Compile Python 3.10 from source
WORKDIR /tmp
RUN wget https://www.python.org/ftp/python/3.10.12/Python-3.10.12.tgz && \
    tar -xf Python-3.10.12.tgz && \
    cd Python-3.10.12 && \
    ./configure --enable-optimizations && \
    make -j$(nproc) && \
    make install && \
    cd .. && \
    rm -rf Python-3.10.12*

# Make sure pip is up to date
RUN python3 -m pip install --upgrade pip

# Set working directory for the application
WORKDIR /app

# Install ROBOT (OBO Tool)
RUN mkdir -p /usr/local/bin && \
    curl -L -o /usr/local/bin/robot.jar https://github.com/ontodev/robot/releases/latest/download/robot.jar && \
    curl -L https://raw.githubusercontent.com/ontodev/robot/master/bin/robot > /usr/local/bin/robot && \
    chmod +x /usr/local/bin/robot

# Copy pom.xml first to leverage Docker cache for Maven dependencies
COPY pom.xml .

# Install Maven
RUN apt-get update && \
    apt-get install -y maven && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy Python requirements
COPY requirements.txt .

# Copy vocabulary fix script 
COPY vocabulary_fix.py .

# Install Python dependencies
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Create necessary directories with proper permissions
RUN mkdir -p /app/output /app/output/ontologies /app/output/cnl /app/output/reports /app/ontologies && \
    chmod -R 777 /app/output /app/ontologies

# Copy the rest of the application
COPY . .

# Run vocabulary fix script to fix type hints in vocabulary.py
RUN python3 vocabulary_fix.py

# Set up Python path for the local verbalizer module
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Make scripts executable
RUN chmod +x compile.sh run.sh

# Try to compile Java application but don't fail if it doesn't work
RUN ./compile.sh

# Verify ROBOT installation
RUN robot --version

# Verify Python version
RUN python3 --version

# Set environment variables for API keys (will be overridden by .env file)
ENV AI_API_KEY=""
ENV AI_URL=""
ENV MODEL_NAME=""

# Create a startup script to keep the container running
RUN echo '#!/bin/bash\n\
echo "Container started. Use docker-compose exec btp-tool bash to connect."\n\
echo "Python version: $(python3 --version)"\n\
echo "To run the application: ./run.sh /app/ontologies/your_ontology.owl"\n\
tail -f /dev/null' > /app/start.sh && chmod +x /app/start.sh

# Keep the container running
ENTRYPOINT ["/bin/bash"]
CMD ["/app/start.sh"] 