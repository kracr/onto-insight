package com.calculation_engine;

import java.util.Collection;
import java.util.Set;
import java.util.TreeSet;

import org.semanticweb.owlapi.model.OWLClass;
import org.semanticweb.owlapi.model.OWLClassExpression;

public class OntologyUtils {
    public static Collection<OWLClass> classExpr2classes(Collection<OWLClassExpression> classExpressions) {
	Set<OWLClass> classes = new TreeSet<OWLClass>();

        for (OWLClassExpression classExpression : classExpressions) {
            if(classExpression instanceof OWLClass)
            classes.addAll(classExpression.getClassesInSignature());
        }
	    return classes;
    }

    

}