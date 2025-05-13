package com.calculation_engine.oquareMetrics;

import java.util.Collection;
import java.util.Set;
import java.util.TreeSet;
import java.util.stream.Collectors;

import org.semanticweb.owlapi.model.OWLClass;
import org.semanticweb.owlapi.model.OWLClassExpression;
import org.semanticweb.owlapi.model.OWLOntology;
import org.semanticweb.owlapi.search.EntitySearcher;

import com.calculation_engine.MetricCalculator;

public class NACOntoCalculator implements MetricCalculator {

    @Override
    public double calculate(OWLOntology ontology) {
        double NACOnto = 0;
        Set<OWLClass> leafClasses = new TreeSet<OWLClass>();
        Set<OWLClass> classes = ontology.getClassesInSignature();

        for (OWLClass owlClass : classes) {
            Collection<OWLClassExpression> subClassExpr = EntitySearcher.getSubClasses(owlClass, ontology)
                    .collect(Collectors.toSet());
            Collection<OWLClass> subClasses = classExpr2classes(subClassExpr);

            if (subClasses.size() < 1) {
                leafClasses.add(owlClass);
            }
        }

        int superClassesOfLeafClasses = 0;
        for (OWLClass owlClass : leafClasses) {
            Collection<OWLClassExpression> superClassOfLeafClass = EntitySearcher.getSuperClasses(owlClass, ontology)
                    .collect(Collectors.toSet());
            superClassesOfLeafClasses += classExpr2classes(superClassOfLeafClass).size();
        }

        if (!classes.isEmpty()) {
            NACOnto = (double) superClassesOfLeafClasses / leafClasses.size();
        }

        return NACOnto;

    }

    private Collection<OWLClass> classExpr2classes(Collection<OWLClassExpression> classExpressions) {
        Set<OWLClass> classes = new TreeSet<>();

        for (OWLClassExpression classExpression : classExpressions) {
            if (classExpression instanceof OWLClass) {
                classes.add((OWLClass) classExpression);
            }
        }
        return classes;
    }

}
