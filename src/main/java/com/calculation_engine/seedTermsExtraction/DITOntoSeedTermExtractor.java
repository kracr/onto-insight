package com.calculation_engine.seedTermsExtraction;

import org.semanticweb.owlapi.model.*;
import java.util.*;
import java.util.stream.Collectors;
import org.semanticweb.owlapi.search.EntitySearcher;

public class DITOntoSeedTermExtractor implements SeedTermExtractor {

    @Override
    public Set<OWLClass> getSeedTerms(OWLOntology ontology) {
        Map<OWLClass, Integer> depthMap = new HashMap<>();
        Set<OWLClass> rootClasses = getRootClasses(ontology);

        // Calculate depths from all root classes
        for (OWLClass root : rootClasses) {
            computeDepthsFromRoot(root, ontology, depthMap);
        }

        // Filter out roots and find maximum depth
        OptionalInt maxDepth = depthMap.entrySet().stream()
                .filter(e -> !rootClasses.contains(e.getKey()))
                .mapToInt(Map.Entry::getValue)
                .max();

        if (!maxDepth.isPresent())
            return Collections.emptySet();

        // Select all classes with maximum depth
        return depthMap.entrySet().stream()
                .filter(e -> e.getValue() == maxDepth.getAsInt())
                .filter(e -> !rootClasses.contains(e.getKey()))
                .map(Map.Entry::getKey)
                .findFirst()
                .map(Collections::singleton)
                .orElse(Collections.emptySet());
    }

    private void computeDepthsFromRoot(OWLClass root, OWLOntology ontology,
            Map<OWLClass, Integer> depthMap) {
        Queue<OWLClass> queue = new LinkedList<>();
        Map<OWLClass, Integer> currentDepths = new HashMap<>();

        currentDepths.put(root, 1);
        queue.add(root);

        while (!queue.isEmpty()) {
            OWLClass current = queue.poll();
            int currentDepth = currentDepths.get(current);

            // Update global depth map if deeper path found
            if (currentDepth > depthMap.getOrDefault(current, 0)) {
                depthMap.put(current, currentDepth);
            }

            // Process subclasses
            Set<OWLClass> subClasses = EntitySearcher.getSubClasses(current, ontology)
                    .flatMap(ce -> ce.classesInSignature())
                    .filter(sub -> !sub.isOWLThing())
                    .collect(Collectors.toSet());

            for (OWLClass sub : subClasses) {
                int newDepth = currentDepth + 1;
                if (newDepth > currentDepths.getOrDefault(sub, 0)) {
                    currentDepths.put(sub, newDepth);
                    queue.add(sub);
                }
            }
        }
    }

    private Set<OWLClass> getRootClasses(OWLOntology ontology) {
        return ontology.getClassesInSignature().stream()
                .filter(cls -> !EntitySearcher.getSuperClasses(cls, ontology)
                        .findFirst().isPresent())
                .collect(Collectors.toSet());
    }
}