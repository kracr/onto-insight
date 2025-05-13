package com.calculation_engine.seedTermsExtraction;

import org.semanticweb.owlapi.model.*;
import java.util.*;
import uk.ac.manchester.cs.owl.owlapi.OWLDataFactoryImpl;
import org.semanticweb.owlapi.search.EntitySearcher;

public class NACOntoSeedTermExtractor implements SeedTermExtractor {

    @Override
    public Set<OWLClass> getSeedTerms(OWLOntology ontology) {
        Set<OWLClass> classes = ontology.getClassesInSignature();
        Map<OWLClass, Integer> leafAncestorCounts = new HashMap<>();
        OWLClass thing = new OWLDataFactoryImpl().getOWLThing();

        for (OWLClass cls : classes) {
            if (cls.isOWLThing())
                continue;

            // Check if leaf class (no direct named subclasses)
            boolean isLeaf = EntitySearcher.getSubClasses(cls, ontology)
                    .flatMap(ce -> ce.classesInSignature())
                    .noneMatch(sub -> !sub.equals(thing));

            if (isLeaf) {
                // Count explicit named superclasses
                int ancestorCount = (int) EntitySearcher.getSuperClasses(cls, ontology)
                        .flatMap(ce -> ce.classesInSignature())
                        .filter(sup -> !sup.equals(thing))
                        .count();

                leafAncestorCounts.put(cls, ancestorCount);
            }
        }

        return leafAncestorCounts.entrySet().stream()
                .sorted(Map.Entry.comparingByValue())
                .findFirst()
                .map(entry -> Collections.singleton(entry.getKey()))
                .orElse(Collections.emptySet());
    }
}