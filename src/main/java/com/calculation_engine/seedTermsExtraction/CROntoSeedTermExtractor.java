package com.calculation_engine.seedTermsExtraction;

import org.semanticweb.owlapi.model.*;
import java.util.*;
import org.semanticweb.owlapi.search.EntitySearcher;

public class CROntoSeedTermExtractor implements SeedTermExtractor {

    @Override
    public Set<OWLClass> getSeedTerms(OWLOntology ontology) {
        Set<OWLClass> classes = ontology.getClassesInSignature();
        int totalClasses = classes.size();
        Map<OWLClass, Integer> instanceCounts = new HashMap<>();
        classes.forEach(cls -> instanceCounts.put(cls, 0));

        // Count instances per class
        ontology.axioms(AxiomType.CLASS_ASSERTION)
                .filter(axiom -> axiom.getClassExpression().isNamed())
                .forEach(axiom -> {
                    OWLClass cls = axiom.getClassExpression().asOWLClass();
                    instanceCounts.put(cls, instanceCounts.get(cls) + 1);
                });

        Map<OWLClass, Double> crScores = new HashMap<>();
        classes.stream()
                .filter(cls -> !cls.isOWLThing())
                .filter(cls -> !isLeafClass(cls, ontology))
                .forEach(cls -> {
                    double score = (double) instanceCounts.get(cls) / totalClasses;
                    crScores.put(cls, score);
                });

        return crScores.entrySet().stream()
                .sorted(Map.Entry.comparingByValue())
                .findFirst()
                .map(e -> Collections.singleton(e.getKey()))
                .orElse(Collections.emptySet());
    }

    private boolean isLeafClass(OWLClass cls, OWLOntology ontology) {
        return EntitySearcher.getSubClasses(cls, ontology)
                .noneMatch(ce -> ce.classesInSignature()
                        .anyMatch(sub -> !sub.isOWLThing() && !sub.isOWLNothing()));
    }
}