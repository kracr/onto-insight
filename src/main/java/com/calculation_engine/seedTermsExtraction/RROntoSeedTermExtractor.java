package com.calculation_engine.seedTermsExtraction;

import org.semanticweb.owlapi.model.*;
import java.util.*;
import org.semanticweb.owlapi.search.EntitySearcher;

public class RROntoSeedTermExtractor implements SeedTermExtractor {

    @Override
    public Set<OWLClass> getSeedTerms(OWLOntology ontology) {
        Set<OWLClass> classes = ontology.getClassesInSignature();
        Map<OWLClass, Double> rroScores = new HashMap<>();

        for (OWLClass cls : classes) {
            if (isLeafClass(cls, ontology))
                continue;

            ClassMetrics metrics = calculateClassMetrics(cls, ontology);
            double rro = calculateRROnto(metrics);
            rroScores.put(cls, rro);
        }

        return rroScores.entrySet().stream()
                .sorted(Map.Entry.comparingByValue())
                .findFirst()
                .map(e -> Collections.singleton(e.getKey()))
                .orElse(Collections.emptySet());
    }

    private ClassMetrics calculateClassMetrics(OWLClass cls, OWLOntology ontology) {
        ClassMetrics metrics = new ClassMetrics();

        // Count subclass axioms where class appears
        metrics.subClassAxioms = ontology.getSubClassAxiomsForSubClass(cls).size()
                + ontology.getSubClassAxiomsForSuperClass(cls).size();

        // Process axioms involving the class
        processAxioms(cls, ontology, metrics);

        return metrics;
    }

    private void processAxioms(OWLClass cls, OWLOntology ontology, ClassMetrics metrics) {
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

    private void processExpression(OWLClassExpression expr, ClassMetrics metrics) {
        expr.signature().forEach(entity -> {
            if (entity.isOWLDataProperty()) {
                metrics.dataProps.add(entity.asOWLDataProperty());
            } else if (entity.isOWLObjectProperty()) {
                metrics.objProps.add(entity.asOWLObjectProperty());
            }
        });
    }

    private double calculateRROnto(ClassMetrics metrics) {
        int dpCount = metrics.dataProps.size();
        int opCount = metrics.objProps.size();
        int total = dpCount + opCount + metrics.subClassAxioms;

        return total > 0 ? (double) (dpCount + opCount) / total : 0.0;
    }

    private boolean isLeafClass(OWLClass cls, OWLOntology ontology) {
        return ontology.getSubClassAxiomsForSuperClass(cls).isEmpty()
                && EntitySearcher.getSubClasses(cls, ontology)
                        .noneMatch(ce -> !ce.isOWLNothing());
    }

    private static class ClassMetrics {
        Set<OWLDataProperty> dataProps = new HashSet<>();
        Set<OWLObjectProperty> objProps = new HashSet<>();
        int subClassAxioms = 0;
    }
}