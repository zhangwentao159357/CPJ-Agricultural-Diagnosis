# File and Folder Renaming Guide

## Current Structure Issues
1. Inconsistent folder naming (mixed spaces, no underscores)
2. Code files contain model names (should be generic)
3. Some files have Chinese characters
4. Data files have very long, inconsistent names

## Proposed New Structure

```
CPJ-Agricultural-Pest-Diagnosis/
├── 1_caption_enhancement/
│   ├── caption_evaluate_optimize.py          # Unified caption judge & optimize
│   ├── diagnosis_caption_generator.py         # Caption generation for diagnosis
│   ├── knowledge_caption_generator.py         # Caption generation for knowledge QA
│   └── data/
│       ├── diagnosis_captions_refined.json
│       └── knowledge_captions_refined.json
│
├── 2_vqa_generation/
│   ├── diagnosis_vqa.py                       # Disease diagnosis VQA
│   ├── knowledge_qa_vqa.py                    # Knowledge QA VQA
│   └── data/
│       ├── diagnosis_dual_answers.json
│       └── knowledge_qa_dual_answers.json
│
├── 3_answer_selection/
│   ├── diagnosis_judge.py                     # Judge for diagnosis
│   ├── knowledge_qa_judge.py                  # Judge for knowledge QA
│   ├── add_evaluation_scores.py               # Utility to add scores
│   └── data/
│       ├── diagnosis_final_answers.json
│       └── knowledge_qa_final_answers.json
│
├── dataset/                                   # Original images
├── docs/                                      # Documentation
│   ├── architecture_diagram.png
│   └── results_table.png
├── README.md
├── CONFIGURATION.md
├── DATA_FORMAT.md
├── LICENSE
├── requirements.txt
└── .gitignore
```

## Detailed Renaming Plan

### Folder Renaming

| Old Name | New Name | Reason |
|----------|----------|--------|
| `step1Image Interpretability and Caption Enhancement` | `1_caption_enhancement` | Shorter, consistent, no spaces |
| `step2 Explanational caption-Optimized VQA` | `2_vqa_generation` | Shorter, clearer purpose |
| `step3 LLM-as-a-Judge Answer Selection` | `3_answer_selection` | Shorter, clearer purpose |
| `caption_judge/` | (merge into `1_caption_enhancement/`) | Simplify structure |

### Code File Renaming

#### Step 1 (Caption Enhancement)

| Old Name | New Name | Changes |
|----------|----------|---------|
| `caption-dieases-judge.py` | `caption_evaluate_optimize.py` | Fix typo, clearer name |
| `caption-judge-dieases(cannot-generate-optimized-results)-improve.py` | _(delete)_ | Redundant with unified script |
| `caption-konwledge-judge.py` | _(use unified script)_ | Fix typo, use unified |
| `lowscore_compensation_code.py` (disease) | _(delete)_ | Merged into unified script |
| `lowscore_compensation_code.py` (diagnosis) | _(delete)_ | Merged into unified script |
| `caption_for_knowledge-no-generation-typename.py` | `knowledge_caption_generator.py` | Clearer name |

#### Step 2 (VQA Generation)

| Old Name | New Name | Changes |
|----------|----------|---------|
| `gpt_5_nano_langchain_pairs_five_shot.py` | `diagnosis_vqa.py` | Remove model name, clearer purpose |
| `know_gpt_5_nano_langchain_pairs_three_shot.py` | `knowledge_qa_vqa.py` | Remove model name, clearer purpose |

#### Step 3 (Answer Selection)

| Old Name | New Name | Changes |
|----------|----------|---------|
| `diage-judge.py` | `diagnosis_judge.py` | Fix typo, consistent naming |
| `judge-knowledge_two_input.py` | `knowledge_qa_judge.py` | Consistent naming |
| `add_scores_to_existing_data.py` | `add_evaluation_scores.py` | Clearer name |

### Data File Renaming

#### Step 1 Data

| Old Name | New Name | Type |
|----------|----------|------|
| `disease_diagnosis_improved.json` | `diagnosis_captions_refined.json` | Diagnosis captions |
| `disease_knowledge_caption_out-noname.json` | `knowledge_captions_initial.json` | Knowledge captions (before refine) |
| `knowledge_caption_improve.json` | `knowledge_captions_refined.json` | Knowledge captions (after refine) |
| `disease_knowledge_caption_out-noname_improve_improve_answer1.json` | _(delete)_ | Redundant |

#### Step 2 Data

| Old Name | New Name | Type |
|----------|----------|------|
| `disease_diagnosis_caption_improved5out.json` | `diagnosis_dual_answers.json` | Diagnosis with 2 answers |
| `disease_knowledge_caption_out-noname_improve-five_answer.json` | `knowledge_qa_dual_answers.json` | Knowledge QA with 2 answers |

#### Step 3 Data

| Old Name | New Name | Type |
|----------|----------|------|
| `disease_diagnosis_caption_improved5out-2to1v2.json` | `diagnosis_final_answers.json` | Final diagnosis answers |
| `qwen72-disease_knowledge_caption_improve_out-noname_qwenchat_five-shot_answerto1.json` | `knowledge_qa_final_answers.json` | Final knowledge QA answers |
| `evaluation_results5.json` | `diagnosis_evaluation_details.json` | Diagnosis evaluation details |
| `evaluation_qwen72-disease_knowledge_caption_improve_out-noname_qwenchat_five-shot_answerto1.json` | `knowledge_qa_evaluation_details.json` | Knowledge QA evaluation details |

## File Purpose Descriptions

### 1_caption_enhancement/

- **caption_evaluate_optimize.py**: Unified script that generates, evaluates, and optimizes captions in one pass. Works for both diagnosis and knowledge QA tasks.
- **diagnosis_caption_generator.py**: Specialized caption generation for diagnosis images (optional, if needed for specific use cases)
- **knowledge_caption_generator.py**: Specialized caption generation for knowledge QA images

### 2_vqa_generation/

- **diagnosis_vqa.py**: Generates dual complementary answers for disease diagnosis tasks
  - Answer 1: Focus on disease/pest identification with symptoms
  - Answer 2: Focus on crop identification with morphology
- **knowledge_qa_vqa.py**: Generates dual complementary answers for knowledge QA tasks
  - Answer 1: Treatment, prevention, and control methods
  - Answer 2: Disease explanation (symptoms, causes, lifecycle)

### 3_answer_selection/

- **diagnosis_judge.py**: LLM-as-a-Judge to select the best answer from two diagnosis answers
- **knowledge_qa_judge.py**: LLM-as-a-Judge to select the best answer from two knowledge QA answers
- **add_evaluation_scores.py**: Utility to add or update evaluation scores in existing judged data

## Implementation Steps

1. Create new folder structure
2. Copy and rename files according to the plan
3. Update import paths in code files
4. Update file path references in README.md
5. Update CONFIGURATION.md and DATA_FORMAT.md to reflect new names
6. Delete old redundant files
7. Test the pipeline with new structure

## Benefits of New Structure

1. **Clarity**: File names clearly indicate their purpose
2. **Consistency**: All files follow the same naming convention
3. **Maintainability**: Easier to find and modify specific components
4. **Professional**: Follows Python naming conventions (snake_case)
5. **Model-agnostic**: No model names in file names (configurable in code)
6. **Internationalization**: All English names (no Chinese characters)
7. **Simplicity**: Shorter, more memorable names
