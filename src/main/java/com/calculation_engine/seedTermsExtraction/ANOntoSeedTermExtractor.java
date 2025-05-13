package com.calculation_engine.seedTermsExtraction;

import org.semanticweb.owlapi.model.*;
import java.util.*;
import java.util.stream.Collectors;
import org.semanticweb.owlapi.search.EntitySearcher;

public class ANOntoSeedTermExtractor implements SeedTermExtractor {

    @Override
    public Set<OWLClass> getSeedTerms(OWLOntology ontology) {
        Set<OWLClass> classes = ontology.getClassesInSignature();
        int totalClasses = classes.size();
        int ontologyLevelAnnotations = ontology.getAnnotations().size();
        Map<OWLClass, Double> anoScores = new HashMap<>();

        // Precompute class annotations
        Map<IRI, Long> classAnnotationCounts = ontology.axioms(AxiomType.ANNOTATION_ASSERTION)
                .filter(axiom -> axiom.getSubject() instanceof IRI)
                .collect(Collectors.groupingBy(
                        axiom -> (IRI) axiom.getSubject(),
                        Collectors.counting()));

        classes.stream()
                .filter(cls -> !isLeafClass(cls, ontology))
                .forEach(cls -> {
                    long classAnnotations = classAnnotationCounts.getOrDefault(cls.getIRI(), 0L);
                    double score = (classAnnotations + ontologyLevelAnnotations) / totalClasses;
                    anoScores.put(cls, score);
                });

        return anoScores.entrySet().stream()
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