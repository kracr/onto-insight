package com.calculation_engine.seedTermsExtraction;

import org.semanticweb.owlapi.model.*;
import java.util.*;
import org.semanticweb.owlapi.search.EntitySearcher;

public class PROntoSeedTermExtractor implements SeedTermExtractor {

    @Override
    public Set<OWLClass> getSeedTerms(OWLOntology ontology) {
        Set<OWLClass> classes = ontology.getClassesInSignature();
        Map<OWLClass, Double> pronoScores = new HashMap<>();

        for (OWLClass cls : classes) {
            if (isLeafClass(cls, ontology))
                continue;

            PROntoMetrics metrics = calculateMetrics(cls, ontology);
            double prono = calculatePROnto(metrics);
            pronoScores.put(cls, prono);
        }

        return pronoScores.entrySet().stream()
                .sorted(Map.Entry.comparingByValue())
                .findFirst()
                .map(e -> Collections.singleton(e.getKey()))
                .orElse(Collections.emptySet());
    }

    private PROntoMetrics calculateMetrics(OWLClass cls, OWLOntology ontology) {
        PROntoMetrics metrics = new PROntoMetrics();

        // Count superclasses (excluding Thing)
        metrics.superClassCount = (int) EntitySearcher.getSuperClasses(cls, ontology)
                .flatMap(ce -> ce.classesInSignature())
                .filter(sup -> !sup.isOWLThing())
                .count();

        // Process relevant axioms
        processAxioms(cls, ontology, metrics);

        // Count subclass axioms involving this class
        metrics.subClassAxioms = ontology.getSubClassAxiomsForSubClass(cls).size()
                + ontology.getSubClassAxiomsForSuperClass(cls).size();

        return metrics;
    }

    private void processAxioms(OWLClass cls, OWLOntology ontology, PROntoMetrics metrics) {
        // Process SubClassOf axioms where cls is subclass
        for (OWLSubClassOfAxiom axiom : ontology.getSubClassAxiomsForSubClass(cls)) {
            processExpression(axiom.getSuperClass(), metrics);
        }

        // Process SubClassOf axioms where cls is superclass
        for (OWLSubClassOfAxiom axiom : ontology.getSubClassAxiomsForSuperClass(cls)) {
            processExpression(axiom.getSubClass(), metrics);
        }

        // Process equivalent class axioms
        for (OWLEquivalentClassesAxiom axiom : ontology.getEquivalentClassesAxioms(cls)) {
            for (OWLClassExpression expr : axiom.getClassExpressions()) {
                if (!expr.equals(cls)) {
                    processExpression(expr, metrics);
                }
            }
        }
    }

    private void processExpression(OWLClassExpression expr, PROntoMetrics metrics) {
        expr.signature().forEach(entity -> {
            if (entity.isOWLDataProperty()) {
                metrics.dataProps.add(entity.asOWLDataProperty());
            } else if (entity.isOWLObjectProperty()) {
                metrics.objectProps.add(entity.asOWLObjectProperty());
            }
        });
    }

    private double calculatePROnto(PROntoMetrics metrics) {
        int denominator = metrics.dataProps.size()
                + metrics.objectProps.size()
                + metrics.subClassAxioms;

        return denominator > 0 ? (double) metrics.superClassCount / denominator : 0.0;
    }

    private boolean isLeafClass(OWLClass cls, OWLOntology ontology) {
        return ontology.getSubClassAxiomsForSuperClass(cls).isEmpty()
                && EntitySearcher.getSubClasses(cls, ontology)
                        .noneMatch(ce -> !ce.isOWLNothing());
    }

    private static class PROntoMetrics {
        Set<OWLDataProperty> dataProps = new HashSet<>();
        Set<OWLObjectProperty> objectProps = new HashSet<>();
        int superClassCount = 0;
        int subClassAxioms = 0;
    }
}