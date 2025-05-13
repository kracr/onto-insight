package com.calculation_engine.oquareMetrics;

import java.util.Set;
import org.semanticweb.owlapi.model.*;
import org.semanticweb.owlapi.search.EntitySearcher;

import com.calculation_engine.MetricCalculator;
import com.calculation_engine.OntologyUtils;

import java.util.Collection;
import java.util.TreeSet;
import uk.ac.manchester.cs.owl.owlapi.OWLDataFactoryImpl;

import java.util.stream.Collectors;

public class RFCOntoCalculator implements MetricCalculator {

    @Override
    public double calculate(OWLOntology ontology) {
        Set<OWLClass> classes = ontology.getClassesInSignature();
        Set<OWLClass> rootClasses = getRootClasses(ontology);

        int subClassOfAxioms = ontology.getAxiomCount(AxiomType.SUBCLASS_OF);
        int dataPropertyAssertionAxioms = ontology.getAxiomCount(AxiomType.DATA_PROPERTY_ASSERTION);
        int objectPropertiesOnClasses = countObjectPropertiesOnClasses(ontology);

        double denominator = classes.size() - rootClasses.size();
        if (denominator == 0) {
            return 0; // Avoid division by zero
        }

        double RFCOnto = ((double) subClassOfAxioms / denominator) 
                         * (dataPropertyAssertionAxioms + objectPropertiesOnClasses);

        return RFCOnto;
    }

    private Set<OWLClass> getRootClasses(OWLOntology ontology) {
        Set<OWLClass> rootClasses = new TreeSet<>();
        Set<OWLClass> classes = ontology.getClassesInSignature();

        for (OWLClass owlClass : classes) {
            Collection<OWLClass> superClasses = OntologyUtils.classExpr2classes(
                EntitySearcher.getSuperClasses(owlClass, ontology).collect(Collectors.toList())
            );
            if ((superClasses.isEmpty() || superClasses.contains(new OWLDataFactoryImpl().getOWLThing())) 
                && !owlClass.isOWLThing()) {
                rootClasses.add(owlClass);
            }
        }
        return rootClasses;
    }

    private int countObjectPropertiesOnClasses(OWLOntology ontology) {
        int count = 0;
        for (OWLClass owlClass : ontology.getClassesInSignature()) {
            for (OWLSubClassOfAxiom axiom : ontology.getSubClassAxiomsForSubClass(owlClass)) {
                count += axiom.getObjectPropertiesInSignature().size();
            }
        }
        return count;
    }
}
