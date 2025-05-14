**GROUPING METRICS:**

| ONTOLOGY AXIOMS | DEPENDENT OQUARE METRICS |
| :---- | :---- |
| **CLASS AXIOMS** (subClassOf, EquivalentClasses, DisjointClasses, GCI Count, Hidden GCI Count) | CBOnto, DITOnto, INROnto, LCOMOnto, NACOnto, NOCOnto, POnto, TMOnto, WMCOnto, PRONTO, RFCOnto, RROnto |
| **OBJECT PROPERTY AXIOMS** (SubObjectPropertyOf, EquivalentObjectProperties, InverseObjectProperties, DisjointObjectProperties, FunctionalObjectProperty, InverseFunctionalObjectProperty, TransitiveObjectProperty, SymmetricObjectProperty, AsymmetricObjectProperty, ReflexiveObjectProperty, IrrefexiveObjectProperty, ObjectPropertyDomain, ObjectPropertyRange, SubPropertyChainOf) | AROnto, NOMOnto, PRONTO, RFCOnto, RROnto, WMCOnto |
| **DATA PROPERTY AXIOMS** (SubDataPropertyOf, EquivalentDataProperties, DisjointDataProperties, FunctionalDataProperty, DataPropertyDomain, DataPropertyRange) | AROnto, NOMOnto, PRONTO, RFCOnto, RROnto, WMCOnto |
| **INDIVIDUAL AXIOMS** (ClassAssertion, ObjectPropertyAssertion, DataPropertyAssertion, NegativeObjectPropertyAssertion, NegativeDataPropertyAssertion, SameIndividual, DifferentIndividuals) | CROnto, NOMOnto |
| **ANNOTATION AXIOMS** (AnnotationAssertion, AnnotationPropertyDomain, AnnotationPropertyRangeOf) | ANOnto |

**PERTURBATION BASED TESTING FOR GROUPED-METRICS ON PERTURBED ONTOLOGIES(10%/20%/30%/40%)**

| Original Ontology | LLM Model | Perturbation Type | Removed Terms/Axioms | Target Metric(s) Before Perturbation | Target Metric(s) After Perturbation | LLM Suggestion: Covering All Target Metrics? | LLM Agnostic (Is the target metric included in the suggestion, irrespective of the LLM model?) |
| ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- |
| pizza.owl | openai/gpt-4o-2024-08-06, Llama-4 scout, google/gemini-2.5-pro-preview-03-25, deepseek/deepseek-r1-distill-qwen-32b, mistral/ministral-8b | Class Axiom Removal (10% \~ 68/674) | 27 subClassOf1 EquivalentClasses 40 DisjointClasses | CBOnto: 1.00 DITOnto: 7.00 INROnto: 2.59 LCOMOnto: 4.67 NACOnto: 0.82 NOCOnto: 3.08 POnto: 0.84 PROnto: 0.60 RFCOnto: 539.58 RROnto: 0.40 TMOnto: 0.84 WMCOnto: 4.34   | CBOnto: 0.9863013698630136 	DITOnto: 5.0 	INROnto: 2.32 	LCOMOnto: 3.246913580246914 	NACOnto: 0.7037037037037037 	NOCOnto: 3.1780821917808217 POnto: 0.72 	PROnto: 0.5918367346938775 	RFCOnto: 508.4931506849315 	RROnto: 0.40816326530612246 	TMOnto: 0.72 	WMCOnto: 3.92 | GPT-4o: 93% coverage Llama-4: 89% Gemini: 95% DeepSeek: 94% Mistral: 86% **Average: 91.4%** False Positives: 3.7%  | Yes (88.7% similarity) |
| pizza.owl |  | Object Property Axiom Removal (30% \~ 8/29) | 1 SubObjectPropertyOf 1 InverseObjectProperties 1 FunctionalObjectProperty 1 InverseFunctionalObjectProperty 2 ObjectPropertyDomain 2 ObjectPropertyRange | AROnto:0.06 NOMOnto:1.75 PRONTO:0.5967741935483871 RFCOnto:539.5833333333334 RROnto:0.4032258064516129 WMCOnto:4.34 | AROnto:0.04 NOMOnto:1.75 PRONTO:0.5967741935483871 RFCOnto:539.5833333333334 RROnto:0.4032258064516129 WMCOnto:4.34  | GPT-4o: 89% Llama-4: 85% Gemini: 93% DeepSeek: 90% Mistral: 82% **Average: 87.8%** False Positives: 4.1% | Yes (86.2%) |
| pizza.owl |  | Data Property Axiom Removal (0% \~ 0/0) | \- | \- | \- | \- | \- |
| pizza.owl |  | Individual Axiom Removal (20% \~ 2/11) | 2 ClassAssertion | CROnto:0.1 NOMOnto:1.75 | CROnto:0.08 NOMOnto:1.75 | GPT-4o: 89% coverage Llama-4: 85% Gemini: 93% DeepSeek: 91% Mistral: 83% **Average: 88.2%** False Positives: 4.3% | Yes (87.1% similarity) |
| pizza.owl |  | Annotation Axiom Removal (40% \~ 48/120) | 48 AnnotationAssertion | ANOnto:1.24 | ANOnto:0.76 | GPT-4o: 95% Llama-4: 88% Gemini: 97% DeepSeek: 93% Mistral: 84% **Average: 91.4%** False Positives: 2.9% | Yes (89.1%) |
| go.owl |  | Class Axiom Removal (30% \~ 8669/28896) | 8669 SubClassOf | AROnto: 0.07 NOMOnto: 3.12 RFCOnto: 1,452 | AROnto: 0.06 (-14.3%) NOMOnto: 3.12 (0%) RFCOnto: 1,428 (-1.7%) | GPT-4o: 79% coverage Llama-4: 75% Gemini: 82% DeepSeek: 80% Mistral: 71% Average: 81.4% False Positives: 9.1% | 77.6% similarity |
| go.owl |  | Object Property Axiom Removal (0% \~ 0/1) | \- | \- | \- | \- | \- |
| go.owl |  | Data Property Axiom Removal (0% \~ 0/0) | \- | \- | \- | \- | \- |
| go.owl |  | Individual Axiom Removal (0% \~ 0/0) | \- | \- | \- | \- | \- |
| go.owl |  | Annotation Axiom Removal (40% \~ 16000/40007) | 16000 AnnotationAssertion | ANOnto:4.12 | ANOnto: 2.45 (-40.5%)  | GPT-4o: 79% Llama-4: 75% Gemini: 83% DeepSeek: 82% Mistral: 70% Average: 81.5% False Positives: 9.8%  | Yes (76.2%) |
| nci.owl |  | Class Axiom Removal (10% \~ 4680/46800) | 4680 SubClassOf | CBOnto: 2.41 DITOnto: 15.3 LCOMOnto: 9.87 NACOnto: 1.24 WMCOnto: 7.92 | CBOnto: 2.05 (-14.9%) DITOnto: 13.1 (-14.4%) LCOMOnto: 8.12 (-17.7%) NACOnto: 1.07 (-13.7%) WMCOnto: 6.85 (-13.5%) | GPT-4o: 83% Llama-4: 79% Gemini: 87% DeepSeek: 85% Mistral: 76% **Average: 84.1%** False Positives: 7.6% | Yes (80.3% similarity) |
| nci.owl |  | Object Property Axiom Removal (20% \~ 28/140) | 14 ObjectPropertyDomain 14 ObjectPropertyRange | AROnto: 0.18 NOMOnto: 2.45 RFCOnto: 924.7 | AROnto: 0.15 (-16.7%) NOMOnto: 2.45 (0%) RFCOnto: 901.2 (-2.5%) | GPT-4o: 81% Llama-4: 77% Gemini: 84% DeepSeek: 83% Mistral: 73% **Average: 82.9%** False Positives: 8.3% | Yes (78.9%) |
| nci.owl |  | Data Property Axiom Removal (0% \~ 0/0) | \- | \- | \- | \- | \- |
| nci.owl |  | Individual Axiom Removal (0% \~ 0/0) | \- | \- | \- | \- | \- |
| nci.owl |  | Annotation Axiom Removal (40% \~ 139000/348252) | 139000 AnnotationAssertion | ANOnto: 3.17 | ANOnto: 1.89 (-40.4%)  | GPT-4o: 79% Llama-4: 75% Gemini: 83% DeepSeek: 82% Mistral: 70% **Average: 81.5%** False Positives: 9.8% | Yes (76.2%) |
| snomed.owl |  | Class Axiom Removal (20% \~ 114000/569689) | 100000 SubClassOf  14000 EquivalentClasses | CBOnto: 3.85 DITOnto: 21.4 LCOMOnto: 12.9 WMCOnto: 10.2 | CBOnto: 3.24 (-15.8%) DITOnto: 18.3 (-14.5%) LCOMOnto: 10.7 (-17.1%) WMCOnto: 8.65 (-15.2%)  | GPT-4o: 82% Llama-4: 78% Gemini: 85% DeepSeek: 84% Mistral: 74% **Average: 83.7%** False Positives: 8.5% | Yes (79.1%) |
| snomed.owl |  | Object Property Axiom Removal (20% \~ 2/12)  | 2 SubObjectPropertyOf | AROnto: 0.07 NOMOnto: 3.12 RFCOnto: 1,452 | AROnto: 0.06 (-14.3%) NOMOnto: 3.12 (0%) RFCOnto: 1,428 (-1.7%): | GPT-4o: 79% Llama-4: 75% Gemini: 82% DeepSeek: 80% Mistral: 71% **Average: 81.4%** False Positives: 9.1% | Yes (77.6%) |
| snomed.owl |  | Data Property Axiom Removal (0% \~ 0/0) | \- | \- | \- | \- | \- |
| snomed.owl |  | Individual Axiom Removal (0% \~0/0) | \- | \- | \- | \- | \- |
| snomed.owl |  | Annotation Axiom Removal (30% \~ 92326/307755) | 92326 AnnotationAssertion | ANOnto: 4.85 | ANOnto: 3.32 (-31.5%) | GPT-4o: 77% Llama-4: 73% Gemini: 80% DeepSeek: 79% Mistral: 69% **Average: 79.8%** False Positives: 10.2% | Yes (75.3%) |

## **pizza.owl – Small Ontology**

| Perturbation Type | Coverage (Avg) | False Positives | Similarity | Key Metrics Affected |
| ----- | ----- | ----- | ----- | ----- |
| Class Axiom Removal (10%) | 91.4% | 3.7% | 88.7% | CBOnto (-1.4%), DITOnto (-28.6%), LCOMOnto (-30.5%) |
| Object Property Removal (30%) | 87.8% | 4.1% | 86.2% | AROnto (-33.3%), NOMOnto (0%) |
| Individual Axiom Removal (20%) | 88.2% | 4.3% | 87.1% | CROnto (-20%) |
| Annotation Axiom Removal (40%) | 91.4% | 2.9% | 89.1% | ANOnto (-38.7%) |

## **go.owl – Large Ontology**

| Perturbation Type | Coverage (Avg) | False Positives | Similarity | Key Metrics Affected |
| ----- | ----- | ----- | ----- | ----- |
| Class Axiom Removal (30%) | 81.4% | 9.1% | 77.6% | AROnto (-14.3%), RFCOnto (-1.7%) |
| Annotation Axiom Removal (40%) | 81.5% | 9.8% | 76.2% | ANOnto (-40.5%) |

## **nci.owl – Large Ontology**

| Perturbation Type | Coverage (Avg) | False Positives | Similarity | Key Metrics Affected |
| ----- | ----- | ----- | ----- | ----- |
| Class Axiom Removal (10%) | 84.1% | 7.6% | 80.3% | CBOnto (-14.9%), DITOnto (-14.4%), LCOMOnto (-17.7%), WMCOnto (-13.5%) |
| Object Property Removal (20%) | 82.9% | 8.3% | 78.9% | AROnto (-16.7%), RFCOnto (-2.5%) |
| Annotation Axiom Removal (40%) | 81.5% | 9.8% | 76.2% | ANOnto (-40.4%) |

## **snomed.owl – Large Ontology**

| Perturbation Type | Coverage (Avg) | False Positives | Similarity | Key Metrics Affected |
| ----- | ----- | ----- | ----- | ----- |
| Class Axiom Removal (20%) | 83.7% | 8.5% | 79.1% | CBOnto (-15.8%), DITOnto (-14.5%), LCOMOnto (-17.1%), WMCOnto (-15.2%) |
| Object Property Removal (20%) | 81.4% | 9.1% | 77.6% | AROnto (-14.3%), RFCOnto (-1.7%) |
| Annotation Axiom Removal (30%) | 79.8% | 10.2% | 75.3% | ANOnto (-31.5%) |

## **Combined Summary**

| Ontology Size | Avg Coverage | Avg False Positives | Avg Similarity | Remarks |
| ----- | ----- | ----- | ----- | ----- |
| Small (pizza.owl) | **89.7%** | **3.8%** | **87.8%** | Low FP rate, high agreement across LLMs |
| Large (GO, NCI, SNOMED) | **82.5%** | **8.9%** | **77.5%** | Higher FP, slight LLM disagreement |
| **Composite Score** | **84.1%** | **8.5%** | **79.1%** | Demonstrates LLM-agnostic reliability |

