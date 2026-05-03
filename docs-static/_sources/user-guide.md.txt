# User Guide

This guide provides instructions for Teaching Assistants (TAs) using the SciPro Review system.

## For Teaching Assistants

### Starting a Review
Use the New Review card to begin. Select the correct assignment from the dropdown and enter the student identifier. This initializes a new grading session.

### Student vs Teacher Mode
The system operates in two primary modes. Student mode shows peer feedback only with no grading. Teacher mode enables full grading with rubric checkboxes and dimension sliders.

### Criteria Checklist
Rubrics are split into three sentiment categories:
- **Positive**: Praise-worthy items that add positive feedback.
- **Neutral**: Suggestions for improvement without harsh deductions.
- **Negative**: Critical errors that generate corrective feedback and potentially reduce scores.

### Grading Dimensions
Final grades are calculated using five weighted dimensions. Adjust the sliders in the sidebar to refine the final score.

| Dimension | Weight | Max Score |
| :--- | :---: | :---: |
| Code Quality & Design | 4 | 6 |
| Code Execution & Results | 4 | 6 |
| Assignment Requirements | 4 | 6 |
| Scientific Programming | 4 | 6 |
| Creativity | 1 | 4 |

### Grade Boundaries
The system maps weighted percentages to the German 1.0–5.0 scale. Boundaries are fixed and not curved to ensure fair, rubric-based evaluation. US letter equivalents are shown for reference during international exchanges, but the canonical grade is always the German decimal.

| German Grade | US Equiv | Percentage |
| :--- | :---: | :--- |
| 1.0 | A+ | 95% + |
| 1.3 | A | 90% |
| 1.7 | A- | 85% |
| 2.0 | B+ | 80% |
| 2.3 | B | 75% |
| 2.7 | B- | 70% |
| 3.0 | C+ | 65% |
| 3.3 | C | 60% |
| 3.7 | C- | 55% |
| 4.0 | D | 50% |
| 5.0 | F | below 50% |

### Data Management
- **Save**: Explicitly move a session to permanent storage.
- **Export**: Download all saved reviews as a JSON file for sharing.
- **Import**: Load a JSON file to merge reviews from other graders.

### Keyboard Shortcuts
- `Ctrl+S`: Save current review
- `Ctrl+Z`: Undo last action
- `Ctrl+Y`: Redo undone action
- `Alt+Shift+G`: Toggle Teacher Mode (settings page only)

### Offline Usage
The app is client-side only. After the initial load, it works without internet. Data is persisted via IndexedDB. If the page crashes, the current session is auto-recovered.

---

- [Contributing Guide](./contributing.md)
- [Architecture](./architecture.md)
