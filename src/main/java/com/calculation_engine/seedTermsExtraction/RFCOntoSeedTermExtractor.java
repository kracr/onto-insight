package com.calculation_engine.seedTermsExtraction;

import org.semanticweb.owlapi.model.*;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.Collectors;
import uk.ac.manchester.cs.owl.owlapi.OWLDataFactoryImpl;
import org.semanticweb.owlapi.search.EntitySearcher;

public class RFCOntoSeedTermExtractor implements SeedTermExtractor {

    @Override
    public Set<OWLClass> getSeedTerms(OWLOntology ontology) {
        Set<OWLClass> classes = ontology.getClassesInSignature();
        Set<OWLClass> rootClasses = getRootClasses(ontology);
        int totalClasses = classes.size();
        int rootClassesCount = rootClasses.size();
        double denominator = totalClasses - rootClassesCount;

        if (denominator <= 0)
            return Collections.emptySet();

        Set<OWLClass> candidateClasses = classes.stream()
                .filter(cls -> !isLeafClass(cls, ontology))
                .collect(Collectors.toSet());

        if (candidateClasses.isEmpty())
            return Collections.emptySet();

        Map<OWLClass, Double> rfcScores = new HashMap<>();

        for (OWLClass cls : candidateClasses) {
            Set<OWLClass> hierarchy = getFullHierarchy(cls, ontology);
            int[] axiomCounts = calculateAxiomUsage(hierarchy, ontology);
            double rfc = (axiomCounts[0] + axiomCounts[1] + axiomCounts[2]) / denominator;
            rfcScores.put(cls, rfc);
        }

        return rfcScores.entrySet().stream()
                .sorted(Map.Entry.comparingByValue())
                .findFirst()
                .map(e -> Collections.singleton(e.getKey()))
                .orElse(Collections.emptySet());
    }

    // KEY IMPROVEMENT: Include both super and subclasses in hierarchy
    private Set<OWLClass> getFullHierarchy(OWLClass cls, OWLOntology ontology) {
        Set<OWLClass> hierarchy = new HashSet<>();
        Deque<OWLClass> toProcess = new ArrayDeque<>();
        toProcess.add(cls);

        while (!toProcess.isEmpty()) {
            OWLClass current = toProcess.poll();

            if (hierarchy.add(current)) {
                // Add superclasses
                EntitySearcher.getSuperClasses(current, ontology)
                        .flatMap(ce -> ce.classesInSignature())
                        .filter(sup -> !sup.isOWLThing())
                        .forEach(sup -> {
                            if (!hierarchy.contains(sup))
                                toProcess.add(sup);
                        });

                // Add subclasses
                EntitySearcher.getSubClasses(current, ontology)
                        .flatMap(ce -> ce.classesInSignature())
                        .filter(sub -> !sub.isOWLThing())
                        .forEach(sub -> {
                            if (!hierarchy.contains(sub))
                                toProcess.add(sub);
                        });
            }
        }
        return hierarchy;
    }

    private boolean isLeafClass(OWLClass cls, OWLOntology ontology) {
        return EntitySearcher.getSubClasses(cls, ontology)
                .noneMatch(ce -> !ce.isOWLNothing());
    }

    // private Set<OWLClass> getClassHierarchy(OWLClass cls, OWLOntology ontology) {
    // Set<OWLClass> hierarchy = new HashSet<>();
    // Queue<OWLClass> queue = new LinkedList<>();
    // queue.add(cls);

    // while (!queue.isEmpty()) {
    // OWLClass current = queue.poll();
    // if (hierarchy.add(current)) {
    // Set<OWLClass> subs = EntitySearcher.getSubClasses(current, ontology)
    // .flatMap(ce -> ce.classesInSignature())
    // .filter(sub -> !sub.isOWLThing())
    // .collect(Collectors.toSet());
    // queue.addAll(subs);
    // }
    // }
    // return hierarchy;
    // }

    private int[] calculateAxiomUsage(Set<OWLClass> hierarchy, OWLOntology ontology) {
        AtomicInteger subclassCount = new AtomicInteger();
        AtomicInteger dataProps = new AtomicInteger();
        AtomicInteger objProps = new AtomicInteger();

        for (OWLClass cls : hierarchy) {
            subclassCount.addAndGet(ontology.getSubClassAxiomsForSubClass(cls).size());
            processClassAxioms(cls, ontology, dataProps, objProps);
        }

        return new int[] {
                subclassCount.get(),
                dataProps.get(),
                objProps.get()
        };
    }

    private void processClassAxioms(OWLClass cls, OWLOntology ontology,
            AtomicInteger dataProps, AtomicInteger objProps) {
        // Process SubClassOf axioms
        for (OWLSubClassOfAxiom axiom : ontology.getSubClassAxiomsForSubClass(cls)) {
            processExpression(axiom.getSuperClass(), dataProps, objProps);
        }

        // Process EquivalentClasses axioms
        for (OWLEquivalentClassesAxiom axiom : ontology.getEquivalentClassesAxioms(cls)) {
            for (OWLClassExpression expr : axiom.getClassExpressions()) {
                if (!expr.equals(cls)) {
                    processExpression(expr, dataProps, objProps);
                }
            }
        }
    }

    private void processExpression(OWLClassExpression expr,
            AtomicInteger dataProps, AtomicInteger objProps) {
        expr.signature().forEach(entity -> {
            if (entity.isOWLDataProperty())
                dataProps.incrementAndGet();
            if (entity.isOWLObjectProperty())
                objProps.incrementAndGet();
        });
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