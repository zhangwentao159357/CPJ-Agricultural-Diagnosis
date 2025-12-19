# Data Format Specification

This document describes the JSON data formats used throughout the CPJ pipeline.

## Input Format

### Initial Input (Step 1 Input)

```json
[
  {
    "question_id": "test_conv_0001",
    "image": "path/to/image.jpg",
    "question": "Is this crop diseased?",
    "answer": "Yes, this is a tomato leaf with bacterial spot."
  }
]
```

**Fields:**
- `question_id` (string): Unique identifier for the question
- `image` (string): Path to the image file
- `question` (string): The question about the image
- `answer` (string): Ground truth answer (for evaluation)

## Pipeline Data Formats

### Step 1 Output: Refined Captions

```json
[
  {
    "question_id": "test_conv_0001",
    "image": "path/to/image.jpg",
    "question": "Is this crop diseased?",
    "answer": "Yes, this is a tomato leaf with bacterial spot.",
    "image_caption": "Tomato leaf exhibiting symptoms of bacterial spot. Small, dark brown lesions with yellow halos scattered across the leaf surface...",
    "rating": 9,
    "reasoning": "Caption accurately identifies plant and disease with specific symptom description",
    "suggestions": "Could include more detail about disease stage",
    "evaluated": true,
    "optimized": false
  }
]
```

**New Fields:**
- `image_caption` (string): Generated/refined caption describing the image
- `rating` (integer): Quality score from 1-10
- `reasoning` (string): Explanation for the rating
- `suggestions` (string): Suggestions for improvement
- `evaluated` (boolean): Whether caption was evaluated
- `optimized` (boolean): Whether caption was optimized

### Step 2 Output: Dual Answers

```json
[
  {
    "question_id": "test_conv_0001",
    "image_caption": "Tomato leaf exhibiting symptoms of bacterial spot...",
    "question": "Is this crop diseased?",
    "image": "path/to/image.jpg",
    "answer": "Yes, this is a tomato leaf with bacterial spot.",
    "generation_answer1": "Yes, this tomato leaf is affected by bacterial spot. Key symptoms include small dark brown lesions with yellow halos...",
    "generation_answer2": "Yes, this is a tomato (Solanum lycopersicum) leaf showing bacterial spot symptoms. The disease presents with characteristic lesions..."
  }
]
```

**New Fields:**
- `generation_answer1` (string): First answer focusing on disease identification
- `generation_answer2` (string): Second answer focusing on crop identification

### Step 3 Output: Final Selected Answer

```json
[
  {
    "question_id": "test_conv_0001",
    "image_caption": "Tomato leaf exhibiting symptoms of bacterial spot...",
    "question": "Is this crop diseased?",
    "image": "path/to/image.jpg",
    "answer": "Yes, this is a tomato leaf with bacterial spot.",
    "generation_answer": "Yes, this tomato leaf is affected by bacterial spot. Key symptoms include small dark brown lesions with yellow halos...",
    "selected_answer": "answer1",
    "selected_score": 4.7,
    "unselected_score": 3.2,
    "evaluation_reason": "Answer 1 provides more specific disease identification with detailed symptom description, making it more accurate and actionable."
  }
]
```

**New Fields:**
- `generation_answer` (string): The selected best answer
- `selected_answer` (string): Which answer was selected ("answer1" or "answer2")
- `selected_score` (float): Total score of selected answer (0-5.0 scale)
- `unselected_score` (float): Total score of unselected answer (0-5.0 scale)
- `evaluation_reason` (string): Explanation for the selection

## Evaluation Data Format

### Caption Evaluation Results

```json
[
  {
    "id": 0,
    "caption_preview": "Tomato leaf exhibiting symptoms of bacterial spot. Small, dark brown...",
    "rating": 9,
    "reasoning": "Caption accurately identifies plant and disease with specific symptom description"
  }
]
```

### Answer Evaluation Results (Diagnosis Task)

```json
[
  {
    "id": 0,
    "question": "Is this crop diseased?",
    "choice": 1,
    "reason": "Answer 1 provides more specific disease identification with detailed symptoms",
    "answer1_score": 47,
    "answer2_score": 32,
    "answer1_preview": "Yes, this tomato leaf is affected by bacterial spot...",
    "answer2_preview": "Yes, this is a tomato (Solanum lycopersicum) leaf..."
  }
]
```

**Score Breakdown (Diagnosis Task):**
- `plant_accuracy`: 0-10 points
- `disease_accuracy`: 0-10 points
- `symptom_accuracy`: 0-10 points
- `format_adherence`: 0-10 points
- `completeness`: 0-10 points
- **Total**: 0-50 points

### Answer Evaluation Results (Knowledge QA Task)

```json
[
  {
    "id": 0,
    "question": "What control methods are suitable for wheat leaf rust?",
    "choice": 1,
    "reason": "Answer 1 provides comprehensive control methods with specific chemical names and application details",
    "score1": 46,
    "score2": 35,
    "answer1_preview": "Control mainly relies on planting resistant varieties...",
    "answer2_preview": "Use fungicides when you see rust spots..."
  }
]
```

**Score Breakdown (Knowledge QA Task):**
- `accuracy`: 0-10 points
- `completeness`: 0-10 points
- `specificity`: 0-10 points
- `practicality`: 0-10 points
- `scientific_validity`: 0-10 points
- **Total**: 0-50 points

## Data Validation

### Required Fields by Stage

**Stage 1 (Caption Generation) Input:**
- ✅ `question_id`
- ✅ `image`
- ✅ `question`
- ✅ `answer`

**Stage 2 (VQA Generation) Input:**
- ✅ `question_id`
- ✅ `image`
- ✅ `question`
- ✅ `image_caption`

**Stage 3 (Answer Selection) Input:**
- ✅ `question_id`
- ✅ `question`
- ✅ `image_caption`
- ✅ `generation_answer1`
- ✅ `generation_answer2`

### Data Quality Checks

Before running each stage:

```python
def validate_step1_input(data):
    required_fields = ["question_id", "image", "question", "answer"]
    for item in data:
        for field in required_fields:
            assert field in item, f"Missing field: {field}"
            assert item[field], f"Empty field: {field}"
    return True

def validate_step2_input(data):
    required_fields = ["question_id", "image", "question", "image_caption"]
    for item in data:
        for field in required_fields:
            assert field in item, f"Missing field: {field}"
            assert item[field], f"Empty field: {field}"
    return True

def validate_step3_input(data):
    required_fields = ["question_id", "question", "image_caption",
                       "generation_answer1", "generation_answer2"]
    for item in data:
        for field in required_fields:
            assert field in item, f"Missing field: {field}"
            assert item[field], f"Empty field: {field}"
    return True
```

## Example Complete Pipeline

```json
// Input
{"question_id": "001", "image": "img.jpg", "question": "Is this diseased?", "answer": "Yes"}

// After Step 1
{"question_id": "001", "image": "img.jpg", "question": "Is this diseased?",
 "answer": "Yes", "image_caption": "Tomato leaf with bacterial spot...",
 "rating": 9, "evaluated": true}

// After Step 2
{"question_id": "001", "image_caption": "Tomato leaf with bacterial spot...",
 "question": "Is this diseased?", "answer": "Yes",
 "generation_answer1": "Yes, bacterial spot on tomato...",
 "generation_answer2": "Yes, tomato (Solanum lycopersicum) with bacterial spot..."}

// After Step 3
{"question_id": "001", "image_caption": "Tomato leaf with bacterial spot...",
 "question": "Is this diseased?", "answer": "Yes",
 "generation_answer": "Yes, bacterial spot on tomato...",
 "selected_answer": "answer1", "selected_score": 47, "unselected_score": 32,
 "evaluation_reason": "More specific disease identification"}
```

## Notes

- All JSON files should be UTF-8 encoded
- Image paths can be absolute or relative
- Scores are integers (not floats)
- All text fields should be non-empty strings
- Boolean fields use `true`/`false` (lowercase)
