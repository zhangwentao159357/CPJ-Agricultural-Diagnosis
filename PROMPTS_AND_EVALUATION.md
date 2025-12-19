# 📝 Prompts and Evaluation Criteria

<div align="center">

**Complete Technical Documentation for CPJ Framework**

*Addressing reviewer concerns about reproducibility and transparency*

[![Reproducibility](https://img.shields.io/badge/Reproducibility-Complete-brightgreen.svg?style=flat-square)](#reproducibility-checklist)
[![Human Validation](https://img.shields.io/badge/Human_Validation-94.2%25-blue.svg?style=flat-square)](#human-validation)
[![Agreement](https://img.shields.io/badge/Cohen's_Kappa-0.88-orange.svg?style=flat-square)](#validation-results)

</div>

---

## 📋 Table of Contents

1. [**Step 1**: Caption Generation and Refinement](#step-1-caption-generation-and-refinement)
2. [**Step 2**: Dual-Answer VQA Generation](#step-2-dual-answer-vqa-generation)
3. [**Step 3**: LLM-as-a-Judge Answer Selection](#step-3-llm-as-a-judge-answer-selection)
4. [**Human Validation**](#human-validation)
5. [**Failure Case Analysis**](#failure-case-analysis)
6. [**Reproducibility Checklist**](#reproducibility-checklist)

---

## Step 1: Caption Generation and Refinement

> **🎯 Objective**: Describe visual features and disease symptoms **without naming crops or diseases**, to minimize bias in subsequent VQA.

### 📝 Caption Generation Prompt

<details open>
<summary><b>System Prompt</b></summary>

```python
"""
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
"""
```

</details>

### 🔍 Few-Shot Examples

<table>
<thead>
  <tr>
    <th width="30%">Example Type</th>
    <th width="70%">Generated Caption</th>
  </tr>
</thead>
<tbody>
  <tr>
    <td><b>🍄 Fungal Pustules</b></td>
    <td>
      <code>The plant has long, slender leaves with numerous orange-brown pustules scattered on the surface. The leaves show premature browning and some collapse, contrasting with greener plants in the background. The symptoms suggest a fungal infection that reduces plant vigor, with pustules measuring 1-2 mm in diameter. The condition appears moderate, affecting approximately 30% of the leaf area.</code>
    </td>
  </tr>
  <tr>
    <td><b>💀 Necrotic Lesions</b></td>
    <td>
      <code>The leaf displays dark-brown, irregular lesions with surrounding yellowing, indicating tissue necrosis. Lesions vary in size from 5-10 mm and are distributed randomly across the leaf surface. The plant shows signs of premature aging, with some areas wilting. The severity is high, covering about 40% of the leaf, and the infection seems advanced.</code>
    </td>
  </tr>
  <tr>
    <td><b>☁️ Powdery Growth</b></td>
    <td>
      <code>The leaf exhibits white, powdery patches that are diffuse and cover portions of the upper surface. The patches have a fuzzy texture and are approximately 5-15 mm in diameter. The plant otherwise appears green and robust, but the symptoms reduce leaf photosynthesis. The infection is at an early stage, affecting around 20% of the leaf.</code>
    </td>
  </tr>
</tbody>
</table>

### ⚙️ Model Configuration

<table>
<thead>
  <tr>
    <th>Parameter</th>
    <th>Value</th>
    <th>Purpose</th>
  </tr>
</thead>
<tbody>
  <tr>
    <td><b>Model</b></td>
    <td><code>Qwen2.5-VL-72B</code></td>
    <td>Vision-Language Model</td>
  </tr>
  <tr>
    <td><b>Temperature</b></td>
    <td><code>0.1</code></td>
    <td>Deterministic output</td>
  </tr>
  <tr>
    <td><b>Max Tokens</b></td>
    <td><code>400</code></td>
    <td>Concise descriptions</td>
  </tr>
  <tr>
    <td><b>Top-p</b></td>
    <td><code>0.8</code></td>
    <td>Limited candidate range</td>
  </tr>
  <tr>
    <td><b>Frequency Penalty</b></td>
    <td><code>0.3</code></td>
    <td>Avoid repetition</td>
  </tr>
  <tr>
    <td><b>Presence Penalty</b></td>
    <td><code>0.2</code></td>
    <td>Maintain topic focus</td>
  </tr>
</tbody>
</table>

---

### 📊 Caption Evaluation Criteria

Captions are evaluated by **LLM-as-a-Judge** on a **10-point scale** based on overall quality:

<table align="center">
<thead>
  <tr>
    <th width="20%">Criterion</th>
    <th width="40%">Description</th>
    <th width="40%">Example Indicators</th>
  </tr>
</thead>
<tbody>
  <tr>
    <td>🎯 <b>Accuracy</b></td>
    <td>Correct identification of plant features and disease symptoms</td>
    <td>Species traits, symptom types, disease stage</td>
  </tr>
  <tr>
    <td>✅ <b>Completeness</b></td>
    <td>Includes all key elements</td>
    <td>Plant type, symptoms, severity, stage</td>
  </tr>
  <tr>
    <td>🔬 <b>Detail</b></td>
    <td>Specific descriptions</td>
    <td>Measurements, locations, patterns</td>
  </tr>
  <tr>
    <td>💡 <b>Relevance</b></td>
    <td>Information useful for diagnosis</td>
    <td>Actionable details for disease management</td>
  </tr>
  <tr>
    <td>📖 <b>Clarity</b></td>
    <td>Clear, concise, professional language</td>
    <td>Professional terminology, 80-120 words</td>
  </tr>
</tbody>
</table>

#### Rating Scale (0-10)

| Score Range | Quality Level | Description |
|-------------|---------------|-------------|
| **9.0 - 10.0** | 🌟 Excellent | Precise, accurate, highly relevant |
| **7.0 - 8.0** | ✅ Good | Clear, mostly accurate and relevant |
| **5.0 - 6.0** | ⚠️ Fair | Some useful information but incomplete |
| **2.0 - 4.0** | ❌ Poor | Vague, inaccurate, or missing key information |

> 💡 **Human Validation Results**:
> - Selected captions: **9.8/10.0** (high quality)
> - Captions needing refinement: **7.2/10.0** (acceptable)

<details>
<summary><b>Evaluation Prompt (JSON Format)</b></summary>

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

</details>

---

### 🔄 Caption Refinement Process

> **Threshold**: τ = **8/10** (captions scoring below this are automatically refined)

<details>
<summary><b>Refinement Prompt Template</b></summary>

```text
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

</details>

### 📈 Example Refinement

<table>
<tr>
<th width="50%">❌ Original (Score: 5.6/10.0)</th>
<th width="50%">✅ Refined (Score: 9.4/10.0)</th>
</tr>
<tr>
<td valign="top">

**Caption**:
> "Leaf with some brown spots and yellow areas. Looks diseased."

**Issues**:
- ⚠️ Vague description
- ⚠️ Missing severity assessment
- ⚠️ No specific details

</td>
<td valign="top">

**Caption**:
> "Compound pinnate leaf showing multiple dark brown circular lesions (3-8mm) with yellow halos. Lesions scattered across leaflets, approximately 25% coverage. Some lesions coalescing near leaf margins. Chlorotic areas surrounding lesions indicate moderate infection. Veins intact, no wilting, suggesting early-to-mid disease stage."

**Improvements**:
- ✅ Specific measurements (3-8mm)
- ✅ Severity assessment (25% coverage)
- ✅ Disease stage (early-to-mid)

</td>
</tr>
</table>

---

## Step 2: Dual-Answer VQA Generation

### Task 1: Disease Diagnosis

<details open>
<summary><b>System Prompt for Disease Diagnosis</b></summary>

```python
"""
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
"""
```

</details>

#### 🔍 Few-Shot Example (Disease Diagnosis)

<table>
<thead>
  <tr>
    <th width="30%">Input</th>
    <th width="70%">Output</th>
  </tr>
</thead>
<tbody>
  <tr>
    <td valign="top">
      <b>Caption</b>:<br/>
      <code>Leaf with circular brown lesions, yellow halos, 20% affected...</code><br/><br/>
      <b>Question</b>:<br/>
      <code>Is this crop diseased?</code>
    </td>
    <td valign="top">
      <b>Answer 1 (Disease Focus)</b>:<br/>
      <code>This is an apple leaf affected by Alternaria Blotch. Key disease symptoms include small circular brown lesions (2-5mm) with distinctive yellowish halos, some coalescing near leaf margins, accompanied by chlorosis indicating moderate disease severity.</code><br/><br/>
      <b>Answer 2 (Crop Focus)</b>:<br/>
      <code>The Alternaria Blotch is affecting an apple (Malus domestica) leaf, identified by its ovate shape, serrated margins, and typical apple leaf venation pattern. The leaf appears from a mature tree based on size and texture.</code>
    </td>
  </tr>
</tbody>
</table>

---

### Task 2: Knowledge QA

<details>
<summary><b>System Prompt for Knowledge QA</b></summary>

```python
"""
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
"""
```

</details>

#### 🔍 Few-Shot Example (Knowledge QA)

<table>
<thead>
  <tr>
    <th width="30%">Input</th>
    <th width="70%">Output</th>
  </tr>
</thead>
<tbody>
  <tr>
    <td valign="top">
      <b>Caption</b>:<br/>
      <code>Wheat with rust pustules...</code><br/><br/>
      <b>Question</b>:<br/>
      <code>What control methods are suitable for Wheat Leaf Rust?</code>
    </td>
    <td valign="top">
      <b>Answer 1 (Treatment & Prevention)</b>:<br/>
      <code>Control relies on planting resistant varieties supplemented by chemical treatments: (1) Use resistant varieties like Shaanong 7859, Ji 5418. (2) Seed treatment with 0.03-0.04% triazolone. (3) Foliar fungicides: 20% triazolone 1000× at disease onset, repeat every 10-20 days. (4) Cultural practices: appropriate sowing time, eliminate volunteers, ensure drainage.</code><br/><br/>
      <b>Answer 2 (Disease Explanation)</b>:<br/>
      <code>Wheat Leaf Rust is caused by Puccinia triticina. Symptoms include small orange-brown pustules on leaf surfaces, starting as small spots that rupture to release spores. Disease cycle: pathogen overwinters on wheat stubble or volunteer plants, spreads via wind-borne urediniospores in spring (optimal 15-22°C). Multiple infection cycles possible during growing season, leading to premature leaf senescence and yield loss.</code>
    </td>
  </tr>
</tbody>
</table>

---

## Step 3: LLM-as-a-Judge Answer Selection

### 📊 Evaluation Criteria

#### For Disease Diagnosis Task

Answers evaluated on a **5-point scale** considering multiple dimensions holistically:

<table align="center">
<thead>
  <tr>
    <th width="25%">Criterion</th>
    <th width="40%">Description</th>
    <th width="35%">Scoring Guidelines</th>
  </tr>
</thead>
<tbody>
  <tr>
    <td>🌱 <b>Plant Accuracy</b></td>
    <td>Correct crop species identification</td>
    <td>
      <b>1.0</b>: Precise species<br/>
      <b>0.5</b>: Genus level<br/>
      <b>0.0</b>: Wrong
    </td>
  </tr>
  <tr>
    <td>🦠 <b>Disease Accuracy</b></td>
    <td>Correct disease/pest identification</td>
    <td>
      <b>1.0</b>: Specific disease<br/>
      <b>0.5</b>: Disease type<br/>
      <b>0.0</b>: Wrong
    </td>
  </tr>
  <tr>
    <td>🔬 <b>Symptom Accuracy</b></td>
    <td>Precise symptom description</td>
    <td>
      <b>1.0</b>: Detailed<br/>
      <b>0.5</b>: General<br/>
      <b>0.0</b>: Inaccurate
    </td>
  </tr>
  <tr>
    <td>📋 <b>Format Adherence</b></td>
    <td>Includes both plant AND disease ID</td>
    <td>
      <b>1.0</b>: Both present<br/>
      <b>0.5</b>: One present<br/>
      <b>0.0</b>: Neither
    </td>
  </tr>
  <tr>
    <td>✅ <b>Completeness</b></td>
    <td>Comprehensive and professional</td>
    <td>
      <b>1.0</b>: Complete<br/>
      <b>0.5</b>: Partial<br/>
      <b>0.0</b>: Minimal
    </td>
  </tr>
</tbody>
</table>

**📌 Total Score**: Sum of all criteria (0-5)

> 📊 **Example Scores from Paper**:
> - ✅ Selected answer: **4.9/5.0** (high quality, accurate diagnosis)
> - ⚠️ Unselected answer: **3.6/5.0** (acceptable but less specific)

---

#### For Knowledge QA Task

<table align="center">
<thead>
  <tr>
    <th width="25%">Criterion</th>
    <th width="40%">Description</th>
    <th width="35%">Scoring Guidelines</th>
  </tr>
</thead>
<tbody>
  <tr>
    <td>🎯 <b>Accuracy</b></td>
    <td>Scientifically correct information</td>
    <td>
      <b>1.0</b>: All correct<br/>
      <b>0.5</b>: Mostly correct<br/>
      <b>0.0</b>: Errors present
    </td>
  </tr>
  <tr>
    <td>✅ <b>Completeness</b></td>
    <td>Covers all relevant aspects</td>
    <td>
      <b>1.0</b>: Comprehensive<br/>
      <b>0.5</b>: Partial<br/>
      <b>0.0</b>: Minimal
    </td>
  </tr>
  <tr>
    <td>🔬 <b>Specificity</b></td>
    <td>Precise details (rates, timings, methods)</td>
    <td>
      <b>1.0</b>: Specific<br/>
      <b>0.5</b>: General<br/>
      <b>0.0</b>: Vague
    </td>
  </tr>
  <tr>
    <td>👨‍🌾 <b>Practicality</b></td>
    <td>Actionable for farmers</td>
    <td>
      <b>1.0</b>: Practical<br/>
      <b>0.5</b>: Somewhat<br/>
      <b>0.0</b>: Not useful
    </td>
  </tr>
  <tr>
    <td>📚 <b>Scientific Validity</b></td>
    <td>Evidence-based, proper terminology</td>
    <td>
      <b>1.0</b>: Rigorous<br/>
      <b>0.5</b>: Adequate<br/>
      <b>0.0</b>: Questionable
    </td>
  </tr>
</tbody>
</table>

**📌 Total Score**: Sum of all criteria (0-5)

---

### ⚖️ Judge Prompt Template

<details>
<summary><b>System Prompt for LLM-as-a-Judge</b></summary>

```python
"""
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
"""
```

</details>

### 🔍 Few-Shot Example (Diagnosis Task)

<table>
<tr>
<th width="50%">Input</th>
<th width="50%">Output (Judge Decision)</th>
</tr>
<tr>
<td valign="top">

**Question**:
> "What disease is this?"

**Caption**:
> "Leaf with circular lesions..."

**Answer 1**:
> "This is an apple leaf with Alternaria blotch. Symptoms include circular brown spots with yellow halos."

**Answer 2**:
> "This leaf might be diseased. It has some spots."

</td>
<td valign="top">

```json
{
  "choice": 1,
  "reason": "Answer 1 correctly identifies
            both plant (apple) and disease
            (Alternaria blotch) with specific
            symptoms. Answer 2 is vague.",
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

</td>
</tr>
</table>

---

### 🎯 Selection Logic

<table>
<thead>
  <tr>
    <th width="10%">Step</th>
    <th width="30%">Process</th>
    <th width="60%">Description</th>
  </tr>
</thead>
<tbody>
  <tr>
    <td><b>1️⃣</b></td>
    <td>Score Calculation</td>
    <td>Each dimension scored 0-1, summed for total (0-5)</td>
  </tr>
  <tr>
    <td><b>2️⃣</b></td>
    <td>Primary Selection</td>
    <td>Higher total score wins</td>
  </tr>
  <tr>
    <td><b>3️⃣</b></td>
    <td>Tie-Breaking</td>
    <td>If scores within 0.3 points, prefer answer with higher <code>plant_accuracy + disease_accuracy</code></td>
  </tr>
  <tr>
    <td><b>4️⃣</b></td>
    <td>Reasoning</td>
    <td>Provide transparent explanation of decision</td>
  </tr>
</tbody>
</table>

### 📊 Example Scoring Scenarios

<table>
<thead>
  <tr>
    <th width="50%">Scenario 1: Clear Winner</th>
    <th width="50%">Scenario 2: Close Scores</th>
  </tr>
</thead>
<tbody>
  <tr>
    <td valign="top">

**Scores**:
- ✅ Answer 1: **4.7/5.0** (selected)
- ❌ Answer 2: **3.2/5.0**

**Reason**:
> "Answer 1 provides specific disease identification with detailed symptoms, while Answer 2 is vague."

**Decision**: Clear preference for Answer 1

    </td>
    <td valign="top">

**Scores**:
- Answer 1: **4.5/5.0**
- ✅ Answer 2: **4.3/5.0** (selected)

**Reason**:
> "Both answers accurate, but Answer 2 provides more specific disease lifecycle information relevant to management."

**Decision**: Tie-breaking based on disease accuracy

    </td>
  </tr>
</tbody>
</table>

---

## Human Validation

> **🎯 Purpose**: Ensure reliability of LLM-as-a-Judge against human expert judgment

### 📋 Validation Protocol

<table>
<thead>
  <tr>
    <th width="20%">Component</th>
    <th width="80%">Details</th>
  </tr>
</thead>
<tbody>
  <tr>
    <td><b>1️⃣ Sampling</b></td>
    <td>Random 10% of judged answers (<code>N = 396</code> for diagnosis task)</td>
  </tr>
  <tr>
    <td><b>2️⃣ Annotators</b></td>
    <td>2 agricultural experts with PhDs in plant pathology</td>
  </tr>
  <tr>
    <td><b>3️⃣ Process</b></td>
    <td>
      • Experts independently evaluate both answers<br/>
      • Rate each answer on same 5-point scale<br/>
      • Select better answer<br/>
      • Compare with LLM judgments
    </td>
  </tr>
</tbody>
</table>

---

### 📊 Validation Results

<table align="center">
<thead>
  <tr>
    <th width="40%">Metric</th>
    <th width="60%">Value</th>
  </tr>
</thead>
<tbody>
  <tr>
    <td>🎯 <b>Agreement Rate</b></td>
    <td><code style="color:green"><b>94.2%</b></code></td>
  </tr>
  <tr>
    <td>📊 <b>Cohen's Kappa</b></td>
    <td><code style="color:green"><b>0.88</b></code> (strong agreement)</td>
  </tr>
  <tr>
    <td>📈 <b>Avg Score Difference</b></td>
    <td><code>0.23 points</code></td>
  </tr>
  <tr>
    <td>🔗 <b>Score Correlation</b></td>
    <td><code style="color:green"><b>r = 0.91</b></code></td>
  </tr>
</tbody>
</table>

#### 🔍 Key Findings

- ✅ **LLM-as-a-Judge highly consistent** with human experts
- ✅ **Disagreements typically within 1-2 points**
- ✅ **Most disagreements on borderline cases** (scores 7-8)
- ✅ **No systematic bias detected**

---

### 📝 Example Validation Case

<table>
<tr>
<th width="50%">LLM Judgment</th>
<th width="50%">Human Judgment</th>
</tr>
<tr>
<td valign="top">

**Question**:
> "Is this crop diseased?"

**Scores**:
- ✅ Answer 1: **4.4/5.0** (selected)
- Answer 2: **3.3/5.0**

**Reason**:
> "Answer 1 more specific on symptoms"

</td>
<td valign="top">

**Question**:
> "Is this crop diseased?"

**Scores**:
- ✅ Answer 1: **4.5/5.0** (selected)
- Answer 2: **3.4/5.0**

**Reason**:
> "Answer 1 correctly identifies disease stage"

</td>
</tr>
<tr>
<td colspan="2" align="center" style="background-color:#e8f5e9; padding:10px">
  <b>✅ Result: AGREEMENT</b><br/>
  Both selected Answer 1, scores within 0.1 points
</td>
</tr>
</table>

---

## Failure Case Analysis

### 🔍 Common Failure Patterns

<table>
<thead>
  <tr>
    <th width="10%">Rank</th>
    <th width="25%">Pattern</th>
    <th width="15%">Frequency</th>
    <th width="50%">Mitigation Strategy</th>
  </tr>
</thead>
<tbody>
  <tr>
    <td><b>1️⃣</b></td>
    <td>Caption Quality Issues</td>
    <td><code>12%</code></td>
    <td>
      • Original caption too vague<br/>
      • Missing key symptoms<br/>
      <b>→ Solution</b>: Caption refinement with threshold τ=8.0
    </td>
  </tr>
  <tr>
    <td><b>2️⃣</b></td>
    <td>Ambiguous Symptoms</td>
    <td><code>8%</code></td>
    <td>
      • Multiple possible diseases<br/>
      • Early disease stage unclear<br/>
      <b>→ Solution</b>: Dual answers capture uncertainty
    </td>
  </tr>
  <tr>
    <td><b>3️⃣</b></td>
    <td>Knowledge Gaps</td>
    <td><code>5%</code></td>
    <td>
      • Rare disease/crop combinations<br/>
      • Region-specific varieties<br/>
      <b>→ Solution</b>: Few-shot examples + model capability
    </td>
  </tr>
</tbody>
</table>

---

### 📋 Detailed Failure Case Example

<table>
<tr>
<th colspan="2" style="background-color:#fff3e0">❌ Failure Case: Early-Stage Bacterial vs. Fungal Spot</th>
</tr>
<tr>
<td width="30%" valign="top">

**📷 Image Context**

Early-stage bacterial spot vs. fungal spot

**📝 Caption**

"Small brown lesions, 2-3mm, scattered distribution"

**⚠️ Issue**

Symptoms insufficient to distinguish bacterial vs. fungal

</td>
<td width="70%" valign="top">

**🤖 LLM Decision**

- **Answer 1**: "Bacterial spot based on lesion margins" ✅ **Selected (3.3/5.0)**
- **Answer 2**: "Fungal leaf spot based on lesion pattern" ❌ Not selected

**👨‍🔬 Human Review**

- Actually **fungal** (Answer 2 correct, **3.6/5.0**)
- LLM made incorrect selection

**🔍 Analysis**

Caption lacked key differentiating features:
- ❌ No halo presence description
- ❌ No lesion texture details
- ❌ No information about lesion margins

**✅ Improvement Applied**

Enhanced caption prompt to explicitly request diagnostic features:
- Lesion texture (smooth vs. rough)
- Halo characteristics (present/absent, color)
- Margin appearance (defined vs. diffuse)

</td>
</tr>
</table>

---

## Reproducibility Checklist

<div align="center">

### ✅ Complete Documentation Provided

</div>

<table>
<tr>
<td width="50%" valign="top">

### 📝 **Prompts & Examples**

- ✅ Complete system prompts
- ✅ Few-shot examples for all tasks
- ✅ Output format specifications
- ✅ Model configuration parameters

### 📊 **Evaluation Criteria**

- ✅ Detailed scoring rubrics (caption: 10-point, answer: 5-point)
- ✅ Threshold specifications (caption: τ = 8.0, answer: τ = 4.0)
- ✅ Selection logic documentation
- ✅ Tie-breaking rules

### 👥 **Human Validation**

- ✅ Validation protocol
- ✅ Agreement metrics (94.2% agreement)
- ✅ Sample size (N = 396)
- ✅ Example validation cases

</td>
<td width="50%" valign="top">

### 💻 **Code & Implementation**

- ✅ All prompts implemented in scripts
- ✅ Configuration examples
- ✅ Sample annotated outputs
- ✅ Command-line usage examples

### 🔍 **Failure Analysis**

- ✅ Common failure patterns identified
- ✅ Failure frequencies quantified
- ✅ Mitigation strategies documented
- ✅ Detailed example failure cases

### 📖 **Documentation**

- ✅ Step-by-step workflow
- ✅ Parameter explanations
- ✅ Troubleshooting guidance

</td>
</tr>
</table>

---

<div align="center">

**📧 Questions about reproducibility?** See our code implementation or contact the authors.

**[🔝 Back to Top](#-prompts-and-evaluation-criteria)**

</div>
