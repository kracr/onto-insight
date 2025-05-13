package com.calculation_engine.seedTermsExtraction;

import org.semanticweb.owlapi.model.*;
import java.util.*;
import org.semanticweb.owlapi.search.EntitySearcher;

public class INROntoSeedTermExtractor implements SeedTermExtractor {

    @Override
    public Set<OWLClass> getSeedTerms(OWLOntology ontology) {
        Set<OWLClass> classes = ontology.getClassesInSignature();
        int totalClasses = classes.size();
        Map<OWLClass, Double> inrScores = new HashMap<>();

        classes.stream()
                .filter(cls -> !isLeafClass(cls, ontology))
                .forEach(cls -> {
                    int axiomCount = ontology.getSubClassAxiomsForSubClass(cls).size()
                            + ontology.getSubClassAxiomsForSuperClass(cls).size();
                    double score = (double) axiomCount / totalClasses;
                    inrScores.put(cls, score);
                });

        return inrScores.entrySet().stream()
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