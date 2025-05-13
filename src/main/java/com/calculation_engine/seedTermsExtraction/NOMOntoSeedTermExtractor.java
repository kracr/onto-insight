package com.calculation_engine.seedTermsExtraction;

import org.semanticweb.owlapi.model.*;
import java.util.*;

public class NOMOntoSeedTermExtractor implements SeedTermExtractor {

    @Override
    public Set<OWLClass> getSeedTerms(OWLOntology ontology) {
        Set<OWLClass> classes = ontology.getClassesInSignature();
        int totalClasses = classes.size();
        Map<OWLClass, Double> nomScores = new HashMap<>();

        for (OWLClass cls : classes) {
            Set<OWLProperty> properties = new HashSet<>();

            // Process class axioms for property usage
            processClassAxioms(cls, ontology, properties);

            double score = (double) properties.size() / totalClasses;
            nomScores.put(cls, score);
        }

        return nomScores.entrySet().stream()
                .sorted(Map.Entry.comparingByValue())
                .findFirst()
                .map(e -> Collections.singleton(e.getKey()))
                .orElse(Collections.emptySet());
    }

    private void processClassAxioms(OWLClass cls, OWLOntology ontology,
            Set<OWLProperty> properties) {
        // Process SubClassOf axioms
        for (OWLSubClassOfAxiom axiom : ontology.getSubClassAxiomsForSubClass(cls)) {
            processExpression(axiom.getSuperClass(), properties);
        }

        // Process EquivalentClasses axioms
        for (OWLEquivalentClassesAxiom axiom : ontology.getEquivalentClassesAxioms(cls)) {
            for (OWLClassExpression expr : axiom.getClassExpressions()) {
                if (!expr.equals(cls)) {
                    processExpression(expr, properties);
                }
            }
        }
    }

    private void processExpression(OWLClassExpression expr,
            Set<OWLProperty> properties) {
        expr.signature()
                .filter(entity -> entity.isOWLDataProperty() || entity.isOWLObjectProperty())
                .forEach(entity -> properties.add((OWLProperty) entity));
    }
}