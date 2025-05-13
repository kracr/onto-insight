package com.calculation_engine.seedTermsExtraction;

import org.semanticweb.owlapi.model.*;
import java.util.*;
import org.semanticweb.owlapi.search.EntitySearcher;

public class AROntoSeedTermExtractor implements SeedTermExtractor {

    @Override
    public Set<OWLClass> getSeedTerms(OWLOntology ontology) {
        Set<OWLClass> classes = ontology.getClassesInSignature();
        int totalClasses = classes.size();
        Map<OWLClass, Double> arScores = new HashMap<>();

        // Pre-cache domain relationships
        Map<OWLClass, Integer> domainCounts = new HashMap<>();
        classes.forEach(cls -> domainCounts.put(cls, 0));

        processDomains(ontology.getAxioms(AxiomType.DATA_PROPERTY_DOMAIN), domainCounts);
        processDomains(ontology.getAxioms(AxiomType.OBJECT_PROPERTY_DOMAIN), domainCounts);

        classes.stream()
                .filter(cls -> !isLeafClass(cls, ontology))
                .forEach(cls -> {
                    double score = (double) domainCounts.get(cls) / totalClasses;
                    arScores.put(cls, score);
                });

        return arScores.entrySet().stream()
                .sorted(Map.Entry.comparingByValue())
                .findFirst()
                .map(e -> Collections.singleton(e.getKey()))
                .orElse(Collections.emptySet());
    }

    private void processDomains(Collection<? extends OWLPropertyDomainAxiom<?>> axioms,
            Map<OWLClass, Integer> counts) {
        for (OWLPropertyDomainAxiom<?> axiom : axioms) {
            axiom.getDomain().classesInSignature().forEach(cls -> {
                counts.computeIfPresent(cls, (k, v) -> v + 1);
            });
        }
    }

    private boolean isLeafClass(OWLClass cls, OWLOntology ontology) {
        return EntitySearcher.getSubClasses(cls, ontology)
                .noneMatch(ce -> ce.classesInSignature()
                        .anyMatch(sub -> !sub.isOWLThing() && !sub.isOWLNothing()));
    }
}