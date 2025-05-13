#!/bin/bash

echo "Compiling project and creating JAR with dependencies..."
mvn clean compile assembly:single
echo "Compilation complete. JAR file should be available in the target directory."
