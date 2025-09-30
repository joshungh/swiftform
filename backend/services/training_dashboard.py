"""
Training Dashboard and Enhanced Management for SwiftformAI
Provides comprehensive monitoring and management of training jobs
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from openai import OpenAI
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class TrainingDashboard:
    """Enhanced training dashboard with analytics and monitoring"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize training dashboard"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key)
        self.cache = {}
        self.metrics = defaultdict(list)

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get comprehensive dashboard summary"""
        try:
            # Get all fine-tuning jobs
            jobs = self.client.fine_tuning.jobs.list(limit=100)

            # Categorize jobs by status
            status_counts = defaultdict(int)
            active_jobs = []
            completed_jobs = []
            failed_jobs = []

            for job in jobs.data:
                status_counts[job.status] += 1

                job_info = {
                    "id": job.id,
                    "status": job.status,
                    "model": job.model,
                    "created_at": job.created_at,
                    "finished_at": job.finished_at,
                    "fine_tuned_model": job.fine_tuned_model
                }

                if job.status in ["validating_files", "queued", "running"]:
                    active_jobs.append(job_info)
                elif job.status == "succeeded":
                    completed_jobs.append(job_info)
                elif job.status in ["failed", "cancelled"]:
                    failed_jobs.append(job_info)

            # Calculate statistics
            total_jobs = len(jobs.data)
            success_rate = (status_counts["succeeded"] / total_jobs * 100) if total_jobs > 0 else 0

            # Get recent models
            recent_models = []
            for job in completed_jobs[:5]:
                if job["fine_tuned_model"]:
                    recent_models.append({
                        "model_id": job["fine_tuned_model"],
                        "created": job["finished_at"],
                        "base_model": job["model"]
                    })

            return {
                "summary": {
                    "total_jobs": total_jobs,
                    "active_jobs": len(active_jobs),
                    "completed_jobs": len(completed_jobs),
                    "failed_jobs": len(failed_jobs),
                    "success_rate": round(success_rate, 2)
                },
                "status_breakdown": dict(status_counts),
                "active_jobs": active_jobs[:10],
                "recent_completions": completed_jobs[:5],
                "recent_failures": failed_jobs[:5],
                "available_models": recent_models,
                "last_updated": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Dashboard summary failed: {str(e)}")
            return {"error": str(e)}

    def get_job_details(self, job_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific job"""
        try:
            job = self.client.fine_tuning.jobs.retrieve(job_id)

            # Get training events
            events = self.client.fine_tuning.jobs.list_events(
                fine_tuning_job_id=job_id,
                limit=50
            )

            # Calculate progress estimation
            progress = self._estimate_progress(job.status, job.created_at)

            # Get training file details if available
            file_details = None
            if hasattr(job, 'training_file'):
                try:
                    file_info = self.client.files.retrieve(job.training_file)
                    file_details = {
                        "id": file_info.id,
                        "bytes": file_info.bytes,
                        "created": file_info.created_at,
                        "filename": file_info.filename
                    }
                except:
                    pass

            return {
                "job_id": job.id,
                "status": job.status,
                "model": job.model,
                "created_at": job.created_at,
                "finished_at": job.finished_at,
                "fine_tuned_model": job.fine_tuned_model,
                "hyperparameters": job.hyperparameters.__dict__ if job.hyperparameters else {},
                "training_file": file_details,
                "error": job.error.__dict__ if job.error else None,
                "progress_estimate": progress,
                "events": [
                    {
                        "message": event.message,
                        "created_at": event.created_at,
                        "level": event.level
                    }
                    for event in events.data
                ],
                "estimated_completion": self._estimate_completion_time(job)
            }

        except Exception as e:
            logger.error(f"Job details failed for {job_id}: {str(e)}")
            return {"error": str(e)}

    def _estimate_progress(self, status: str, created_at: int) -> Dict[str, Any]:
        """Estimate training progress based on status and time"""
        status_progress = {
            "validating_files": 10,
            "queued": 20,
            "running": 50,
            "succeeded": 100,
            "failed": 0,
            "cancelled": 0
        }

        progress_percent = status_progress.get(status, 0)

        # Estimate based on time if running
        if status == "running":
            elapsed = datetime.now().timestamp() - created_at
            # Assume average 2 hours for completion
            estimated_percent = min(95, 20 + (elapsed / 7200) * 75)
            progress_percent = max(progress_percent, estimated_percent)

        return {
            "percent": round(progress_percent, 1),
            "status": status,
            "description": self._get_status_description(status)
        }

    def _get_status_description(self, status: str) -> str:
        """Get human-readable status description"""
        descriptions = {
            "validating_files": "Validating training data format and content",
            "queued": "Job queued for processing",
            "running": "Training in progress - this may take 1-3 hours",
            "succeeded": "Training completed successfully",
            "failed": "Training failed - check error details",
            "cancelled": "Training was cancelled"
        }
        return descriptions.get(status, "Unknown status")

    def _estimate_completion_time(self, job) -> Optional[str]:
        """Estimate when training will complete"""
        if job.status in ["succeeded", "failed", "cancelled"]:
            return None

        if job.status == "validating_files":
            # Usually takes a few minutes
            estimated = datetime.fromtimestamp(job.created_at) + timedelta(hours=2)
        elif job.status == "queued":
            # Add queue time estimate
            estimated = datetime.fromtimestamp(job.created_at) + timedelta(hours=2.5)
        elif job.status == "running":
            # Typical training time
            elapsed = datetime.now().timestamp() - job.created_at
            remaining = max(0, 7200 - elapsed)  # 2 hours typical
            estimated = datetime.now() + timedelta(seconds=remaining)
        else:
            return None

        return estimated.isoformat()

    def get_training_metrics(self) -> Dict[str, Any]:
        """Get training metrics and analytics"""
        try:
            jobs = self.client.fine_tuning.jobs.list(limit=100)

            # Calculate metrics
            metrics = {
                "total_training_jobs": len(jobs.data),
                "total_models_created": 0,
                "average_training_time": 0,
                "cost_estimate": 0,
                "monthly_stats": defaultdict(lambda: {"count": 0, "success": 0, "failed": 0})
            }

            training_times = []

            for job in jobs.data:
                # Count successful models
                if job.fine_tuned_model:
                    metrics["total_models_created"] += 1

                # Calculate training times
                if job.finished_at and job.created_at:
                    training_time = job.finished_at - job.created_at
                    training_times.append(training_time)

                # Monthly breakdown
                month = datetime.fromtimestamp(job.created_at).strftime("%Y-%m")
                metrics["monthly_stats"][month]["count"] += 1

                if job.status == "succeeded":
                    metrics["monthly_stats"][month]["success"] += 1
                elif job.status == "failed":
                    metrics["monthly_stats"][month]["failed"] += 1

                # Estimate costs (rough approximation)
                if job.status == "succeeded":
                    # Approximate cost: $0.008 per 1K tokens, assume 100K tokens average
                    metrics["cost_estimate"] += 0.8

            # Calculate average training time
            if training_times:
                avg_time = sum(training_times) / len(training_times)
                metrics["average_training_time"] = str(timedelta(seconds=avg_time))

            # Convert monthly stats to list
            metrics["monthly_stats"] = [
                {"month": month, **stats}
                for month, stats in sorted(metrics["monthly_stats"].items())
            ]

            return metrics

        except Exception as e:
            logger.error(f"Metrics calculation failed: {str(e)}")
            return {"error": str(e)}

    def compare_models(self, model_ids: List[str], test_prompt: str) -> Dict[str, Any]:
        """Compare multiple models on the same prompt"""
        results = {}

        for model_id in model_ids:
            try:
                response = self.client.chat.completions.create(
                    model=model_id,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert form parser. Extract structured data from documents."
                        },
                        {
                            "role": "user",
                            "content": test_prompt
                        }
                    ],
                    temperature=0,
                    max_tokens=2000
                )

                results[model_id] = {
                    "success": True,
                    "response": response.choices[0].message.content,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    },
                    "response_time": response.response_ms if hasattr(response, 'response_ms') else None
                }

            except Exception as e:
                results[model_id] = {
                    "success": False,
                    "error": str(e)
                }

        return {
            "comparison": results,
            "models_tested": len(model_ids),
            "test_prompt": test_prompt[:200] + "..." if len(test_prompt) > 200 else test_prompt
        }

    def get_model_performance(self, model_id: str) -> Dict[str, Any]:
        """Get performance statistics for a specific model"""
        # In a real implementation, this would track actual usage
        # For now, return mock data structure
        return {
            "model_id": model_id,
            "total_requests": 0,
            "average_response_time": 0,
            "average_tokens_used": 0,
            "success_rate": 0,
            "last_used": None,
            "performance_trend": [],
            "common_errors": []
        }

    def export_training_report(self) -> Dict[str, Any]:
        """Generate comprehensive training report"""
        dashboard = self.get_dashboard_summary()
        metrics = self.get_training_metrics()

        return {
            "report_generated": datetime.now().isoformat(),
            "executive_summary": {
                "total_models": metrics.get("total_models_created", 0),
                "success_rate": dashboard["summary"].get("success_rate", 0),
                "estimated_cost": metrics.get("cost_estimate", 0),
                "active_trainings": dashboard["summary"].get("active_jobs", 0)
            },
            "dashboard": dashboard,
            "metrics": metrics,
            "recommendations": self._generate_recommendations(dashboard, metrics)
        }

    def _generate_recommendations(self, dashboard: Dict, metrics: Dict) -> List[str]:
        """Generate recommendations based on current state"""
        recommendations = []

        # Check success rate
        if dashboard["summary"]["success_rate"] < 80:
            recommendations.append("Success rate is below 80%. Review failed jobs for common issues.")

        # Check active jobs
        if dashboard["summary"]["active_jobs"] > 5:
            recommendations.append("Multiple training jobs active. Monitor for resource constraints.")

        # Check for recent failures
        if dashboard["summary"]["failed_jobs"] > 2:
            recommendations.append("Multiple failed jobs detected. Check training data quality.")

        # Cost optimization
        if metrics.get("cost_estimate", 0) > 10:
            recommendations.append("Consider using GPT-3.5-turbo for cost optimization.")

        if not recommendations:
            recommendations.append("All systems operating normally. Continue monitoring.")

        return recommendations