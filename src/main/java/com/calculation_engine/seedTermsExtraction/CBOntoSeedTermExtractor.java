package com.calculation_engine.seedTermsExtraction;

import org.semanticweb.owlapi.model.*;
import java.util.*;
import java.util.stream.Collectors;
import uk.ac.manchester.cs.owl.owlapi.OWLDataFactoryImpl;
import org.semanticweb.owlapi.search.EntitySearcher;

public class CBOntoSeedTermExtractor implements SeedTermExtractor {

    @Override
    public Set<OWLClass> getSeedTerms(OWLOntology ontology) {
        Set<OWLClass> classes = ontology.getClassesInSignature();
        Set<OWLClass> rootClasses = getRootClasses(ontology);
        int denominator = classes.size() - rootClasses.size();

        if (denominator <= 0)
            return Collections.emptySet();

        Map<OWLClass, Double> cbScores = new HashMap<>();
        // OWLClass thing = new OWLDataFactoryImpl().getOWLThing();

        for (OWLClass cls : classes) {
            if (cls.isOWLThing() || isLeafClass(cls, ontology))
                continue;

            int superClassCount = countMeaningfulSuperclasses(cls, ontology);
            double score = (double) superClassCount / denominator;
            cbScores.put(cls, score);
        }

        return cbScores.entrySet().stream()
                .sorted(Map.Entry.comparingByValue())
                .findFirst()
                .map(e -> Collections.singleton(e.getKey()))
                .orElse(Collections.emptySet());
    }

    private int countMeaningfulSuperclasses(OWLClass cls, OWLOntology ontology) {
        return (int) EntitySearcher.getSuperClasses(cls, ontology)
                .flatMap(ce -> ce.classesInSignature())
                .filter(sup -> !sup.isOWLThing())
                .count();
    }

    private Set<OWLClass> getRootClasses(OWLOntology ontology) {
        Set<OWLClass> roots = new HashSet<>();
        OWLClass thing = new OWLDataFactoryImpl().getOWLThing();

        for (OWLClass cls : ontology.getClassesInSignature()) {
            if (cls.isOWLThing())
                continue;

            Set<OWLClass> superClasses = EntitySearcher.getSuperClasses(cls, ontology)
                    .flatMap(ce -> ce.classesInSignature())
                    .collect(Collectors.toSet());

            if (superClasses.isEmpty() || superClasses.contains(thing)) {
                roots.add(cls);
            }
        }
        return roots;
    }

    private boolean isLeafClass(OWLClass cls, OWLOntology ontology) {
        return EntitySearcher.getSubClasses(cls, ontology)
                .noneMatch(ce -> ce.classesInSignature()
                        .anyMatch(sub -> !sub.isOWLThing() && !sub.isOWLNothing()));
    }
}