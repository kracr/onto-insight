package com.calculation_engine.oquareMetrics;

import org.semanticweb.owlapi.model.OWLOntology;
import org.semanticweb.owlapi.search.EntitySearcher;

import com.calculation_engine.MetricCalculator;
import com.calculation_engine.OntologyUtils;

import java.util.stream.Collectors;
import java.util.Collection;
import java.util.Set;
import java.util.TreeSet;

import org.semanticweb.owlapi.model.OWLClass;

import uk.ac.manchester.cs.owl.owlapi.OWLDataFactoryImpl;

public class CBOntoCalculator implements MetricCalculator {


    @Override
    public double calculate(OWLOntology ontology) {
        int superClassCount = 0;
        Set<OWLClass> classes = ontology.getClassesInSignature();
        Set<OWLClass> rootClasses = new TreeSet<>();

        for (OWLClass cls : classes) {
            Collection<OWLClass> superClassesOfOwlClass = OntologyUtils
                .classExpr2classes(EntitySearcher.getSuperClasses(cls, ontology).collect(Collectors.toSet()));

            superClassCount += superClassesOfOwlClass.size();

            if ((superClassesOfOwlClass.isEmpty() || superClassesOfOwlClass.contains(new OWLDataFactoryImpl().getOWLThing())) 
                && !cls.isOWLThing()) {
                rootClasses.add(cls);
            }
        }

        return (double) superClassCount / (classes.size() - rootClasses.size());
    }
}
