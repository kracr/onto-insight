package com.calculation_engine.seedTermsExtraction;

import org.semanticweb.owlapi.model.*;
import java.util.*;
import java.util.AbstractMap.SimpleEntry;
import org.semanticweb.owlapi.search.EntitySearcher;
import uk.ac.manchester.cs.owl.owlapi.OWLDataFactoryImpl;

public class POntoSeedTermExtractor implements SeedTermExtractor {

    @Override
    public Set<OWLClass> getSeedTerms(OWLOntology ontology) {
        Set<OWLClass> classes = ontology.getClassesInSignature();
        OWLClass thing = new OWLDataFactoryImpl().getOWLThing();

        return classes.stream()
                .filter(cls -> !cls.equals(thing))
                .filter(cls -> !isLeafClass(cls, ontology))
                .map(cls -> new SimpleEntry<>(cls, countMeaningfulSuperclasses(cls, ontology)))
                .sorted(Comparator.comparingInt(Map.Entry::getValue))
                .findFirst()
                .map(entry -> Collections.singleton(entry.getKey()))
                .orElse(Collections.emptySet());
    }

    private int countMeaningfulSuperclasses(OWLClass cls, OWLOntology ontology) {
        OWLClass thing = new OWLDataFactoryImpl().getOWLThing();
        return (int) EntitySearcher.getSuperClasses(cls, ontology)
                .flatMap(ce -> ce.classesInSignature())
                .filter(sup -> !sup.equals(thing))
                .count();
    }

    private boolean isLeafClass(OWLClass cls, OWLOntology ontology) {
        return EntitySearcher.getSubClasses(cls, ontology)
                .noneMatch(ce -> ce.classesInSignature()
                        .anyMatch(sub -> !sub.isOWLThing() && !sub.isOWLNothing()));
    }
}