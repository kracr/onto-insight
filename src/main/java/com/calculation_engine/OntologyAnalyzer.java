package com.calculation_engine;

import org.semanticweb.owlapi.apibinding.OWLManager;
import org.semanticweb.owlapi.model.*;
import org.semanticweb.owlapi.search.EntitySearcher;

import java.io.File;
import java.util.HashMap;
import java.util.Map;
import java.util.stream.Stream;

public class OntologyAnalyzer {

    public static void main(String[] args) {
        try {
            // Load the ontology
            OWLOntologyManager manager = OWLManager.createOWLOntologyManager();
            OWLOntology ontology = manager.loadOntologyFromOntologyDocument(new File("ontologies/ontologycosylab.rdf"));

            // Maps to store counts for each class
            Map<OWLClass, Integer> subclassCounts = new HashMap<>();
            Map<OWLClass, Integer> dataPropertyCounts = new HashMap<>();
            Map<OWLClass, Integer> objectPropertyCounts = new HashMap<>();

            // Iterate over all classes in the ontology
            for (OWLClass cls : ontology.getClassesInSignature()) {
                // Count subclasses
                int subclassCount = ontology.getSubClassAxiomsForSuperClass(cls).size();
                subclassCounts.put(cls, subclassCount);

                // Count data properties that have this class in their domain
                int dataPropertyCount = (int) ontology.getDataPropertiesInSignature().stream()
                    .filter(prop -> {
                        try (Stream<OWLClassExpression> domains = EntitySearcher.getDomains(prop, ontology)) {
                            return domains.anyMatch(domain -> domain.containsEntityInSignature(cls));
                        }
                    })
                    .count();
                dataPropertyCounts.put(cls, dataPropertyCount);

                // Count object properties that have this class in their domain
                int objectPropertyCount = (int) ontology.getObjectPropertiesInSignature().stream()
                    .filter(prop -> {
                        try (Stream<OWLClassExpression> domains = EntitySearcher.getDomains(prop, ontology)) {
                            return domains.anyMatch(domain -> domain.containsEntityInSignature(cls));
                        }
                    })
                    .count();
                objectPropertyCounts.put(cls, objectPropertyCount);
            }

            // Print the results
            int totalSubclasses = 0;
            int totalDataProperties = 0;
            int totalObjectProperties = 0;

            for (OWLClass cls : ontology.getClassesInSignature()) {
                String classIRI = cls.getIRI().getShortForm();
                int subCount = subclassCounts.get(cls);
                int dataCount = dataPropertyCounts.get(cls);
                int objCount = objectPropertyCounts.get(cls);
                
                totalSubclasses += subCount;
                totalDataProperties += dataCount;
                totalObjectProperties += objCount;

                System.out.println("Class: " + classIRI);
                System.out.println("Subclasses Count: " + subCount);
                System.out.println("Data Properties Count: " + dataCount);
                System.out.println("Object Properties Count: " + objCount);
                System.out.println();
            }

            // Print totals
            System.out.println("=== TOTALS ===");
            System.out.println("Total Subclasses: " + totalSubclasses);
            System.out.println("Total Data Properties: " + totalDataProperties);
            System.out.println("Total Object Properties: " + totalObjectProperties);

        } catch (OWLOntologyCreationException e) {
            e.printStackTrace();
        }
    }
}
