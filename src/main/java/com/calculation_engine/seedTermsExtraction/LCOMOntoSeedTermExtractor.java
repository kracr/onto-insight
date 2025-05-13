package com.calculation_engine.seedTermsExtraction;

import org.semanticweb.owlapi.model.*;
import org.semanticweb.owlapi.reasoner.*;
import org.semanticweb.owlapi.reasoner.structural.StructuralReasonerFactory;
import org.semanticweb.owlapi.search.EntitySearcher;

import java.util.*;
import java.util.stream.Collectors;

public class LCOMOntoSeedTermExtractor implements SeedTermExtractor {

    @Override
    public Set<OWLClass> getSeedTerms(OWLOntology ontology) {
        OWLReasonerFactory reasonerFactory = new StructuralReasonerFactory();
        OWLReasoner reasoner = reasonerFactory.createReasoner(ontology);

        Set<OWLClass> leafClasses = getLeafClasses(ontology);
        Map<OWLClass, Integer> pathLengths = new HashMap<>();

        // Calculate path lengths for all leaves
        leafClasses.forEach(leaf -> pathLengths.put(leaf, getPathLength(leaf, reasoner)));

        // Sort leaves by path length (ascending order)
        List<OWLClass> sortedLeaves = leafClasses.stream()
                .sorted(Comparator.comparingInt(pathLengths::get))
                .collect(Collectors.toList());

        // Select the top 2 leaves with the shortest paths
        Set<OWLClass> seedTerms = new HashSet<>();
        int limit = Math.min(2, sortedLeaves.size());
        for (int i = 0; i < limit; i++) {
            seedTerms.add(sortedLeaves.get(i));
        }

        reasoner.dispose();
        return seedTerms;
    }

    private Set<OWLClass> getLeafClasses(OWLOntology ontology) {
        return ontology.classesInSignature()
                .filter(cls -> EntitySearcher.getSubClasses(cls, ontology)
                        .noneMatch(ce -> !ce.isAnonymous()))
                .collect(Collectors.toSet());
    }

    private int getPathLength(OWLClass cls, OWLReasoner reasoner) {
        return getPathLengthHelper(cls, reasoner, new HashSet<>());
    }

    private int getPathLengthHelper(OWLClass cls,
            OWLReasoner reasoner,
            Set<OWLClass> visited) {
        if (visited.contains(cls))
            return 0;
        visited.add(cls);

        return reasoner.getSuperClasses(cls, true).entities()
                .mapToInt(superCls -> 1 + getPathLengthHelper(superCls, reasoner, visited))
                .max()
                .orElse(0);
    }
}