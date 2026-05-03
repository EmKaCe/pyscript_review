# Grading System Guide

This document explains the German grading system implemented in SciPro Review.

## Grading Scale

The system uses the standard German university grading scale from 1.0 to 5.0:

| Grade | Description |
|-------|-------------|
| 1.0   | Excellent |
| 1.3   | Very Good+ |
| 1.7   | Very Good |
| 2.0   | Good+ |
| 2.3   | Good |
| 2.7   | Good- |
| 3.0   | Satisfactory+ |
| 3.3   | Satisfactory |
| 3.7   | Satisfactory- |
| 4.0   | Sufficient (Pass) |
| 5.0   | Fail |

## Grading Dimensions

The final grade is calculated based on 5 weighted dimensions:

1. **Completeness**: Does the submission cover all requirements?
2. **Correctness**: Is the implementation technically accurate?
3. **Quality**: Is the code clean and maintainable?
4. **Documentation**: Is the manuscript well-documented?
5. **Approach**: Was an appropriate methodology used?

## Grade Calculation Logic

The system employs a "quality floor" approach. If a critical criterion is marked as "not met", the grade cannot exceed a certain boundary, regardless of performance in other dimensions.

### Near-Fence Detection

The `GradeCalculator` includes logic to detect "near-fence" scenarios where a student's performance is very close to a grade boundary. This allows reviewers to provide targeted feedback to help the student reach the next grade level.
