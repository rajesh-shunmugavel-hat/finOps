import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from openai import OpenAI
from sqlalchemy.orm import Session
from src.config import OPENAI_API_KEY
from src.models import Report, ReportStatus, AwsCost, Metric
import logging

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            if not OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY environment variable is not set. Please configure it to use AI reports.")
            self._client = OpenAI(api_key=OPENAI_API_KEY)
        return self._client
    
    def is_configured(self) -> bool:
        return OPENAI_API_KEY is not None and len(OPENAI_API_KEY) > 0
    
    def generate_cost_optimization_report(
        self, 
        db: Session,
        report_id: int,
        cost_data: List[Dict[str, Any]],
        metrics_data: List[Dict[str, Any]],
        scope: str = "all"
    ) -> Dict[str, Any]:
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            raise ValueError(f"Report {report_id} not found")
        
        report.status = ReportStatus.PROCESSING
        db.commit()
        
        try:
            prompt = self._build_analysis_prompt(cost_data, metrics_data, scope)
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert AWS FinOps consultant specializing in cloud cost optimization. 
Your task is to analyze AWS cost and usage data, compare it with CloudWatch metrics, and provide actionable recommendations.

For each analysis, you must:
1. Identify the AWS services and their usage patterns
2. Provide a detailed cost and metric breakdown
3. Compare metrics vs cost to determine if the cost is justified
4. If cost is justified, explain why based on utilization metrics
5. If cost is NOT justified, provide concrete steps to reduce cost
6. Suggest specific AWS services, features, or configurations for savings
7. Provide a final cost report with prioritized recommendations

Always structure your response as valid JSON with the following format:
{
    "summary": "Executive summary of findings",
    "total_cost_analyzed": 0.00,
    "potential_savings": 0.00,
    "savings_percentage": 0.00,
    "findings": [
        {
            "service": "Service Name",
            "current_cost": 0.00,
            "utilization_level": "low/medium/high",
            "cost_justified": true/false,
            "justification": "Explanation",
            "potential_savings": 0.00
        }
    ],
    "recommendations": [
        {
            "priority": "high/medium/low",
            "service": "Service Name",
            "action": "Specific action to take",
            "estimated_savings": 0.00,
            "implementation_effort": "low/medium/high",
            "description": "Detailed description of the recommendation",
            "aws_features": ["List of AWS features/services to use"]
        }
    ],
    "optimization_opportunities": [
        {
            "category": "rightsizing/reserved_instances/spot_instances/storage_optimization/etc",
            "description": "Description of the opportunity",
            "affected_services": ["List of services"],
            "estimated_impact": 0.00
        }
    ]
}"""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            ai_response = response.choices[0].message.content
            
            try:
                json_start = ai_response.find('{')
                json_end = ai_response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = ai_response[json_start:json_end]
                    parsed_response = json.loads(json_str)
                else:
                    parsed_response = {"raw_response": ai_response}
            except json.JSONDecodeError:
                parsed_response = {"raw_response": ai_response}
            
            report.status = ReportStatus.COMPLETED
            report.summary = parsed_response.get('summary', '')
            report.recommendations = parsed_response.get('recommendations', [])
            report.raw_ai_response = ai_response
            report.total_cost_analyzed = parsed_response.get('total_cost_analyzed', 0)
            report.potential_savings = parsed_response.get('potential_savings', 0)
            report.completed_at = datetime.now()
            db.commit()
            
            logger.info(f"Report {report_id} completed successfully")
            return parsed_response
            
        except Exception as e:
            logger.error(f"Error generating report {report_id}: {e}")
            report.status = ReportStatus.FAILED
            report.raw_ai_response = str(e)
            db.commit()
            raise
    
    def _build_analysis_prompt(
        self, 
        cost_data: List[Dict[str, Any]], 
        metrics_data: List[Dict[str, Any]],
        scope: str
    ) -> str:
        total_cost = sum(item.get('cost', 0) for item in cost_data)
        
        services_summary = {}
        for item in cost_data:
            service = item.get('service_name', 'Unknown')
            if service not in services_summary:
                services_summary[service] = {'cost': 0, 'resources': set()}
            services_summary[service]['cost'] += item.get('cost', 0)
            if item.get('resource_id'):
                services_summary[service]['resources'].add(item.get('resource_id'))
        
        metrics_summary = {}
        for item in metrics_data:
            service = item.get('service_name', 'Unknown')
            resource = item.get('resource_id', 'Unknown')
            metric_name = item.get('metric_name', 'Unknown')
            
            key = f"{service}:{resource}"
            if key not in metrics_summary:
                metrics_summary[key] = {}
            if metric_name not in metrics_summary[key]:
                metrics_summary[key][metric_name] = []
            metrics_summary[key][metric_name].append(item.get('value', 0))
        
        for key in metrics_summary:
            for metric in metrics_summary[key]:
                values = metrics_summary[key][metric]
                metrics_summary[key][metric] = {
                    'avg': sum(values) / len(values) if values else 0,
                    'max': max(values) if values else 0,
                    'min': min(values) if values else 0
                }
        
        prompt = f"""
Analyze the following AWS cost and usage data for scope: {scope}

## Cost Summary
- Total Cost: ${total_cost:.2f}
- Number of Services: {len(services_summary)}
- Analysis Period: Last 30 days

## Cost Breakdown by Service
"""
        
        for service, data in sorted(services_summary.items(), key=lambda x: x[1]['cost'], reverse=True):
            prompt += f"\n### {service}\n"
            prompt += f"- Total Cost: ${data['cost']:.2f}\n"
            prompt += f"- Resource Count: {len(data['resources'])}\n"
            prompt += f"- Percentage of Total: {(data['cost']/total_cost*100):.1f}%\n" if total_cost > 0 else ""
        
        prompt += "\n## CloudWatch Metrics Summary\n"
        
        for key, metrics in metrics_summary.items():
            service, resource = key.split(':', 1)
            prompt += f"\n### {service} - {resource}\n"
            for metric_name, stats in metrics.items():
                prompt += f"- {metric_name}: avg={stats['avg']:.2f}, max={stats['max']:.2f}, min={stats['min']:.2f}\n"
        
        prompt += """

## Analysis Request
Please analyze this data and provide:
1. Assessment of whether each service's cost is justified based on utilization
2. Specific recommendations for cost optimization
3. Estimated potential savings
4. Prioritized action items

Focus on identifying:
- Underutilized resources (low CPU, memory, or throughput)
- Oversized instances or storage
- Opportunities for Reserved Instances or Savings Plans
- Unused or orphaned resources
- Storage optimization opportunities
- Data transfer cost reduction strategies
"""
        
        return prompt

openai_service = OpenAIService()
