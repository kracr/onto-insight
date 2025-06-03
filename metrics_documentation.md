## Quality Metrics

The tool evaluates ontologies using 16 OQuaRE metrics mapped to 26 ISO/IEC 25010 sub-characteristics. Each metric is scored from 1 (worst) to 5 (best).

### Metric Descriptions and Ranges

#### Structural Metrics

1. **ANOnto (Annotation Richness)**

   - Description: Measures the mean number of annotations per class
   - Best Score: > 0.8
   - Worst Score: < 0.2
   - Formula: (annotationAsserionAxioms + generalAnnotationAxioms)/classes

2. **AROnto (Attribute Richness)**

   - Description: Measures the mean number of attributes per class
   - Best Score: > 0.8
   - Worst Score: < 0.2
   - Formula: (dataPropertyDomainAxioms + objectPropertyDomainAxioms)/classes

3. **CBOnto (Coupling Between Objects)**

   - Description: Quantifies the number of related classes
   - Best Score: 1-3
   - Worst Score: > 12
   - Formula: superClasses/(classes-rootClasses)

4. **CROnto (Class Richness)**

   - Description: Evaluates the mean number of instances per class
   - Best Score: > 0.8
   - Worst Score: < 0.2
   - Formula: classAssertionAxioms/classes

5. **DITOnto (Depth of Inheritance Tree)**

   - Description: Measures the length of the longest path from root to leaf
   - Best Score: 1-2
   - Worst Score: > 8
   - Formula: maximalDepth

6. **INROnto (Inheritance Richness)**

   - Description: Calculates the mean number of relationships per class
   - Best Score: > 0.8
   - Worst Score: < 0.2
   - Formula: subClassOfAxioms/classes

7. **LCOMOnto (Lack of Cohesion in Methods)**

   - Description: Measures semantic and conceptual relatedness of classes
   - Best Score: ≤ 2
   - Worst Score: > 8
   - Formula: Summation of Length of Path i from root to leaf/Summation of leaf classes i

8. **NACOnto (Number of Ancestors)**

   - Description: Calculates mean number of ancestor classes per leaf
   - Best Score: 1-2
   - Worst Score: > 8
   - Formula: superClassesOfLeafClasses/absoluteLeafCardinality

9. **NOCOnto (Number of Children)**

   - Description: Measures mean number of direct subclasses per class
   - Best Score: 1-2
   - Worst Score: > 8
   - Formula: subClassOfAxioms/(classes - rootClasses)

10. **NOMOnto (Number of Methods)**

    - Description: Calculates average number of properties per class
    - Best Score: ≤ 2
    - Worst Score: > 8
    - Formula: (dataPropertyAssertionAxioms + objectPropertiesOnClasses)/classes

11. **PONTO (Parents per Class)**

    - Description: Represents ancestors per class
    - Best Score: > 0.8
    - Worst Score: < 0.2
    - Formula: superClasses/classes

12. **PRONTO (Property Ratio)**

    - Description: Ratio of subclass relationships to total relationships
    - Best Score: > 0.8
    - Worst Score: < 0.2
    - Formula: subClassOfAxioms/(dataPropertyAssertionAxioms+objectPropertiesOnClasses+subClassOfAxioms)

13. **RFCOnto (Response for a Class)**

    - Description: Measures number of properties directly accessible from each class
    - Best Score: 1-3
    - Worst Score: > 12
    - Formula: (subClassOfAxioms/(classes-rootClasses))\*(datapropertyAssertionAxioms+objectPropertyOnClasses)

14. **RROnto (Relationship Richness)**

    - Description: Evaluates number of properties relative to total relationships
    - Best Score: > 0.8
    - Worst Score: < 0.2
    - Formula: (dataPropertyAssertionAxioms+objectPropertiesOnClasses)/(dataPropertyAssertionAxioms+objectPropertiesOnClasses+subClassOfAxioms)

15. **TMOnto (Tree Metric)**

    - Description: Evaluates mean number of parents per class
    - Best Score: 1-2
    - Worst Score: > 8
    - Formula: superClasses/classes

16. **WMCOnto (Weighted Method Count)**
    - Description: Calculates mean number of properties and relationships per class
    - Best Score: 1-2
    - Worst Score: > 8
    - Formula: (dataPropertyAssertionAxioms+objectPropertiesOnClasses+subClassOfAxioms)/classes

### Sub-characteristics

The metrics are mapped to 24 sub-characteristics across 8 quality characteristics:

#### Structural Characteristics

- **Formal Relations Support (C1.2)**

  - Formula: +RROnto
  - Best Score: > 0.8
  - Worst Score: < 0.2

- **Redundancy (C1.3)**

  - Formula: +ANOnto
  - Best Score: > 0.8
  - Worst Score: < 0.2

- **Tangledness (C1.6)**

  - Formula: -TMOnto
  - Best Score: > 8
  - Worst Score: 1-2

- **Cohesion (C1.8)**
  - Formula: -LCOMOnto
  - Best Score: > 8
  - Worst Score: ≤ 2

#### Functional Adequacy Characteristics

- **Controlled Vocabulary (C2.2)**

  - Formula: +ANOnto
  - Best Score: > 0.8
  - Worst Score: < 0.2

- **Schema & Value Reconciliation (C2.3)**

  - Formula: AROnto+RROnto
  - Best Score: > 1.6
  - Worst Score: < 0.4

- **Consistent Search & Query (C2.4)**

  - Formula: ANOnto+AROnto+INROnto+RROnto
  - Best Score: > 3.2
  - Worst Score: < 0.8

- **Knowledge Acquisition (C2.5)**

  - Formula: ANOnto+RROnto-NOMOnto
  - Best Score: > 9.6
  - Worst Score: ≤ 2.4

- **Clustering (C2.6)**

  - Formula: +ANOnto
  - Best Score: > 0.8
  - Worst Score: < 0.2

- **Similarity (C2.7)**

  - Formula: AROnto+RROnto
  - Best Score: > 1.6
  - Worst Score: < 0.4

- **Indexing & Linking (C2.8)**

  - Formula: AROnto+RROnto+INROnto
  - Best Score: > 2.4
  - Worst Score: < 0.6

- **Result Representation (C2.9)**

  - Formula: AROnto+CROnto
  - Best Score: > 1.6
  - Worst Score: < 0.4

- **Guidance (C2.12)**

  - Formula: AROnto+INROnto
  - Best Score: > 1.6
  - Worst Score: < 0.4

- **Decision Trees (C2.13)**

  - Formula: AROnto+INROnto-TMOnto
  - Best Score: > 9.6
  - Worst Score: < 2.4

- **Knowledge Reuse (C2.14)**

  - Formula: ANOnto+AROnto+INROnto-NOMOnto-LCOMOnto
  - Best Score: > 18.4
  - Worst Score: ≤ 4.6

- **Inference (C2.15)**
  - Formula: RROnto+CROnto
  - Best Score: > 1.6
  - Worst Score: < 0.4

#### Compatibility Characteristics

- **Replaceability (C3.1)**
  - Formula: -DITOnto-NOCOnto-NOMOnto-WMCOnto
  - Best Score: > 32
  - Worst Score: ≤ 8

#### Transferability Characteristics

- **Adaptability (C4.2)**
  - Formula: -CBOOnto-DITOnto-NOCOnto-NOMOnto-RFCOnto-WMCOnto
  - Best Score: > 56
  - Worst Score: ≤ 14

#### Operability Characteristics

- **Learnability (C5.2)**
  - Formula: -CBOnto-NOCOnto-NOMOnto-LCOMOnto-RFCOnto-WMCOnto
  - Best Score: > 56
  - Worst Score: ≤ 14

#### Maintainability Characteristics

- **Modularity (C6.1)**

  - Formula: -CBOnto-WMCOnto
  - Best Score: > 20
  - Worst Score: 2-5

- **Reusability (C6.2)**

  - Formula: -CBOnto-DITOnto-NOCOnto-NOMOnto-RFCOnto-WMCOnto
  - Best Score: > 56
  - Worst Score: ≤ 14

- **Analyzability (C6.3)**

  - Formula: -CBOnto-DITOnto-NOMOnto-LCOMOnto-RFCOnto-WMCOnto
  - Best Score: > 56
  - Worst Score: ≤ 14

- **Changeability (C6.4)**

  - Formula: -CBOnto-DITOnto-NOCOnto-NOMOnto-LCOMOnto-RFCOnto-WMCOnto
  - Best Score: > 64
  - Worst Score: ≤ 16

- **Modification Stability (C6.5)**
  - Formula: -CBOnto-NOCOnto-LCOMOnto-RFCOnto
  - Best Score: > 40
  - Worst Score: ≤ 10

### Beginner-Friendly Metric Glossary

#### Core Metrics

- **Property Binding (AROnto)**: Average domain axioms per class
- **Annotation Richness (ANOnto)**: Average annotations per class
- **Coupling (CBOnto)**: Average superclasses per non-root class
- **Class Population (CROnto)**: Average instances per class
- **Hierarchy Depth (DITOnto)**: Maximum depth from root to leaf class
- **Relationship Density (INROnto)**: Average object properties per class
- **Ancestral Depth (NACOnto)**: Average ancestor classes per leaf
- **Child Breadth (NOCOnto)**: Average child classes per class
- **Property Variety (NOMOnto)**: Average number of properties per class
- **Cohesion Loss (LCOMOnto)**: Measures how scattered the connections are
- **Property Usage (RFCOnto)**: Average usage of properties per class
- **Link Expressiveness (RROnto)**: Ratio of relationships to total axioms
- **Multi-Inheritance (TMOnto)**: Average number of superclasses per class
- **Schema Density (WMCOnto)**: Average datatype/object properties and subclasses per class
- **Linkable Elements (PROnto)**: Linkable elements based on domain axioms
- **Ancestral Breadth (POnto)**: Superclasses per class

#### Sub-characteristics

- **Relation Formality (C1.2)**: Ontology supports formal relations beyond taxonomy
- **Non-Redundancy (C1.3)**: All knowledge items are informative
- **Inheritance Simplicity (C1.6)**: Multi-inheritance is minimized
- **Class Cohesion (C1.8)**: Classes are strongly related
- **Term Uniformity (C2.2)**: Heterogeneity of terms is avoided
- **Interoperability (C2.3)**: Provides a common data model
- **Query Support (C2.4)**: Ontology structure guides search/query
- **Knowledge Capturing (C2.5)**: Capability to represent acquired knowledge
- **Term Grouping (C2.6)**: Annotations enable grouping of terms
- **Comparability (C2.7)**: Components can be compared for similarity
- **Indexability (C2.8)**: Classes serve as indexes for retrieval
- **Output Analysis (C2.9)**: Can analyze complex results
- **Domain Guidance (C2.12)**: Guides specification of domain knowledge
- **Decision Support (C2.13)**: Supports building decision trees
- **Reusability (C2.14)**: Ontology can be used to build other ontologies
- **Inference Capability (C2.15)**: Enables using reasoners to infer new knowledge
- **Ontology Replacement (C3.1)**: Can replace another ontology for same task
- **Adaptability (C4.2)**: Can be adapted to different environments
- **Learnability (C5.2)**: Users can easily learn the ontology
- **Component Separation (C6.1)**: Ontology is divided into independent components
- **Reuse in Others (C6.2)**: Parts can be reused in other ontologies
- **Issue Diagnosability (C6.3)**: Can be diagnosed for issues
- **Modifiability (C6.4)**: Can be easily modified
- **Stability on Change (C6.5)**: Avoids unexpected effects of changes
