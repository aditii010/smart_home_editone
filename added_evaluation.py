# added_evaluation.py
# --- MODIFIED: Created evaluation script for F1, confusion matrices, and explanation quality ---
"""
Evaluation script for LLMe2e Human Activity Recognition system.
Provides weighted F1 scores, confusion matrices, and explanation quality assessment.
"""

import os
import json
import csv
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from sklearn.metrics import f1_score, confusion_matrix, classification_report
from sklearn.preprocessing import LabelEncoder
import matplotlib.pyplot as plt
import seaborn as sns

# Local imports
from llm_interface import LLMe2eProcessor, LLMExplainer
from rag_engine import RAGEngine
from vision_module import VisionModule
from preprocess_dataset import DatasetPreprocessor, create_sample_states2json_data


class LLMe2eEvaluator:
    """
    Comprehensive evaluation system for LLMe2e pipeline including:
    - Recognition performance (F1, confusion matrix)
    - Explanation quality assessment  
    - Sample window analysis with comparisons
    """
    
    def __init__(self, use_cloud_llm: bool = False, local_llm_mode: bool = True):
        """
        Initialize evaluator with LLM configuration options.
        
        Args:
            use_cloud_llm: Whether to use external cloud LLM services (default False for offline testing)
            local_llm_mode: Whether to use local LLM or mock responses for testing
        """
        self.use_cloud_llm = use_cloud_llm
        self.local_llm_mode = local_llm_mode
        
        # Initialize components
        self.processor = LLMe2eProcessor()
        self.explainer = LLMExplainer()
        self.rag_engine = RAGEngine()
        self.vision_module = VisionModule()
        self.dataset_preprocessor = DatasetPreprocessor()
        
        # Results storage
        self.evaluation_results = []
        self.explanation_samples = []
        
        # Mock LLM responses for offline testing
        self.mock_responses = {
            "cooking": "ACTIVITY={'cooking'} EXPLANATION={'I predicted the activity cooking mainly because motion was detected in the kitchen and the microwave was activated'}",
            "walking": "ACTIVITY={'walking'} EXPLANATION={'I predicted the activity walking mainly because continuous motion was detected with consistent acceleration patterns'}",
            "watching_tv": "ACTIVITY={'watching_tv'} EXPLANATION={'I predicted the activity watching TV mainly because a person was detected near the TV and it was turned on'}",
            "unknown": "ACTIVITY={'unknown'} EXPLANATION={'I am not certain, but most likely the activity is unclear due to insufficient sensor evidence'}"
        }
    
    def evaluate_recognition_performance(self, test_data: List[Dict]) -> Dict:
        """
        Evaluate activity recognition performance on test dataset.
        
        Args:
            test_data: List of test windows with ground truth labels
            
        Returns:
            Dictionary with evaluation metrics
        """
        print("[Eval] Starting recognition performance evaluation...")
        
        if not test_data:
            print("[Eval] No test data provided, using sample data")
            test_data = [create_sample_states2json_data()]
        
        predictions = []
        ground_truths = []
        confidence_scores = []
        
        for i, window in enumerate(test_data):
            print(f"[Eval] Processing window {i+1}/{len(test_data)}: {window.get('window_id', f'window_{i}')}")
            
            # Extract data
            states_data = window.get("states2json", {})
            ground_truth = window.get("ground_truth", "unknown")
            
            # Get prediction using LLMe2e processor
            try:
                if self.local_llm_mode and not self.use_cloud_llm:
                    # Use mock response for offline testing
                    prediction_result = self._get_mock_prediction(states_data, ground_truth)
                else:
                    # Use actual LLM
                    prediction_result = self.processor.process_states2json(
                        states_data=states_data,
                        user_query="",
                        spatial_context="",
                        habit_context=""
                    )
                
                predicted_activity = prediction_result.get("activity", "unknown")
                confidence = prediction_result.get("confidence", 0.0)
                
                predictions.append(predicted_activity)
                ground_truths.append(ground_truth)
                confidence_scores.append(confidence)
                
                # Store detailed results
                self.evaluation_results.append({
                    "window_id": window.get("window_id", f"window_{i}"),
                    "predicted_activity": predicted_activity,
                    "ground_truth": ground_truth,
                    "confidence": confidence,
                    "explanation": prediction_result.get("explanation", ""),
                    "evidence_states": prediction_result.get("evidence_states", []),
                    "correct": predicted_activity == ground_truth
                })
                
            except Exception as e:
                print(f"[Eval] Error processing window {i}: {e}")
                predictions.append("unknown")
                ground_truths.append(ground_truth)
                confidence_scores.append(0.0)
        
        # Calculate metrics
        metrics = self._calculate_metrics(ground_truths, predictions, confidence_scores)
        
        print(f"[Eval] Recognition evaluation complete:")
        print(f"  Accuracy: {metrics['accuracy']:.3f}")
        print(f"  Weighted F1: {metrics['weighted_f1']:.3f}")
        print(f"  Average Confidence: {metrics['avg_confidence']:.3f}")
        
        return metrics
    
    def _get_mock_prediction(self, states_data: Dict, ground_truth: str) -> Dict:
        """Generate mock prediction for offline testing."""
        # Simple heuristic based on states
        if "PersonNearMicrowave" in states_data or "LightKitchenOn" in states_data:
            activity = "cooking"
        elif "PersonMoving" in states_data:
            activity = "walking"
        elif "PersonNearTv" in states_data:
            activity = "watching_tv"
        else:
            activity = "unknown"
        
        # Use mock response
        mock_response = self.mock_responses.get(activity, self.mock_responses["unknown"])
        
        # Parse mock response
        import re
        activity_match = re.search(r"ACTIVITY=\{['\"]([^'\"]+)['\"]\}", mock_response)
        explanation_match = re.search(r"EXPLANATION=\{['\"]([^'\"]+)['\"]\}", mock_response)
        
        return {
            "activity": activity_match.group(1) if activity_match else "unknown",
            "explanation": explanation_match.group(1) if explanation_match else "Mock explanation",
            "confidence": 0.8 if activity != "unknown" else 0.3,
            "evidence_states": list(states_data.keys())[:3],  # Top 3 states as evidence
            "structured_output": mock_response
        }
    
    def _calculate_metrics(self, y_true: List[str], y_pred: List[str], 
                          confidence_scores: List[float]) -> Dict:
        """Calculate comprehensive evaluation metrics."""
        
        # Encode labels for sklearn
        all_labels = list(set(y_true + y_pred))
        label_encoder = LabelEncoder()
        label_encoder.fit(all_labels)
        
        y_true_encoded = label_encoder.transform(y_true)
        y_pred_encoded = label_encoder.transform(y_pred)
        
        # Calculate metrics
        accuracy = np.mean(np.array(y_true) == np.array(y_pred))
        weighted_f1 = f1_score(y_true_encoded, y_pred_encoded, average='weighted')
        macro_f1 = f1_score(y_true_encoded, y_pred_encoded, average='macro')
        
        # Confidence statistics
        avg_confidence = np.mean(confidence_scores)
        confidence_std = np.std(confidence_scores)
        
        # Classification report
        class_report = classification_report(y_true, y_pred, output_dict=True)
        
        # Confusion matrix
        conf_matrix = confusion_matrix(y_true, y_pred, labels=all_labels)
        
        return {
            "accuracy": accuracy,
            "weighted_f1": weighted_f1,
            "macro_f1": macro_f1,
            "avg_confidence": avg_confidence,
            "confidence_std": confidence_std,
            "classification_report": class_report,
            "confusion_matrix": conf_matrix,
            "labels": all_labels,
            "n_samples": len(y_true)
        }
    
    def generate_confusion_matrix_plot(self, metrics: Dict, save_path: str = "confusion_matrix.png"):
        """Generate and save confusion matrix visualization."""
        plt.figure(figsize=(8, 6))
        
        conf_matrix = metrics["confusion_matrix"]
        labels = metrics["labels"]
        
        sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='Blues',
                   xticklabels=labels, yticklabels=labels)
        
        plt.title("Activity Recognition Confusion Matrix")
        plt.xlabel("Predicted Activity")
        plt.ylabel("True Activity")
        plt.tight_layout()
        
        try:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"[Eval] Confusion matrix saved to: {save_path}")
        except Exception as e:
            print(f"[Eval] Error saving confusion matrix: {e}")
        
        plt.close()
    
    def sample_explanations(self, test_data: List[Dict], n_samples: int = 5) -> List[Dict]:
        """
        Sample N windows and generate explanations from both data-driven and LLM explainers.
        
        Args:
            test_data: Test dataset
            n_samples: Number of samples to analyze
            
        Returns:
            List of explanation analysis results
        """
        print(f"[Eval] Generating explanation samples for {n_samples} windows...")
        
        if not test_data:
            test_data = [create_sample_states2json_data()]
        
        # Select random samples
        sample_indices = np.random.choice(len(test_data), min(n_samples, len(test_data)), replace=False)
        sampled_windows = [test_data[i] for i in sample_indices]
        
        explanation_results = []
        
        for i, window in enumerate(sampled_windows):
            window_id = window.get("window_id", f"sample_{i}")
            states_data = window.get("states2json", {})
            ground_truth = window.get("ground_truth", "unknown")
            
            print(f"[Eval] Analyzing explanations for window: {window_id}")
            
            try:
                # Get LLM prediction and explanation
                if self.local_llm_mode and not self.use_cloud_llm:
                    llm_result = self._get_mock_prediction(states_data, ground_truth)
                else:
                    llm_result = self.processor.process_states2json(states_data=states_data)
                
                # Get data-driven explanation (rule-based analysis)
                data_driven_explanation = self._generate_data_driven_explanation(states_data, ground_truth)
                
                # Compare explanations
                explanation_analysis = {
                    "window_id": window_id,
                    "ground_truth": ground_truth,
                    "predicted_activity": llm_result.get("activity", "unknown"),
                    "llm_explanation": llm_result.get("explanation", ""),
                    "llm_confidence": llm_result.get("confidence", 0.0),
                    "data_driven_explanation": data_driven_explanation,
                    "important_states": list(states_data.keys()),
                    "explanation_quality": self._assess_explanation_quality(
                        llm_result.get("explanation", ""),
                        states_data,
                        ground_truth
                    )
                }
                
                explanation_results.append(explanation_analysis)
                self.explanation_samples.append(explanation_analysis)
                
            except Exception as e:
                print(f"[Eval] Error generating explanation for {window_id}: {e}")
        
        return explanation_results
    
    def _generate_data_driven_explanation(self, states_data: Dict, ground_truth: str) -> str:
        """
        Generate rule-based explanation from sensor data.
        This represents a traditional data-driven explainer for comparison.
        """
        active_states = [state for state, windows in states_data.items() if windows]
        
        if not active_states:
            return "No significant sensor activity detected during this time window."
        
        # Rule-based explanation logic
        explanation_parts = []
        
        # Check for location-specific patterns
        kitchen_states = [s for s in active_states if "Kitchen" in s or "Microwave" in s]
        if kitchen_states:
            explanation_parts.append("kitchen area activity detected")
        
        living_room_states = [s for s in active_states if "Living" in s or "Tv" in s]
        if living_room_states:
            explanation_parts.append("living room engagement observed")
        
        # Check for motion patterns
        motion_states = [s for s in active_states if "Motion" in s or "Moving" in s]
        if motion_states:
            explanation_parts.append("movement patterns consistent with activity")
        
        # Check for device interactions
        device_states = [s for s in active_states if any(device in s for device in ["Light", "Door", "Microwave", "Tv"])]
        if device_states:
            explanation_parts.append(f"interaction with {len(device_states)} smart home devices")
        
        base_explanation = "Data-driven analysis indicates " + ", ".join(explanation_parts) + "."
        
        # Add confidence qualifier based on number of supporting states
        if len(active_states) >= 3:
            return f"High confidence: {base_explanation}"
        elif len(active_states) >= 2:
            return f"Medium confidence: {base_explanation}"
        else:
            return f"Low confidence: {base_explanation}"
    
    def _assess_explanation_quality(self, explanation: str, states_data: Dict, ground_truth: str) -> Dict:
        """
        Assess the quality of LLM-generated explanations.
        
        Returns quality metrics including:
        - Relevance: Does explanation mention relevant sensor states?
        - Completeness: Does it cover the main evidence?
        - Clarity: Is it understandable to users?
        - Accuracy: Does it align with ground truth?
        """
        explanation_lower = explanation.lower()
        active_states = list(states_data.keys())
        
        # Relevance: Check if explanation mentions relevant states/concepts
        relevance_score = 0.0
        mentioned_concepts = []
        
        for state in active_states:
            # Extract concepts from state names
            if "kitchen" in state.lower() and "kitchen" in explanation_lower:
                relevance_score += 0.2
                mentioned_concepts.append("kitchen")
            elif "motion" in state.lower() and ("motion" in explanation_lower or "movement" in explanation_lower):
                relevance_score += 0.2
                mentioned_concepts.append("movement")
            elif "light" in state.lower() and "light" in explanation_lower:
                relevance_score += 0.1
                mentioned_concepts.append("lighting")
            elif "door" in state.lower() and "door" in explanation_lower:
                relevance_score += 0.1
                mentioned_concepts.append("door")
        
        relevance_score = min(1.0, relevance_score)
        
        # Completeness: Length and detail appropriateness
        word_count = len(explanation.split())
        if 10 <= word_count <= 30:
            completeness_score = 1.0
        elif 5 <= word_count < 10 or 30 < word_count <= 50:
            completeness_score = 0.7
        else:
            completeness_score = 0.5
        
        # Clarity: Check for user-friendly language (no technical jargon)
        clarity_score = 1.0
        technical_terms = ["sensor", "timestamp", "json", "state", "api"]
        for term in technical_terms:
            if term in explanation_lower:
                clarity_score -= 0.2
        clarity_score = max(0.0, clarity_score)
        
        # Accuracy: Alignment with ground truth activity
        accuracy_score = 1.0 if ground_truth.lower() in explanation_lower else 0.5
        
        return {
            "relevance": relevance_score,
            "completeness": completeness_score, 
            "clarity": clarity_score,
            "accuracy": accuracy_score,
            "overall_quality": (relevance_score + completeness_score + clarity_score + accuracy_score) / 4.0,
            "mentioned_concepts": mentioned_concepts,
            "word_count": word_count
        }
    
    def save_evaluation_results(self, output_dir: str = "evaluation_results"):
        """Save comprehensive evaluation results to CSV and JSON files."""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed results CSV
        if self.evaluation_results:
            results_df = pd.DataFrame(self.evaluation_results)
            results_csv_path = os.path.join(output_dir, f"evaluation_results_{timestamp}.csv")
            results_df.to_csv(results_csv_path, index=False)
            print(f"[Eval] Evaluation results saved to: {results_csv_path}")
        
        # Save explanation samples CSV
        if self.explanation_samples:
            explanations_df = pd.DataFrame(self.explanation_samples)
            explanations_csv_path = os.path.join(output_dir, f"explanation_samples_{timestamp}.csv")
            explanations_df.to_csv(explanations_csv_path, index=False)
            print(f"[Eval] Explanation samples saved to: {explanations_csv_path}")
        
        # Save summary JSON
        summary = {
            "evaluation_timestamp": timestamp,
            "total_windows_evaluated": len(self.evaluation_results),
            "explanation_samples_generated": len(self.explanation_samples),
            "configuration": {
                "use_cloud_llm": self.use_cloud_llm,
                "local_llm_mode": self.local_llm_mode
            }
        }
        
        if self.evaluation_results:
            accuracy = np.mean([r["correct"] for r in self.evaluation_results])
            avg_confidence = np.mean([r["confidence"] for r in self.evaluation_results])
            summary.update({
                "overall_accuracy": accuracy,
                "average_confidence": avg_confidence
            })
        
        summary_path = os.path.join(output_dir, f"evaluation_summary_{timestamp}.json")
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"[Eval] Evaluation summary saved to: {summary_path}")


def run_comprehensive_evaluation():
    """
    Main evaluation function that runs the complete LLMe2e evaluation pipeline.
    """
    print("🔬 LLMe2e Comprehensive Evaluation")
    print("=" * 60)
    
    # Initialize evaluator in local mode for offline testing
    evaluator = LLMe2eEvaluator(use_cloud_llm=False, local_llm_mode=True)
    
    # Load or create test data
    print("📁 Loading test data...")
    test_data = []
    
    try:
        # Try to load processed test data
        dataset_preprocessor = DatasetPreprocessor()
        uci_test = dataset_preprocessor.load_processed_data("uci_adl_test.json")
        marble_test = dataset_preprocessor.load_processed_data("marble_test.json")
        
        test_data = uci_test + marble_test
        
    except Exception as e:
        print(f"[Eval] Could not load processed datasets: {e}")
    
    # Use sample data if no real datasets available
    if not test_data:
        print("📝 Using sample data for evaluation...")
        test_data = [create_sample_states2json_data() for _ in range(10)]  # Create 10 sample windows
        
        # Add some variety to sample data
        for i, window in enumerate(test_data):
            if i % 3 == 0:
                window["ground_truth"] = "walking"
                window["states2json"] = {"PersonMoving": [["10:00:00", "10:01:00"]]}
            elif i % 3 == 1:
                window["ground_truth"] = "watching_tv"
                window["states2json"] = {"PersonNearTv": [["19:00:00", "19:30:00"]], "LightLivingRoomOn": [["19:00:00", "19:30:00"]]}
    
    print(f"📊 Evaluating on {len(test_data)} test windows")
    
    # Run recognition performance evaluation
    print("\n🎯 Evaluating recognition performance...")
    metrics = evaluator.evaluate_recognition_performance(test_data)
    
    # Generate confusion matrix
    evaluator.generate_confusion_matrix_plot(metrics)
    
    # Sample explanations for quality analysis
    print("\n💬 Generating explanation samples...")
    explanation_samples = evaluator.sample_explanations(test_data, n_samples=5)
    
    # Print sample explanations for review
    print("\n📋 Sample Explanations for Review:")
    print("-" * 50)
    for i, sample in enumerate(explanation_samples[:3], 1):
        print(f"\nSample {i}: {sample['window_id']}")
        print(f"Ground Truth: {sample['ground_truth']}")
        print(f"Predicted: {sample['predicted_activity']}")