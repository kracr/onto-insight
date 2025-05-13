package com.calculation_engine.seedTermsExtraction;

import org.semanticweb.owlapi.model.*;
import java.util.*;

public class WMCOntoSeedTermExtractor implements SeedTermExtractor {

    @Override
    public Set<OWLClass> getSeedTerms(OWLOntology ontology) {
        Set<OWLClass> classes = ontology.getClassesInSignature();
        int totalClasses = classes.size();
        Map<OWLClass, Double> wmcScores = new HashMap<>();

        // Precompute all necessary metrics
        Map<OWLClass, Integer> dataProps = countDataPropertyAssertions(ontology);
        Map<OWLClass, Integer> objectProps = countObjectPropertyUsage(ontology);
        Map<OWLClass, Integer> subclassAxioms = countSubclassInvolvements(ontology);

        // Calculate weighted scores per class
        classes.forEach(cls -> {
            double score = (dataProps.getOrDefault(cls, 0) +
                    objectProps.getOrDefault(cls, 0) +
                    subclassAxioms.getOrDefault(cls, 0)) / (double) totalClasses;

            wmcScores.put(cls, score);
        });

        return wmcScores.entrySet().stream()
                .sorted(Map.Entry.<OWLClass, Double>comparingByValue().reversed())
                .findFirst()
                .map(entry -> Collections.singleton(entry.getKey()))
                .orElse(Collections.emptySet());
    }

    private Map<OWLClass, Integer> countDataPropertyAssertions(OWLOntology ontology) {
        Map<OWLClass, Integer> counts = new HashMap<>();
        ontology.axioms(AxiomType.DATA_PROPERTY_ASSERTION).forEach(axiom -> {
            OWLIndividual individual = ((OWLDataPropertyAssertionAxiom) axiom).getSubject();
            ontology.classAssertionAxioms(individual)
                    .map(ax -> ax.getClassExpression())
                    .filter(OWLClassExpression::isNamed)
                    .map(ce -> ce.asOWLClass())
                    .forEach(cls -> counts.put(cls, counts.getOrDefault(cls, 0) + 1));
        });
        return counts;
    }

    private Map<OWLClass, Integer> countObjectPropertyUsage(OWLOntology ontology) {
        Map<OWLClass, Integer> counts = new HashMap<>();
        ontology.axioms(AxiomType.SUBCLASS_OF).forEach(axiom -> {
            axiom.getSubClass().classesInSignature().forEach(cls -> {
                int props = axiom.getObjectPropertiesInSignature().size();
                counts.put(cls, counts.getOrDefault(cls, 0) + props);
            });
        });
        return counts;
    }

    private Map<OWLClass, Integer> countSubclassInvolvements(OWLOntology ontology) {
        Map<OWLClass, Integer> counts = new HashMap<>();
        ontology.axioms(AxiomType.SUBCLASS_OF).forEach(axiom -> {
            axiom.getSubClass().classesInSignature()
                    .forEach(cls -> counts.put(cls, counts.getOrDefault(cls, 0) + 1));
            axiom.getSuperClass().classesInSignature()
                    .forEach(cls -> counts.put(cls, counts.getOrDefault(cls, 0) + 1));
        });
        return counts;
    }
}