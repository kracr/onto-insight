package com.calculation_engine.seedTermsExtraction;

import org.semanticweb.owlapi.apibinding.OWLManager;
import org.semanticweb.owlapi.model.IRI;
import org.semanticweb.owlapi.model.OWLClass;
import org.semanticweb.owlapi.model.OWLOntology;
import org.semanticweb.owlapi.model.OWLOntologyCreationException;
import org.semanticweb.owlapi.model.OWLOntologyManager;

import java.io.File;
import java.io.FileNotFoundException;
import java.util.*;

public class RunGenericExtractor {

    public static void main(String[] args) {
        if (args.length < 1) {
            System.err.println("Usage: java -cp <classpath> com.calculation_engine.seedTermsExtraction.RunGenericExtractor <ontology_path> [comma_separated_metrics]");
            System.exit(1);
        }

        // Get ontology path from command line arguments
        String ontologyPath = args[0];
        
        // Get specific metrics to extract if provided
        final List<String> specificMetrics;
        if (args.length > 1 && args[1] != null && !args[1].trim().isEmpty()) {
            specificMetrics = Arrays.asList(args[1].split(","));
            System.out.println("Extracting seed terms for specific metrics: " + String.join(", ", specificMetrics));
        } else {
            specificMetrics = new ArrayList<>();
        }

        try {
            // 1. Create OWLOntologyManager
            OWLOntologyManager manager = OWLManager.createOWLOntologyManager();

            // 2. Load ontology from file
            File ontologyFile = new File(ontologyPath);
            if (!ontologyFile.exists()) {
                throw new FileNotFoundException("Ontology file not found: " + ontologyPath);
            }

            OWLOntology ontology = manager.loadOntologyFromOntologyDocument(ontologyFile);
            System.out.println(
                    "Loaded ontology: " + ontology.getOntologyID().getOntologyIRI().orElse(IRI.create("Unknown")));

            // 3. Create list of all available extractors
            List<Object> allExtractors = Arrays.asList(
                    new ANOntoSeedTermExtractor(),
                    new AROntoSeedTermExtractor(),
                    new CROntoSeedTermExtractor(),
                    new DITOntoSeedTermExtractor(),
                    new LCOMOntoSeedTermExtractor(),
                    new CBOntoSeedTermExtractor(),
                    new INROntoSeedTermExtractor(),
                    new NACOntoSeedTermExtractor(),
                    new NOCOntoSeedTermExtractor(),
                    new NOMOntoSeedTermExtractor(),
                    new POntoSeedTermExtractor(),
                    new PROntoSeedTermExtractor(),
                    new RFCOntoSeedTermExtractor(),
                    new RROntoSeedTermExtractor(),
                    new TMOntoSeedTermExtractor(),
                    new WMCOntoSeedTermExtractor());

            // Filter extractors based on specific metrics if provided
            List<Object> extractors = allExtractors;
            if (!specificMetrics.isEmpty()) {
                // Create a new filtered list
                List<Object> filteredExtractors = new ArrayList<>();
                
                // Loop through all extractors and check each one
                for (Object extractor : allExtractors) {
                    String fullClassName = extractor.getClass().getSimpleName();
                    // Remove the "OntoSeedTermExtractor" suffix to get the metric name
                    String metricName = fullClassName.replace("OntoSeedTermExtractor", "");
                    
                    // Check if this metric is in our specificMetrics list
                    boolean isRequested = specificMetrics.contains(metricName);
                    
                    if (isRequested) {
                        filteredExtractors.add(extractor);
                    }
                }
                
                // Update our extractors list
                extractors = filteredExtractors;
                
                if (extractors.isEmpty()) {
                    System.err.println("Warning: No matching extractors found for the specified metrics.");
                    System.exit(1);
                }
            }

            // 4. Run extractors and collect results
            Map<String, Set<OWLClass>> results = new HashMap<>();
            for (Object extractor : extractors) {
                try {
                    Set<OWLClass> seedTerms = ((SeedTermExtractor) extractor).getSeedTerms(ontology);
                    String extractorName = extractor.getClass().getSimpleName().replace("OntoSeedTermExtractor", "");
                    results.put(extractorName, seedTerms);
                } catch (Exception e) {
                    System.err.println("Error running extractor: " + e.getMessage());
                }
            }

            // 5. Print results
            System.out.println("\nSeed Terms by Metric:");
            System.out.println("=====================");

            results.entrySet().stream()
                    .sorted(Map.Entry.comparingByKey())
                    .forEach(entry -> {
                        System.out.println("\nMetric: " + entry.getKey());
                        System.out.println("Number of seed terms: " + entry.getValue().size());
                        if (entry.getValue().isEmpty()) {
                            System.out.println("No seed terms found for this metric");
                        } else {
                            // Print all seed terms, not just limited to 2
                            entry.getValue().forEach(cls -> {
                                System.out.println("Seed term: " + cls.getIRI().getShortForm());
                                System.out.println("Full IRI: " + cls.getIRI().toString());
                            });
                        }
                        System.out.println("-----------------------------");
                    });

        } catch (OWLOntologyCreationException e) {
            System.err.println("Error creating ontology: " + e.getMessage());
            System.exit(1);
        } catch (FileNotFoundException e) {
            System.err.println(e.getMessage());
            System.exit(1);
        } catch (Exception e) {
            System.err.println("Unexpected error: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }
    }
}
