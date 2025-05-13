package com.calculation_engine.seedTermsExtraction;

import org.semanticweb.owlapi.model.*;
import java.util.*;
import org.semanticweb.owlapi.search.EntitySearcher;
import uk.ac.manchester.cs.owl.owlapi.OWLDataFactoryImpl;

public class NOCOntoSeedTermExtractor implements SeedTermExtractor {

    @Override
    public Set<OWLClass> getSeedTerms(OWLOntology ontology) {
        Set<OWLClass> classes = ontology.getClassesInSignature();
        Set<OWLClass> rootClasses = getRootClasses(ontology);
        int denominator = classes.size() - rootClasses.size();

        if (denominator <= 0)
            return Collections.emptySet();

        Map<OWLClass, Double> nocScores = new HashMap<>();

        for (OWLClass cls : classes) {
            if (cls.isOWLThing())
                continue;

            Set<OWLClass> subclasses = getTransitiveSubclasses(cls, ontology);
            if (subclasses.isEmpty())
                continue; // Skip leaf classes

            double noc = (double) subclasses.size() / denominator;
            nocScores.put(cls, noc);
        }

        return nocScores.entrySet().stream()
                .sorted(Map.Entry.<OWLClass, Double>comparingByValue().reversed())
                .findFirst()
                .map(entry -> Collections.singleton(entry.getKey()))
                .orElse(Collections.emptySet());
    }

    private Set<OWLClass> getTransitiveSubclasses(OWLClass cls, OWLOntology ontology) {
        Set<OWLClass> subclasses = new HashSet<>();
        Queue<OWLClass> queue = new LinkedList<>();

        EntitySearcher.getSubClasses(cls, ontology)
                .flatMap(ce -> ce.classesInSignature())
                .filter(sub -> !sub.isOWLThing())
                .forEach(queue::add);

        while (!queue.isEmpty()) {
            OWLClass current = queue.poll();
            if (subclasses.add(current)) {
                EntitySearcher.getSubClasses(current, ontology)
                        .flatMap(ce -> ce.classesInSignature())
                        .filter(sub -> !sub.isOWLThing())
                        .forEach(queue::add);
            }
        }
        return subclasses;
    }

    private Set<OWLClass> getRootClasses(OWLOntology ontology) {
        Set<OWLClass> roots = new HashSet<>();
        OWLClass thing = new OWLDataFactoryImpl().getOWLThing();

        for (OWLClass cls : ontology.getClassesInSignature()) {
            if (cls.isOWLThing())
                continue;

            boolean hasNonThingSuper = EntitySearcher.getSuperClasses(cls, ontology)
                    .flatMap(ce -> ce.classesInSignature())
                    .anyMatch(sup -> !sup.equals(thing));

            if (!hasNonThingSuper)
                roots.add(cls);
        }
        return roots;
    }
}