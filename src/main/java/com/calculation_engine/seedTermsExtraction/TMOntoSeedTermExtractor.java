package com.calculation_engine.seedTermsExtraction;

import org.semanticweb.owlapi.model.*;
import java.util.*;
import uk.ac.manchester.cs.owl.owlapi.OWLDataFactoryImpl;
import org.semanticweb.owlapi.search.EntitySearcher;

public class TMOntoSeedTermExtractor implements SeedTermExtractor {

    @Override
    public Set<OWLClass> getSeedTerms(OWLOntology ontology) {
        Set<OWLClass> classes = ontology.getClassesInSignature();
        Map<OWLClass, Integer> superClassCounts = new HashMap<>();
        OWLClass thing = new OWLDataFactoryImpl().getOWLThing();

        for (OWLClass cls : classes) {
            if (cls.isOWLThing())
                continue;

            int count = (int) EntitySearcher.getSuperClasses(cls, ontology)
                    .flatMap(ce -> ce.classesInSignature())
                    .filter(sup -> !sup.equals(thing))
                    .count();

            superClassCounts.put(cls, count);
        }

        return superClassCounts.entrySet().stream()
                .sorted(Map.Entry.<OWLClass, Integer>comparingByValue().reversed())
                .findFirst()
                .map(entry -> Collections.singleton(entry.getKey()))
                .orElse(Collections.emptySet());
    }
}