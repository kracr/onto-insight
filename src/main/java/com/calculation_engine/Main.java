package com.calculation_engine;

import org.semanticweb.owlapi.apibinding.OWLManager;
import org.semanticweb.owlapi.functional.parser.OWLFunctionalSyntaxOWLParserFactory;
import org.semanticweb.owlapi.model.OWLOntology;
import org.semanticweb.owlapi.model.OWLOntologyManager;
import org.semanticweb.owlapi.model.OWLOntologyCreationException;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonObject;

import java.io.File;
import java.io.FileWriter;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.Instant;
import java.util.concurrent.*;

public class Main {
    public static void main(String[] args) {
        if (args.length == 0) {
            System.err.println("Error: Please provide the path to the ontology file as an argument.");
            System.exit(1);
        }

        String ontologyPath = args[0];
        
        ExecutorService executor = Executors.newSingleThreadExecutor();
        Future<Void> future = executor.submit(() -> {
            try {
                processOntology(ontologyPath);
            } catch (Exception e) {
                System.err.println("Error processing the ontology: " + e.getMessage());
                System.err.println("Please ensure the file is a valid ontology and you have the necessary permissions.");
            }
            return null;
        });

        try {
            future.get(5, TimeUnit.MINUTES); // Set a 5-minute timeout
        } catch (TimeoutException e) {
            System.err.println("Error: Ontology processing timed out after 5 minutes.");
        } catch (InterruptedException | ExecutionException e) {
            System.err.println("Error: " + e.getMessage());
        } finally {
            executor.shutdownNow();
        }
    }

    private static void processOntology(String ontologyPath) throws Exception {
        OWLOntologyManager manager = OWLManager.createOWLOntologyManager();
        File ontologyFile = new File(ontologyPath);

        if (!ontologyFile.exists()) {
            throw new IllegalArgumentException("The specified ontology file does not exist: " + ontologyPath);
        }

        // Add specific format handling for OFN files
        if (ontologyPath.toLowerCase().endsWith(".ofn")) {
            manager.getOntologyParsers().add(new OWLFunctionalSyntaxOWLParserFactory());
        }

        try {
            OWLOntology ontology = manager.loadOntologyFromOntologyDocument(ontologyFile);
            
            if (ontology == null) {
                throw new IllegalStateException("Failed to load ontology: null ontology returned");
            }

            // Calculate OQuaRE metrics
            OQuaRE.Scores metrics = OQuaRE.calculateScores(ontology);
            
            // Calculate Sub-characteristics
            SubcharacteristicsCalculator.Scores subCharScores = SubcharacteristicsCalculator.calculateScores(metrics);
            
            // Print to console
            System.out.println("\n===============================================");
            System.out.println("OQuaRE Scores for ontology: " + ontologyPath);
            System.out.println(metrics);
            System.out.println("\n===============================================");
            System.out.println("Sub-characteristics Scores:");
            System.out.println(subCharScores);

            // Save to JSON file
            saveScoresToJson(metrics, subCharScores, ontologyPath);
            
        } catch (OWLOntologyCreationException e) {
            System.err.println("Error loading ontology: " + e.getMessage());
            System.err.println("File format: " + (ontologyPath.endsWith(".ofn") ? "OWL Functional Syntax" : "Unknown"));
            System.err.println("File path: " + ontologyFile.getAbsolutePath());
            System.err.println("File size: " + ontologyFile.length() + " bytes");
            System.err.println("File readable: " + ontologyFile.canRead());
            throw e;
        }
    }

    private static void saveScoresToJson(OQuaRE.Scores metrics, SubcharacteristicsCalculator.Scores subCharScores, String ontologyPath) {
        try {
            Path inputPath = Paths.get(ontologyPath);
            String baseName = inputPath.getFileName().toString();
            String jsonFilePath = inputPath.getParent().resolve(baseName + "_metrics.json").toString();

            JsonObject rootObject = new JsonObject();
            rootObject.addProperty("name", baseName);
            rootObject.addProperty("timestamp", Instant.now().toString());
            
            Gson gson = new GsonBuilder().setPrettyPrinting().create();
            JsonObject metricsObject = gson.toJsonTree(metrics).getAsJsonObject();
            JsonObject subCharObject = gson.toJsonTree(subCharScores).getAsJsonObject();
            
            rootObject.add("metrics", metricsObject);
            rootObject.add("subcharacteristics", subCharObject);

            try (FileWriter writer = new FileWriter(jsonFilePath)) {
                gson.toJson(rootObject, writer);
            }

            System.out.println("\nMetrics saved to: " + jsonFilePath);

        } catch (Exception e) {
            System.err.println("Error saving metrics to JSON: " + e.getMessage());
        }
    }
}
