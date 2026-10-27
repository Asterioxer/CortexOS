---
title: "Explainable AI (XAI) & Model Interpretability Workspace"
type: "workspace_catalog"
tags:
  - cortex/workspaces
  - cortex/xai
  - cortex/interpretability
  - cortex/responsible_ai
  - cortex/shap_lime
last_updated: "2026-10-27"
status: "verified"
---

# 🔍 Explainable AI (XAI) & Model Interpretability Workspace

- **Location**: `C:\Users\soham\Desktop\xai`
- **Domain**: Machine Learning Interpretability, Post-hoc Explanations, Monotonic Constraints, Responsible AI & Fairness
- **Context**: B.Tech 4th Year Advanced Machine Learning & Interpretability Curriculum and Practical Implementation Suite
- **Primary Toolchains**: Python 3 (XGBoost, LightGBM, scikit-learn, shap, lime, alibi, matplotlib, seaborn)

## 📚 Curriculum Structure & Artifacts

| Unit / Artifact | Format / Size | Focus & Key Concepts |
|---|---|---|
| **`XAI_Unit1_Foundations.pptx`** | PPTX (991 KB) | Foundations of Interpretability, Black-box vs. White-box models, Trade-offs between accuracy and explainability, Intrinsic vs. Post-hoc interpretability. |
| **`XAI_Monotone_Constraints_Demo.ipynb`** | Jupyter (35 KB) | Practical implementation of Monotonic Constraints in gradient boosting (XGBoost / LightGBM) to prevent non-monotonic "zigzag" artifacts and enforce domain logic. |
| **`XAI_Unit2_Model_Agnostic_Methods.docx`** | DOCX (52 KB) | Theory of model-agnostic local and global explanation methods. |
| **`XAI_Unit2_Practical_Programs _on _all_techniques.ipynb`** | Jupyter (53 KB) | Hands-on code implementations for all 9 core model-agnostic explanation techniques. |
| **`XAI_Unit3_DL_NLP_Explainability.docx`** | DOCX (76 KB) | Deep Learning & NLP Explainability: Saliency maps, Integrated Gradients, Grad-CAM, Layer-wise Relevance Propagation (LRP), and Transformer attention visualization. |
| **`XAI_Unit4_Evaluation_Bias_ResponsibleAI.docx`** | DOCX (73 KB) | Evaluation metrics for explanations, Faithfulness, Stability, Algorithmic Fairness (Demographic Parity, Equal Opportunity, Disparate Impact), and Responsible AI governance. |
| **`flutter_testing_notes.docx`** | DOCX (41 KB) | Unit, widget, and integration testing methodologies for client frontend interfaces. |

---

## 🔬 The 9 Model-Agnostic Techniques Implemented in Unit 2

The notebook `XAI_Unit2_Practical_Programs _on _all_techniques.ipynb` provides functional code implementations for:

1. **LIME (Local Interpretable Model-Agnostic Explanations)**:
   - Fits a locally weighted linear surrogate model in the perturbed neighborhood of a single query instance.
   - Answers: *"Which features drove this individual prediction locally?"*
2. **SHAP (SHapley Additive exPlanations)**:
   - Computes game-theoretic Shapley values to fairly distribute the payoff (prediction delta from base rate) among all input features.
   - Satisfies efficiency, symmetry, dummy player, and additivity axioms.
3. **PDP (Partial Dependence Plots)**:
   - Marginalizes over all other features to show the average marginal effect of 1 or 2 features on the predicted outcome globally.
4. **ICE (Individual Conditional Expectation)**:
   - Disaggregates PDPs by plotting one curve per data instance, uncovering hidden feature interactions and heterogeneous effects.
5. **ALE (Accumulated Local Effects)**:
   - Computes differences in conditional predictions over small windows; avoids evaluating models on impossible feature combinations when features are correlated.
6. **Permutation Feature Importance (PFI)**:
   - Shuffles a feature's values across validation samples and measures the degradation in validation loss/metric.
7. **Global Surrogate Model**:
   - Trains an intrinsically interpretable model (e.g., shallow decision tree or linear regression) to mimic the black-box predictions globally, reporting $R^2$ fidelity.
8. **Anchors (High-Precision Rules)**:
   - Discovers local IF-THEN rules that "anchor" the prediction such that changes to other features rarely alter the model's decision.
9. **Counterfactual Explanations**:
   - Finds the minimal perturbation to feature inputs required to flip the predicted classification (e.g., *"What minimum increase in salary would convert a loan rejection into an approval?"*).

---

## ⚡ Monotone Constraints in Gradient Boosting

In `XAI_Monotone_Constraints_Demo.ipynb`, Soham demonstrates why unconstrained gradient boosting trees often overfit to noise in small data slices, producing non-monotonic "zigzag" predictions that violate domain axioms (e.g., higher credit score leading to lower approved loan amount).

### Technical Solution
Enforces monotone constraints in XGBoost via the `monotone_constraints` hyperparameter tuple:
- `+1`: Enforces monotonic non-decreasing output as feature increases.
- `-1`: Enforces monotonic non-increasing output.
- `0`: Unconstrained.

$$\frac{\partial \hat{y}}{\partial x_i} \ge 0 \quad (\text{for } c_i = +1)$$

This guarantees domain plausibility and improves model trust without sacrificing global predictive power.

---

## 🧠 Grounding & Value for CortexOS
CortexOS uses these exact XAI principles to explain its own internal reasoning and heuristic arbitration:
- **Feature Attribution**: Explaining why the [[06_Self_Evolution/Heuristic_Adaptation_Matrix|Heuristic Adaptation Matrix]] shifted weights between Analytic, Pragmatic, and Cautious perspectives.
- **Counterfactual Introspection**: Determining what change in system entropy or resource pressure would cause CortexOS to escalate an action to the operator.

---
## Related Notes
- [[07_Workspace_Index/Desktop_Workspace_Master_Index|Desktop Workspace Master Index]]
- [[05_System_State/Filesystem_and_Workspaces|Filesystem and Workspaces]]
- [[06_Self_Evolution/Heuristic_Adaptation_Matrix|Heuristic Adaptation Matrix]]
- [[01_Architecture/Global_Workspace_Theory|Global Workspace Theory]]
- [[06_Self_Evolution/Introspection_Ledger|Introspection Ledger]]
