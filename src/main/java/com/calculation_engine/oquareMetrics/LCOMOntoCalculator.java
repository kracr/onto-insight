package com.calculation_engine.oquareMetrics;

import org.semanticweb.owlapi.model.OWLClass;
import org.semanticweb.owlapi.model.OWLOntology;
import org.semanticweb.owlapi.search.EntitySearcher;

import com.calculation_engine.MetricCalculator;

import org.semanticweb.owlapi.reasoner.OWLReasoner;
import org.semanticweb.owlapi.reasoner.OWLReasonerFactory;
import org.semanticweb.owlapi.reasoner.structural.StructuralReasonerFactory;

import java.util.Set;
import java.util.HashSet;
import java.util.stream.Collectors;

public class LCOMOntoCalculator implements MetricCalculator {

    @Override
    public double calculate(OWLOntology ontology) {
        OWLReasonerFactory reasonerFactory = new StructuralReasonerFactory();
        OWLReasoner reasoner = reasonerFactory.createReasoner(ontology);
        double LCOMOnto = 0.0;
        Set<OWLClass> classes = ontology.getClassesInSignature();
        int totalPathLength = 0;
        int totalLeaves = 0;

        Set<OWLClass> leafClasses = classes.stream()
            .filter(cls -> EntitySearcher.getSubClasses(cls, ontology).collect(Collectors.toSet()).stream().noneMatch(sub -> !sub.isAnonymous()))
            .collect(Collectors.toSet());

        for (OWLClass leaf : leafClasses) {
            int pathLength = getPathLength(leaf, ontology, reasoner);
            totalPathLength += pathLength;
            totalLeaves++;
        }

        if (totalLeaves != 0) {
            LCOMOnto = (double) totalPathLength / totalLeaves;
        }

        reasoner.dispose();
        return LCOMOnto;
    }

    private int getPathLength(OWLClass cls, OWLOntology ontology, OWLReasoner reasoner) {
        Set<OWLClass> visited = new HashSet<>();
        return getPathLengthHelper(cls, ontology, reasoner, visited);
    }

    private int getPathLengthHelper(OWLClass cls, OWLOntology ontology, OWLReasoner reasoner, Set<OWLClass> visited) {
        int length = 0;
        visited.add(cls);
        Set<OWLClass> superClasses = reasoner.getSuperClasses(cls, true).getFlattened();
        for (OWLClass superClass : superClasses) {
            if (!visited.contains(superClass)) {
                length = 1 + getPathLengthHelper(superClass, ontology, reasoner, visited);
            }
        }
        return length;
    }
}
