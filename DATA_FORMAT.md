# 📋 Data Format Specification

<div align="center">

**JSON Data Formats for CPJ Pipeline**

[![Format](https://img.shields.io/badge/Format-JSON-blue.svg?style=flat-square)](DATA_FORMAT.md)
[![Encoding](https://img.shields.io/badge/Encoding-UTF--8-green.svg?style=flat-square)](DATA_FORMAT.md)
[![Validation](https://img.shields.io/badge/Validation-Included-orange.svg?style=flat-square)](#data-validation)

</div>

---

## 📌 Table of Contents

1. [Input Format](#input-format)
2. [Pipeline Data Formats](#pipeline-data-formats)
3. [Evaluation Data Format](#evaluation-data-format)
4. [Data Validation](#data-validation)
5. [Example Complete Pipeline](#example-complete-pipeline)
6. [Notes](#notes)

---

## 📥 Input Format

### Initial Input (Step 1 Input)

<table>
<tr>
<th width="40%">JSON Structure</th>
<th width="60%">Field Descriptions</th>
</tr>
<tr>
<td valign="top">

```json
[
  {
    "question_id": "test_conv_0001",
    "image": "path/to/image.jpg",
    "question": "Is this crop diseased?",
    "answer": "Yes, bacterial infection."
  }
]
```

</td>
<td valign="top">

| Field | Type | Description |
|-------|------|-------------|
| `question_id` | `string` | Unique identifier |
| `image` | `string` | Image file path |
| `question` | `string` | Question text |
| `answer` | `string` | Ground truth answer |

</td>
</tr>
</table>

---

## 🔄 Pipeline Data Formats

### Step 1 Output: Refined Captions

> **Purpose**: Caption generation with quality evaluation and refinement

<details>
<summary><b>JSON Structure & Fields</b></summary>

```json
[
  {
    "question_id": "test_conv_0001",
    "image": "path/to/image.jpg",
    "question": "Is this crop diseased?",
    "answer": "Yes, bacterial infection.",
    "image_caption": "Compound pinnate leaf exhibiting symptoms of bacterial infection. Small, dark brown lesions with yellow halos scattered across the leaf surface, showing angular patterns following vein structures...",
    "rating": 9,
    "reasoning": "Caption accurately describes plant morphology and disease symptoms with specific details",
    "suggestions": "Could include more detail about disease stage",
    "evaluated": true,
    "optimized": false
  }
]
```

**New Fields Added:**

| Field | Type | Description |
|-------|------|-------------|
| `image_caption` | `string` | Generated/refined caption |
| `rating` | `integer` | Quality score (1-10) |
| `reasoning` | `string` | Explanation for rating |
| `suggestions` | `string` | Improvement suggestions |
| `evaluated` | `boolean` | Was caption evaluated? |
| `optimized` | `boolean` | Was caption optimized? |

</details>

---

### Step 2 Output: Dual Answers

> **Purpose**: Generate two complementary answers from different perspectives

<details>
<summary><b>JSON Structure & Fields</b></summary>

```json
[
  {
    "question_id": "test_conv_0001",
    "image_caption": "Compound pinnate leaf exhibiting symptoms of bacterial infection. Dark brown lesions with yellow halos scattered across the surface, showing angular patterns and coalescing areas...",
    "question": "Is this crop diseased?",
    "image": "path/to/image.jpg",
    "answer": "Yes, bacterial infection.",
    "generation_answer1": "Yes, bacterial necrotic lesions. Key symptoms include small dark brown lesions with yellow halos...",
    "generation_answer2": "Yes, compound pinnate leaf showing bacterial infection symptoms. The disease presents with characteristic lesions..."
  }
]
```

**New Fields Added:**

| Field | Type | Description |
|-------|------|-------------|
| `generation_answer1` | `string` | Answer focusing on disease identification |
| `generation_answer2` | `string` | Answer focusing on crop identification |

</details>

---

### Step 3 Output: Final Selected Answer

> **Purpose**: Select best answer using LLM-as-a-Judge with transparent scoring

<details>
<summary><b>JSON Structure & Fields</b></summary>

```json
[
  {
    "question_id": "test_conv_0001",
    "image_caption": "Compound pinnate leaf exhibiting symptoms of bacterial infection. Dark brown lesions with yellow halos scattered across the surface...",
    "question": "Is this crop diseased?",
    "image": "path/to/image.jpg",
    "answer": "Yes, bacterial infection.",
    "generation_answer": "Yes, bacterial necrotic lesions. Key symptoms include small dark brown lesions with yellow halos...",
    "selected_answer": "answer1",
    "selected_score": 4.7,
    "unselected_score": 3.2,
    "evaluation_reason": "Answer 1 provides more specific disease identification with detailed symptom description, making it more accurate and actionable."
  }
]
```

**New Fields Added:**

| Field | Type | Description |
|-------|------|-------------|
| `generation_answer` | `string` | The selected best answer |
| `selected_answer` | `string` | Which was selected (`"answer1"` or `"answer2"`) |
| `selected_score` | `float` | Total score of selected (0-5.0 scale) |
| `unselected_score` | `float` | Total score of unselected (0-5.0 scale) |
| `evaluation_reason` | `string` | Explanation for the selection |

</details>

---

## 📊 Evaluation Data Format

### Caption Evaluation Results

<table>
<tr>
<th width="50%">JSON Format</th>
<th width="50%">Example Output</th>
</tr>
<tr>
<td valign="top">

```json
[
  {
    "id": 0,
    "caption_preview": "Leaf exhibiting symptoms...",
    "rating": 9,
    "reasoning": "Accurate description"
  }
]
```

</td>
<td valign="top">

**Fields:**
- `id`: Caption identifier
- `caption_preview`: First 80 characters
- `rating`: Quality score (1-10)
- `reasoning`: Evaluation explanation

</td>
</tr>
</table>

---

### Answer Evaluation Results (Diagnosis Task)

<table>
<tr>
<th width="50%">JSON Format</th>
<th width="50%">Scoring Breakdown</th>
</tr>
<tr>
<td valign="top">

```json
[
  {
    "id": 0,
    "question": "Is this crop diseased?",
    "choice": 1,
    "reason": "More specific identification",
    "answer1_score": 47,
    "answer2_score": 32,
    "answer1_preview": "Bacterial infection...",
    "answer2_preview": "Showing symptoms..."
  }
]
```

</td>
<td valign="top">

**Criteria (0-10 points each):**
- 🌱 `plant_accuracy`: Crop identification
- 🦠 `disease_accuracy`: Disease identification
- 🔬 `symptom_accuracy`: Symptom description
- 📋 `format_adherence`: Format compliance
- ✅ `completeness`: Comprehensiveness

**Total**: 0-50 points

</td>
</tr>
</table>

---

### Answer Evaluation Results (Knowledge QA Task)

<table>
<tr>
<th width="50%">JSON Format</th>
<th width="50%">Scoring Breakdown</th>
</tr>
<tr>
<td valign="top">

```json
[
  {
    "id": 0,
    "question": "Control methods for rust?",
    "choice": 1,
    "reason": "Comprehensive details",
    "score1": 46,
    "score2": 35,
    "answer1_preview": "Resistant varieties...",
    "answer2_preview": "Use fungicides..."
  }
]
```

</td>
<td valign="top">

**Criteria (0-10 points each):**
- 🎯 `accuracy`: Scientific correctness
- ✅ `completeness`: Coverage
- 🔬 `specificity`: Detail level
- 👨‍🌾 `practicality`: Actionability
- 📚 `scientific_validity`: Evidence-based

**Total**: 0-50 points

</td>
</tr>
</table>

---

## ✅ Data Validation

### Required Fields by Stage

<table>
<thead>
  <tr>
    <th width="33%">📝 Stage 1 Input</th>
    <th width="33%">🎯 Stage 2 Input</th>
    <th width="33%">⚖️ Stage 3 Input</th>
  </tr>
</thead>
<tbody>
  <tr>
    <td valign="top">

**Caption Generation**

- ✅ `question_id`
- ✅ `image`
- ✅ `question`
- ✅ `answer`

    </td>
    <td valign="top">

**VQA Generation**

- ✅ `question_id`
- ✅ `image`
- ✅ `question`
- ✅ `image_caption`

    </td>
    <td valign="top">

**Answer Selection**

- ✅ `question_id`
- ✅ `question`
- ✅ `image_caption`
- ✅ `generation_answer1`
- ✅ `generation_answer2`

    </td>
  </tr>
</tbody>
</table>

---

### Data Quality Checks

Use these validation functions before running each stage:

<details>
<summary><b>Step 1 Validation Function</b></summary>

```python
def validate_step1_input(data):
    """Validate input data for caption generation stage"""
    required_fields = ["question_id", "image", "question", "answer"]

    for item in data:
        for field in required_fields:
            assert field in item, f"Missing field: {field}"
            assert item[field], f"Empty field: {field}"

    return True
```

</details>

<details>
<summary><b>Step 2 Validation Function</b></summary>

```python
def validate_step2_input(data):
    """Validate input data for VQA generation stage"""
    required_fields = ["question_id", "image", "question", "image_caption"]

    for item in data:
        for field in required_fields:
            assert field in item, f"Missing field: {field}"
            assert item[field], f"Empty field: {field}"

    return True
```

</details>

<details>
<summary><b>Step 3 Validation Function</b></summary>

```python
def validate_step3_input(data):
    """Validate input data for answer selection stage"""
    required_fields = ["question_id", "question", "image_caption",
                       "generation_answer1", "generation_answer2"]

    for item in data:
        for field in required_fields:
            assert field in item, f"Missing field: {field}"
            assert item[field], f"Empty field: {field}"

    return True
```

</details>

---

## 🔄 Example Complete Pipeline

### Data Evolution Through Pipeline

<table>
<thead>
  <tr>
    <th>Stage</th>
    <th>Data Structure</th>
  </tr>
</thead>
<tbody>
  <tr>
    <td><b>🔹 Initial Input</b></td>
    <td>
      <code>{"question_id": "001", "image": "img.jpg", "question": "Is this diseased?", "answer": "Yes"}</code>
    </td>
  </tr>
  <tr>
    <td><b>📝 After Step 1</b></td>
    <td>
      <code>{"question_id": "001", ..., "image_caption": "Compound pinnate leaf with bacterial necrotic lesions...", "rating": 9, "evaluated": true}</code>
    </td>
  </tr>
  <tr>
    <td><b>🎯 After Step 2</b></td>
    <td>
      <code>{"question_id": "001", "image_caption": "...", "generation_answer1": "Yes, bacterial infection...", "generation_answer2": "Yes, showing symptoms..."}</code>
    </td>
  </tr>
  <tr>
    <td><b>⚖️ After Step 3</b></td>
    <td>
      <code>{"question_id": "001", ..., "generation_answer": "Yes, bacterial infection...", "selected_answer": "answer1", "selected_score": 4.7, "unselected_score": 3.2}</code>
    </td>
  </tr>
</tbody>
</table>

---

## 📌 Notes

<table>
<tr>
<td width="50%" valign="top">

### 📝 **Format Requirements**

- **Encoding**: UTF-8
- **Score Format**: Integers (not floats)
- **Boolean Values**: `true`/`false` (lowercase)
- **Text Fields**: Non-empty strings

</td>
<td width="50%" valign="top">

### 🔧 **Path Specifications**

- **Image Paths**: Absolute or relative
- **File Extension**: `.json`
- **Line Endings**: Unix-style (`\n`) preferred
- **Indentation**: 2 spaces recommended

</td>
</tr>
</table>

---

<div align="center">

**📖 For implementation examples, see the [Configuration Guide](CONFIGURATION.md)**

**[🔝 Back to Top](#-data-format-specification)**

</div>
