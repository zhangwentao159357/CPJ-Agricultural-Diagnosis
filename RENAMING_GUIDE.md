# File and Folder Structure Guide

## Current Repository Structure

This document describes the current repository structure after organization and cleanup.

```
CPJ-Agricultural-Diagnosis/
├── step1_caption_generation&enhancement/  # 📝 Caption generation & refinement
│   ├── caption_generation.py              (Initial caption generation)
│   ├── caption_judge_optimize.py          (Unified caption eval & optimization)
│   └── data/
│       └── refined_captions_sample.json   (Sample refined captions)
│
├── step2_vqa_generation/                  # 🎯 Dual-answer generation
│   ├── diagnosis_vqa.py                   (Disease diagnosis task)
│   ├── knowledge_qa_vqa.py                (Knowledge QA task)
│   └── data/
│       └── dual_answers_sample.json       (Sample dual-answer VQA outputs)
│
├── step3_answer_selection/                # ⚖️ LLM-as-a-Judge selection
│   ├── diagnosis_judge.py                 (Diagnosis task judge)
│   ├── knowledge_qa_judge.py              (Knowledge QA task judge)
│   └── data/
│       └── judged_answers_sample.json     (Sample judged answers with scores)
│
├── dataset/                               # CDDMBench images
│   └── README.md                          (Download instructions)
│
├── docs/                                  # Documentation images
│   └── framework.png                      (CPJ pipeline diagram)
│
├── PROMPTS_AND_EVALUATION.md             # 🔥 Complete evaluation details
├── CONFIGURATION.md                       # ⚙️ Setup guide
├── DATA_FORMAT.md                         # 📋 Data specifications
├── requirements.txt                       # 📦 Dependencies
├── LICENSE                                # MIT License
└── README.md                              # Main documentation
```

## File Purpose Descriptions

### step1_caption_generation&enhancement/

- **caption_generation.py**: Initial caption generation using Vision-Language Models
  - Generates descriptive captions without naming crops or diseases
  - Uses few-shot prompting for consistent output
  - Supports command-line arguments for input/output files

- **caption_judge_optimize.py**: Unified script for caption evaluation and optimization
  - Evaluates caption quality on a 5-point scale
  - Automatically refines captions scoring below threshold
  - Works for both diagnosis and knowledge QA tasks

### step2_vqa_generation/

- **diagnosis_vqa.py**: Generates dual complementary answers for disease diagnosis tasks
  - Answer 1: Focus on disease/pest identification with symptoms
  - Answer 2: Focus on crop identification with morphology

- **knowledge_qa_vqa.py**: Generates dual complementary answers for knowledge QA tasks
  - Answer 1: Treatment, prevention, and control methods
  - Answer 2: Disease explanation (symptoms, causes, lifecycle)

### step3_answer_selection/

- **diagnosis_judge.py**: LLM-as-a-Judge to select the best answer from two diagnosis answers
  - Evaluates on plant accuracy, disease accuracy, symptom accuracy, format, and completeness
  - Provides numerical scores and transparent reasoning

- **knowledge_qa_judge.py**: LLM-as-a-Judge to select the best answer from two knowledge QA answers
  - Evaluates on accuracy, completeness, specificity, practicality, and scientific validity
  - Provides numerical scores and transparent reasoning

## Key Design Principles

1. **No Bias**: Captions exclude crop and disease names to minimize VQA bias
2. **Explainability**: All decisions include transparent scoring and reasoning
3. **Modularity**: Each step is independent and can be run separately
4. **Reproducibility**: All prompts and evaluation criteria are documented
5. **Maintainability**: Clear naming conventions and consistent structure
