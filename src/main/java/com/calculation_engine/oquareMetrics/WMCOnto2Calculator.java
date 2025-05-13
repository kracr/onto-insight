package com.calculation_engine.oquareMetrics;

import java.util.*;
import java.util.stream.Collectors;
import org.semanticweb.owlapi.model.OWLClass;
import org.semanticweb.owlapi.model.OWLOntology;
import org.semanticweb.owlapi.search.EntitySearcher;

import com.calculation_engine.MetricCalculator;
import com.calculation_engine.OntologyUtils;

public class WMCOnto2Calculator implements MetricCalculator {
    @Override
    public double calculate(OWLOntology ontology) {
        Set<OWLClass> classes = ontology.getClassesInSignature();
        int totalPaths = 0;
        int leafClassCount = 0;

        for (OWLClass cls : classes) {
            // Skip owl:Thing
            if (cls.isOWLThing()) {
                continue;
            }

            // Check if class is a leaf class (has no subclasses)
            Collection<OWLClass> subClasses = OntologyUtils
                .classExpr2classes(EntitySearcher.getSubClasses(cls, ontology).collect(Collectors.toList()));
            
            if (subClasses.isEmpty()) {
                // This is a leaf class
                leafClassCount++;
                // Count number of paths to this leaf class
                totalPaths += countPathsToClass(cls, ontology);
            }
        }

        // Avoid division by zero
        if (leafClassCount == 0) {
            return 0.0;
        }

        return (double) totalPaths / leafClassCount;
    }

    private int countPathsToClass(OWLClass cls, OWLOntology ontology) {
        // Base case: if we reach Thing, we found one path
        if (cls.isOWLThing()) {
            return 1;
        }

        int pathCount = 0;
        // Get direct superclasses
        Collection<OWLClass> superClasses = OntologyUtils
            .classExpr2classes(EntitySearcher.getSuperClasses(cls, ontology).collect(Collectors.toList()));

        // If no superclasses are found, assume there's an implicit path to Thing
        if (superClasses.isEmpty()) {
            return 1;
        }

        // Count paths through each superclass
        for (OWLClass superClass : superClasses) {
            pathCount += countPathsToClass(superClass, ontology);
        }

        return pathCount;
    }
}
