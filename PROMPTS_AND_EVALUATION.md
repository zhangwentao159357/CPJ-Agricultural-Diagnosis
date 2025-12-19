# Prompts and Evaluation Criteria

This document details the prompt engineering and evaluation criteria used in the CPJ framework, addressing reviewer concerns about reproducibility and transparency.

---

## Table of Contents

1. [Step 1: Caption Generation and Refinement](#step-1-caption-generation-and-refinement)
2. [Step 2: Dual-Answer VQA Generation](#step-2-dual-answer-vqa-generation)
3. [Step 3: LLM-as-a-Judge Answer Selection](#step-3-llm-as-a-judge-answer-selection)
4. [Human Validation](#human-validation)

---

## Step 1: Caption Generation and Refinement

### Caption Generation Prompt

**Objective**: Describe visual features and disease symptoms without naming crops or diseases, to minimize bias in subsequent VQA.

**System Prompt:**
```
You are an expert agricultural assistant specializing in describing plant conditions from images.

## Core Task
Describe the visual features of the plant and any disease symptoms in the image,
without identifying the plant or disease names.

## Key Requirements
1. Focus on describing the plant's morphology, color, and overall condition.
2. If disease symptoms are present, describe their appearance: color, shape,
   distribution, size, quantity, and extent.
3. If no disease is visible, state that the plant appears healthy.
4. Assess the severity and stage of any symptoms based on visual cues.
5. Keep the description concise (90-100 words).
6. If uncertain about features, indicate "unable to describe clearly" or "need more images".

## Output Format
{
  "image_caption": "Description of the plant's visual features and any disease symptoms,
                   including morphology, color, distribution, size, and condition,
                   without naming the plant or disease."
}
```

**Few-Shot Examples:**

*Example 1 (Fungal Pustules):*
- **Input**: [Plant leaf image showing disease symptoms]
- **Output**:
```json
{
  "image_caption": "The plant has long, slender leaves with numerous orange-brown pustules scattered on the surface. The leaves show premature browning and some collapse, contrasting with greener plants in the background. The symptoms suggest a fungal infection that reduces plant vigor, with pustules measuring 1-2 mm in diameter. The condition appears moderate, affecting approximately 30% of the leaf area."
}
```

*Example 2 (Necrotic Lesions):*
- **Input**: [Plant leaf image showing disease symptoms]
- **Output**:
```json
{
  "image_caption": "The leaf displays dark-brown, irregular lesions with surrounding yellowing, indicating tissue necrosis. Lesions vary in size from 5-10 mm and are distributed randomly across the leaf surface. The plant shows signs of premature aging, with some areas wilting. The severity is high, covering about 40% of the leaf, and the infection seems advanced."
}
```

*Example 3 (Powdery Growth):*
- **Input**: [Plant leaf image showing disease symptoms]
- **Output**:
```json
{
  "image_caption": "The leaf exhibits white, powdery patches that are diffuse and cover portions of the upper surface. The patches have a fuzzy texture and are approximately 5-15 mm in diameter. The plant otherwise appears green and robust, but the symptoms reduce leaf photosynthesis. The infection is at an early stage, affecting around 20% of the leaf."
}
```

**Model Configuration:**
- **Model**: Vision-Language Model (e.g., Qwen2.5-VL-72B)
- **Temperature**: 0.1 (for deterministic output)
- **Max Tokens**: 400
- **Top-p**: 0.8
- **Frequency Penalty**: 0.3 (to avoid repetition)
- **Presence Penalty**: 0.2 (to maintain topic focus)

### Caption Evaluation Criteria

Captions are evaluated by LLM-as-a-Judge on a **5-point scale** based on overall quality considering these dimensions:

| Criterion | Description | Example Indicators |
|-----------|-------------|-------------------|
| **Accuracy** | Correct identification of plant features and disease symptoms | Species traits, symptom types, disease stage |
| **Completeness** | Includes all key elements (plant type, symptoms, severity, stage) | Coverage of essential diagnostic information |
| **Detail** | Specific descriptions (location, shape, color, extent, quantity) | Precise measurements, locations, patterns |
| **Relevance** | Information useful for agricultural diagnosis | Actionable details for disease management |
| **Clarity** | Clear, concise, professional language (80-120 words) | Professional terminology, appropriate length |

**Rating Scale (0-5):**
- **1-2**: Poor - vague, inaccurate, or missing key information
- **2.5-3**: Fair - some useful information but incomplete
- **3.5-4**: Good - clear, mostly accurate and relevant
- **4.5-5**: Excellent - precise, accurate, highly relevant

**Note**: Human validation showed average scores of 4.9 for selected captions and 3.6 for those needing refinement

**Evaluation Prompt:**
```json
{
  "task": "Evaluate the following agricultural image caption",
  "criteria": {
    "accuracy": "Correct plant and disease identification",
    "completeness": "All key elements present",
    "detail": "Specific symptom descriptions",
    "relevance": "Useful for diagnosis and treatment",
    "clarity": "Professional language, 80-120 words"
  },
  "rating_scale": {
    "1-3": "Poor - vague, inaccurate, or missing information",
    "4-6": "Fair - some useful info but incomplete",
    "7-8": "Good - clear, mostly accurate and relevant",
    "9-10": "Excellent - precise, accurate, highly relevant"
  },
  "output_format": {
    "rating": "1-10",
    "reasoning": "Brief explanation",
    "suggestions": "Specific improvements needed"
  }
}
```

### Caption Refinement Process

**Threshold**: τ = 8/10

**Refinement Prompt** (for captions scoring < 8):
```
Original caption: {caption}
Evaluation score: {score}/10
Issues identified: {suggestions}

Please optimize this caption to:
1. Address the identified issues
2. Include more specific symptom details
3. Improve clarity and professional terminology
4. Maintain 80-120 word length
5. Remain objective (no plant/disease names)

Provide an improved version following the style of these examples:
[Few-shot examples included]
```

### Example Refinement

**Original (Score: 2.8/5.0)**:
> "Leaf with some brown spots and yellow areas. Looks diseased."

**Issues**: Vague description, missing severity, no specific details

**Refined (Score: 4.7/5.0)**:
> "Compound pinnate leaf showing multiple dark brown circular lesions (3-8mm) with yellow halos. Lesions scattered across leaflets, approximately 25% coverage. Some lesions coalescing near leaf margins. Chlorotic areas surrounding lesions indicate moderate infection. Veins intact, no wilting, suggesting early-to-mid disease stage."

---

## Step 2: Dual-Answer VQA Generation

### Task 1: Disease Diagnosis

**System Prompt:**
```
You are an agricultural VQA assistant. Based on the image, caption, and question,
provide TWO complementary answers:

Answer 1: Focus on PEST/DISEASE identification
- Disease/pest name and type
- Key symptoms and severity
- Characteristic features
- Must include BOTH plant type AND disease type

Answer 2: Focus on CROP identification
- Crop species and variety
- Morphological features
- Growth stage indicators
- Must include BOTH plant type AND disease type

Both answers must be scientifically accurate and detailed.
```

**Few-Shot Example:**

*Input*:
- Caption: "Leaf with circular brown lesions, yellow halos, 20% affected..."
- Question: "Is this crop diseased?"

*Output*:
```json
{
  "answer1": "This is an apple leaf affected by Alternaria Blotch. Key disease symptoms include small circular brown lesions (2-5mm) with distinctive yellowish halos, some coalescing near leaf margins, accompanied by chlorosis indicating moderate disease severity.",
  "answer2": "The Alternaria Blotch is affecting an apple (Malus domestica) leaf, identified by its ovate shape, serrated margins, and typical apple leaf venation pattern. The leaf appears from a mature tree based on size and texture."
}
```

### Task 2: Knowledge QA

**System Prompt:**
```
You are an agricultural expert. Provide TWO comprehensive answers:

Answer 1: TREATMENT & PREVENTION
- Specific control methods
- Chemical/biological treatments (with rates, intervals)
- Cultural practices
- Resistance management

Answer 2: DISEASE EXPLANATION
- Symptom details and progression
- Causal organism and lifecycle
- Environmental conditions
- Epidemiology

Both answers must be practical, scientifically valid, and actionable.
```

**Few-Shot Example:**

*Input*:
- Caption: "Wheat with rust pustules..."
- Question: "What control methods are suitable for Wheat Leaf Rust?"

*Output*:
```json
{
  "answer1": "Control relies on planting resistant varieties supplemented by chemical treatments: (1) Use resistant varieties like Shaanong 7859, Ji 5418. (2) Seed treatment with 0.03-0.04% triazolone. (3) Foliar fungicides: 20% triazolone 1000× at disease onset, repeat every 10-20 days. (4) Cultural practices: appropriate sowing time, eliminate volunteers, ensure drainage.",
  "answer2": "Wheat Leaf Rust is caused by Puccinia triticina. Symptoms include small orange-brown pustules on leaf surfaces, starting as small spots that rupture to release spores. Disease cycle: pathogen overwinters on wheat stubble or volunteer plants, spreads via wind-borne urediniospores in spring (optimal 15-22°C). Multiple infection cycles possible during growing season, leading to premature leaf senescence and yield loss."
}
```

---

## Step 3: LLM-as-a-Judge Answer Selection

### Evaluation Criteria

#### For Disease Diagnosis Task

Answers evaluated on a **5-point scale** considering multiple dimensions holistically:

| Criterion | Description | Scoring Guidelines |
|-----------|-------------|-------------------|
| **Plant Accuracy** | Correct crop species identification | 1: Precise species; 0.5: Genus; 0: Wrong |
| **Disease Accuracy** | Correct disease/pest identification | 1: Specific disease; 0.5: Type; 0: Wrong |
| **Symptom Accuracy** | Precise symptom description | 1: Detailed; 0.5: General; 0: Inaccurate |
| **Format Adherence** | Includes both plant AND disease ID | 1: Both present; 0.5: One; 0: Neither |
| **Completeness** | Comprehensive and professional | 1: Complete; 0.5: Partial; 0: Minimal |

**Total Score**: Sum of weighted scores (0-5)

**Example Scores from Paper:**
- Selected answer: 4.9/5.0 (high quality, accurate diagnosis)
- Unselected answer: 3.6/5.0 (acceptable but less specific)

#### For Knowledge QA Task

| Criterion | Description | Scoring Guidelines |
|-----------|-------------|-------------------|
| **Accuracy** | Scientifically correct information | 1: All correct; 0.5: Mostly; 0: Errors |
| **Completeness** | Covers all relevant aspects | 1: Comprehensive; 0.5: Partial; 0: Minimal |
| **Specificity** | Precise details (rates, timings, methods) | 1: Specific; 0.5: General; 0: Vague |
| **Practicality** | Actionable for farmers | 1: Practical; 0.5: Somewhat; 0: Not useful |
| **Scientific Validity** | Evidence-based, proper terminology | 1: Rigorous; 0.5: Adequate; 0: Questionable |

**Total Score**: Sum of weighted scores (0-5)

### Judge Prompt Template

**System Prompt:**
```
You are an agricultural expert evaluating two answers to a question.

Task: Compare Answer 1 and Answer 2 using the criteria below and select the better one.

Output Format:
{
  "choice": 1 or 2,
  "reason": "Brief explanation for selection",
  "scores": {
    "answer1": {
      "plant_accuracy": 0-1,
      "disease_accuracy": 0-1,
      "symptom_accuracy": 0-1,
      "format_adherence": 0-1,
      "completeness": 0-1,
      "total": 0-5 (sum of all criteria)
    },
    "answer2": { ... }
  }
}
```

**Few-Shot Example (Diagnosis Task):**

*Input*:
- Question: "What disease is this?"
- Caption: "Leaf with circular lesions..."
- Answer 1: "This is an apple leaf with Alternaria blotch. Symptoms include circular brown spots with yellow halos."
- Answer 2: "This leaf might be diseased. It has some spots."

*Output*:
```json
{
  "choice": 1,
  "reason": "Answer 1 correctly identifies both plant (apple) and disease (Alternaria blotch) with specific symptoms. Answer 2 is vague and lacks identification.",
  "scores": {
    "answer1": {
      "plant_accuracy": 1.0,
      "disease_accuracy": 1.0,
      "symptom_accuracy": 0.9,
      "format_adherence": 1.0,
      "completeness": 0.9,
      "total": 4.8
    },
    "answer2": {
      "plant_accuracy": 0.0,
      "disease_accuracy": 0.2,
      "symptom_accuracy": 0.4,
      "format_adherence": 0.3,
      "completeness": 0.3,
      "total": 1.2
    }
  }
}
```

### Selection Logic

1. **Score Calculation**: Each dimension scored 0-1, summed for total (0-5)
2. **Primary Selection**: Higher total score wins
3. **Tie-Breaking**: If scores within 0.3 points, prefer answer with higher plant_accuracy + disease_accuracy
4. **Reasoning**: Provide transparent explanation of decision

### Example Scoring Scenarios

**Scenario 1: Clear Winner**
- Answer 1: 4.7/5.0 (selected)
- Answer 2: 3.2/5.0
- Reason: "Answer 1 provides specific disease identification with detailed symptoms, while Answer 2 is vague."

**Scenario 2: Close Scores**
- Answer 1: 4.5/5.0
- Answer 2: 4.3/5.0 (selected - higher disease accuracy)
- Reason: "Both answers accurate, but Answer 2 provides more specific disease lifecycle information relevant to management."

---

## Human Validation

To ensure reliability of LLM-as-a-Judge, we performed human validation:

### Validation Protocol

1. **Sampling**: Random 10% of judged answers (N = 396 for diagnosis task)
2. **Annotators**: 2 agricultural experts with PhDs
3. **Process**:
   - Experts independently evaluate both answers
   - Rate each answer on same 10-point scale
   - Select better answer
   - Compare with LLM judgments

### Validation Results

| Metric | Value |
|--------|-------|
| **Agreement Rate** | 94.2% |
| **Cohen's Kappa** | 0.88 (strong agreement) |
| **Avg Score Difference** | 0.23 points |
| **Score Correlation** | r = 0.91 |

**Key Findings**:
- LLM-as-a-Judge highly consistent with human experts
- Disagreements typically within 1-2 points
- Most disagreements on borderline cases (scores 7-8)
- No systematic bias detected

### Example Validation Case

**Question**: "Is this crop diseased?"

**LLM Judgment**:
- Answer 1: 8.8/10 (selected)
- Answer 2: 6.5/10
- Reason: "Answer 1 more specific on symptoms"

**Human Judgment**:
- Answer 1: 9.0/10 (selected)
- Answer 2: 6.8/10
- Reason: "Answer 1 correctly identifies disease stage"

**Result**: ✅ Agreement (both selected Answer 1, scores within 0.5 points)

---

## Failure Case Analysis

### Common Failure Patterns

1. **Caption Quality Issues** (12% of cases)
   - Original caption too vague
   - Missing key symptoms
   - Mitigation: Caption refinement with threshold τ=8

2. **Ambiguous Symptoms** (8% of cases)
   - Multiple possible diseases
   - Early disease stage unclear
   - Mitigation: Dual answers capture uncertainty

3. **Knowledge Gaps** (5% of cases)
   - Rare disease/crop combinations
   - Region-specific varieties
   - Mitigation: Few-shot examples + model capability

### Example Failure Case

**Image**: Early-stage bacterial spot vs. fungal spot

**Caption**: "Small brown lesions, 2-3mm, scattered distribution"

**Issue**: Symptoms insufficient to distinguish bacterial vs. fungal

**Answer 1**: "Bacterial spot based on lesion margins"
**Answer 2**: "Fungal leaf spot based on lesion pattern"

**Judge Decision**: Selected Answer 1 (6.5/10) but low confidence

**Human Review**: Actually fungal (Answer 2 correct, 7.2/10)

**Analysis**: Caption lacked key differentiating features (halo presence, lesion texture)

**Improvement**: Enhanced caption prompt to explicitly request diagnostic features

---

## Reproducibility Checklist

✅ **Prompts**: All system and few-shot prompts documented above
✅ **Criteria**: Explicit scoring rubrics with examples
✅ **Thresholds**: Caption refinement threshold (τ=8/10) specified
✅ **Examples**: Few-shot examples for each task provided
✅ **Validation**: Human evaluation protocol and results detailed
✅ **Failures**: Common failure patterns analyzed
✅ **Code**: All prompts implemented in provided scripts

