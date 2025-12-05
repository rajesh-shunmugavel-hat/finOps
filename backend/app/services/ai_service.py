import os
import json
from typing import List, Dict, Any
from openai import OpenAI
from sqlalchemy.orm import Session
from ..models.models import (
    Service, Resource, EC2Metric, RDSMetric, S3Metric, LambdaMetric,
    AIReport, Recommendation, Department
)

# the newest OpenAI model is "gpt-5" which was released August 7, 2025.
# do not change this unless explicitly requested by the user
OPENAI_MODEL = "gpt-5"

def get_openai_client():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)

def prepare_cost_data_for_analysis(db: Session) -> Dict[str, Any]:
    services = db.query(Service).all()
    resources = db.query(Resource).all()
    
    cost_data = {
        "total_spend": sum(s.monthly_cost for s in services),
        "services": []
    }
    
    for service in services:
        service_resources = [r for r in resources if r.service_id == service.id]
        service_data = {
            "name": service.name,
            "type": service.service_type,
            "monthly_cost": service.monthly_cost,
            "resources": []
        }
        
        for resource in service_resources:
            resource_data = {
                "name": resource.resource_name,
                "instance_type": resource.instance_type,
                "monthly_cost": resource.monthly_cost,
                "department": resource.department.name if resource.department else "Unknown",
                "metrics": {}
            }
            
            if service.name == "EC2":
                metrics = db.query(EC2Metric).filter(
                    EC2Metric.resource_id == resource.id
                ).order_by(EC2Metric.timestamp.desc()).first()
                if metrics:
                    resource_data["metrics"] = {
                        "cpu_utilization": metrics.cpu_utilization,
                        "memory_utilization": metrics.memory_utilization,
                        "network_in": metrics.network_in,
                        "network_out": metrics.network_out,
                        "disk_read_ops": metrics.disk_read_ops,
                        "disk_write_ops": metrics.disk_write_ops
                    }
            elif service.name == "RDS":
                metrics = db.query(RDSMetric).filter(
                    RDSMetric.resource_id == resource.id
                ).order_by(RDSMetric.timestamp.desc()).first()
                if metrics:
                    resource_data["metrics"] = {
                        "cpu_utilization": metrics.cpu_utilization,
                        "database_connections": metrics.database_connections,
                        "free_storage_space": metrics.free_storage_space,
                        "read_latency": metrics.read_latency,
                        "write_latency": metrics.write_latency,
                        "read_iops": metrics.read_iops,
                        "write_iops": metrics.write_iops
                    }
            elif service.name == "S3":
                metrics = db.query(S3Metric).filter(
                    S3Metric.resource_id == resource.id
                ).order_by(S3Metric.timestamp.desc()).first()
                if metrics:
                    resource_data["metrics"] = {
                        "bucket_size_bytes": metrics.bucket_size_bytes,
                        "number_of_objects": metrics.number_of_objects,
                        "all_requests": metrics.all_requests,
                        "get_requests": metrics.get_requests,
                        "put_requests": metrics.put_requests,
                        "bytes_downloaded": metrics.bytes_downloaded
                    }
            elif service.name == "Lambda":
                metrics = db.query(LambdaMetric).filter(
                    LambdaMetric.resource_id == resource.id
                ).order_by(LambdaMetric.timestamp.desc()).first()
                if metrics:
                    resource_data["metrics"] = {
                        "invocations": metrics.invocations,
                        "duration_avg": metrics.duration_avg,
                        "errors": metrics.errors,
                        "throttles": metrics.throttles,
                        "concurrent_executions": metrics.concurrent_executions
                    }
            
            service_data["resources"].append(resource_data)
        
        cost_data["services"].append(service_data)
    
    return cost_data

def generate_ai_analysis(db: Session) -> AIReport:
    client = get_openai_client()
    cost_data = prepare_cost_data_for_analysis(db)
    
    prompt = f"""You are a FinOps expert analyzing AWS cloud spending. Analyze the following cost and metrics data to identify optimization opportunities.

Cost and Metrics Data:
{json.dumps(cost_data, indent=2)}

For each service, evaluate if the spending is justified based on the CloudWatch metrics:
- For EC2: CPU < 10% is underutilized, 10-40% is partially utilized, >40% is well utilized
- For RDS: CPU < 20% is underutilized, connections < 5 means possibly oversized
- For S3: Low request counts with high storage suggest need for lifecycle policies
- For Lambda: Low invocations with provisioned concurrency suggest waste

Provide your analysis in the following JSON format:
{{
    "total_current_spend": <float>,
    "total_monthly_savings": <float>,
    "status": "Optimization Opportunities Found" or "Spending Well Optimized",
    "executive_summary": "<CTO-level summary with total savings potential, top opportunities, and recommended timeline>",
    "findings": [
        {{
            "service_name": "<EC2|RDS|S3|Lambda>",
            "resource_name": "<specific resource name if applicable>",
            "finding_title": "<concise title>",
            "justification_status": "JUSTIFIED|NOT_JUSTIFIED|PARTIALLY_JUSTIFIED",
            "issue_description": "<detailed issue description with specific metrics>",
            "recommendation_text": "<specific, actionable recommendation with AWS features/alternatives>",
            "estimated_monthly_savings": <float>,
            "roi_percentage": <float>,
            "implementation_effort_hours": <float>,
            "department_name": "<affected department>"
        }}
    ]
}}

Be specific with recommendations - include exact instance types to migrate to, specific S3 storage classes, etc.
Calculate realistic ROI percentages based on savings vs current spend.
"""

    if client:
        try:
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a FinOps expert specializing in AWS cost optimization. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                max_completion_tokens=4096
            )
            
            analysis = json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"OpenAI API error: {e}")
            analysis = generate_mock_analysis(cost_data)
    else:
        analysis = generate_mock_analysis(cost_data)
    
    report = AIReport(
        total_current_spend=analysis.get("total_current_spend", cost_data["total_spend"]),
        total_monthly_savings=analysis.get("total_monthly_savings", 0),
        optimization_count=len(analysis.get("findings", [])),
        status=analysis.get("status", "Optimization Opportunities Found"),
        executive_summary=analysis.get("executive_summary", "")
    )
    db.add(report)
    db.flush()
    
    for finding in analysis.get("findings", []):
        recommendation = Recommendation(
            report_id=report.id,
            service_name=finding.get("service_name", ""),
            resource_name=finding.get("resource_name", ""),
            finding_title=finding.get("finding_title", ""),
            justification_status=finding.get("justification_status", ""),
            issue_description=finding.get("issue_description", ""),
            recommendation_text=finding.get("recommendation_text", ""),
            estimated_monthly_savings=finding.get("estimated_monthly_savings", 0),
            roi_percentage=finding.get("roi_percentage", 0),
            implementation_effort_hours=finding.get("implementation_effort_hours", 0),
            department_name=finding.get("department_name", "")
        )
        db.add(recommendation)
    
    db.commit()
    db.refresh(report)
    
    return report

def generate_mock_analysis(cost_data: Dict[str, Any]) -> Dict[str, Any]:
    findings = []
    total_savings = 0
    
    for service in cost_data.get("services", []):
        if service["name"] == "EC2":
            for resource in service.get("resources", []):
                metrics = resource.get("metrics", {})
                cpu = metrics.get("cpu_utilization", 50)
                
                if cpu < 10:
                    savings = resource["monthly_cost"] * 0.6
                    total_savings += savings
                    findings.append({
                        "service_name": "EC2",
                        "resource_name": resource["name"],
                        "finding_title": f"Underutilized EC2 Instance: {resource['name']}",
                        "justification_status": "NOT_JUSTIFIED",
                        "issue_description": f"Instance {resource['name']} ({resource['instance_type']}) is running with only {cpu:.1f}% average CPU utilization. Memory utilization is also low at {metrics.get('memory_utilization', 0):.1f}%.",
                        "recommendation_text": f"Downsize from {resource['instance_type']} to a smaller instance type (e.g., t3.micro or t3.small). Alternatively, implement Auto Scaling to match capacity with demand. Consider using Spot Instances for non-critical workloads.",
                        "estimated_monthly_savings": round(savings, 2),
                        "roi_percentage": round((savings / resource["monthly_cost"]) * 100, 1) if resource["monthly_cost"] > 0 else 0,
                        "implementation_effort_hours": 2,
                        "department_name": resource.get("department", "Unknown")
                    })
                elif cpu < 40:
                    savings = resource["monthly_cost"] * 0.3
                    total_savings += savings
                    findings.append({
                        "service_name": "EC2",
                        "resource_name": resource["name"],
                        "finding_title": f"Partially Utilized EC2 Instance: {resource['name']}",
                        "justification_status": "PARTIALLY_JUSTIFIED",
                        "issue_description": f"Instance {resource['name']} is running at {cpu:.1f}% CPU utilization, which indicates some room for optimization.",
                        "recommendation_text": f"Consider right-sizing to a smaller instance type or implementing Auto Scaling during off-peak hours.",
                        "estimated_monthly_savings": round(savings, 2),
                        "roi_percentage": round((savings / resource["monthly_cost"]) * 100, 1) if resource["monthly_cost"] > 0 else 0,
                        "implementation_effort_hours": 1.5,
                        "department_name": resource.get("department", "Unknown")
                    })
        
        elif service["name"] == "RDS":
            for resource in service.get("resources", []):
                metrics = resource.get("metrics", {})
                cpu = metrics.get("cpu_utilization", 50)
                connections = metrics.get("database_connections", 10)
                
                if cpu < 20 and connections < 5:
                    savings = resource["monthly_cost"] * 0.4
                    total_savings += savings
                    findings.append({
                        "service_name": "RDS",
                        "resource_name": resource["name"],
                        "finding_title": f"Oversized RDS Instance: {resource['name']}",
                        "justification_status": "NOT_JUSTIFIED",
                        "issue_description": f"RDS instance {resource['name']} has low CPU utilization ({cpu:.1f}%) and only {connections} active connections.",
                        "recommendation_text": f"Consider downsizing to a smaller instance class. If Multi-AZ is enabled and not required, switching to Single-AZ can reduce costs by 50%.",
                        "estimated_monthly_savings": round(savings, 2),
                        "roi_percentage": round((savings / resource["monthly_cost"]) * 100, 1) if resource["monthly_cost"] > 0 else 0,
                        "implementation_effort_hours": 3,
                        "department_name": resource.get("department", "Unknown")
                    })
                elif cpu > 60:
                    findings.append({
                        "service_name": "RDS",
                        "resource_name": resource["name"],
                        "finding_title": f"Well Utilized RDS Instance: {resource['name']}",
                        "justification_status": "JUSTIFIED",
                        "issue_description": f"RDS instance is running at {cpu:.1f}% CPU with {connections} connections, indicating appropriate sizing.",
                        "recommendation_text": "No changes recommended. Consider enabling Performance Insights for detailed monitoring.",
                        "estimated_monthly_savings": 0,
                        "roi_percentage": 0,
                        "implementation_effort_hours": 0,
                        "department_name": resource.get("department", "Unknown")
                    })
        
        elif service["name"] == "S3":
            for resource in service.get("resources", []):
                metrics = resource.get("metrics", {})
                requests = metrics.get("all_requests", 0)
                size_gb = metrics.get("bucket_size_bytes", 0) / (1024**3)
                
                if size_gb > 100 and requests < 1000:
                    savings = resource["monthly_cost"] * 0.5
                    total_savings += savings
                    findings.append({
                        "service_name": "S3",
                        "resource_name": resource["name"],
                        "finding_title": f"Infrequently Accessed S3 Bucket: {resource['name']}",
                        "justification_status": "PARTIALLY_JUSTIFIED",
                        "issue_description": f"Bucket {resource['name']} contains {size_gb:.1f}GB of data with only {requests} requests/month, suggesting infrequent access patterns.",
                        "recommendation_text": "Enable S3 Intelligent-Tiering to automatically move data between access tiers. For data accessed less than once per month, consider transitioning to S3 Glacier or Glacier Deep Archive.",
                        "estimated_monthly_savings": round(savings, 2),
                        "roi_percentage": round((savings / resource["monthly_cost"]) * 100, 1) if resource["monthly_cost"] > 0 else 0,
                        "implementation_effort_hours": 1,
                        "department_name": resource.get("department", "Unknown")
                    })
        
        elif service["name"] == "Lambda":
            for resource in service.get("resources", []):
                metrics = resource.get("metrics", {})
                invocations = metrics.get("invocations", 0)
                errors = metrics.get("errors", 0)
                
                if invocations < 100:
                    savings = resource["monthly_cost"] * 0.7
                    total_savings += savings
                    findings.append({
                        "service_name": "Lambda",
                        "resource_name": resource["name"],
                        "finding_title": f"Low Usage Lambda Function: {resource['name']}",
                        "justification_status": "NOT_JUSTIFIED",
                        "issue_description": f"Lambda function {resource['name']} has only {invocations} invocations/month with {errors} errors.",
                        "recommendation_text": "Review if this function is still needed. Consider consolidating with other functions or removing provisioned concurrency if enabled.",
                        "estimated_monthly_savings": round(savings, 2),
                        "roi_percentage": round((savings / resource["monthly_cost"]) * 100, 1) if resource["monthly_cost"] > 0 else 0,
                        "implementation_effort_hours": 0.5,
                        "department_name": resource.get("department", "Unknown")
                    })
    
    savings_percentage = (total_savings / cost_data["total_spend"] * 100) if cost_data["total_spend"] > 0 else 0
    
    return {
        "total_current_spend": cost_data["total_spend"],
        "total_monthly_savings": round(total_savings, 2),
        "status": "Optimization Opportunities Found" if total_savings > 0 else "Spending Well Optimized",
        "executive_summary": f"Total identified savings: ${total_savings:,.2f}/month ({savings_percentage:.1f}% reduction). "
                           f"Found {len([f for f in findings if f['justification_status'] != 'JUSTIFIED'])} optimization opportunities across {len(cost_data['services'])} AWS services. "
                           f"Highest ROI opportunities: EC2 right-sizing and S3 tiering. Recommended implementation timeline: 2 weeks.",
        "findings": findings
    }
