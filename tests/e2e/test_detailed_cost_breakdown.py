#!/usr/bin/env python3
"""
Detailed Cost Breakdown Test
Shows exactly where every cent of AWS spending goes
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import asyncio
from config import Config
from src.application.dependency_injection import DependencyContainer


def get_user_friendly_service_name(aws_service_name: str) -> str:
    """Convert AWS service names to user-friendly names"""
    friendly_names = {
        # Cost Explorer
        'AWS Cost Explorer': 'Cost Explorer API Calls',
        
        # Bedrock AI Services
        'Amazon Bedrock': 'Bedrock AI Assistant',
        'Claude 3 Haiku (Amazon Bedrock Edition)': 'Claude 3 Haiku AI Model',
        
        # Storage Services
        'Amazon Simple Storage Service': 'S3 Storage & Requests',
        'Amazon Elastic Block Store': 'EBS Storage Volumes',
        
        # Compute Services
        'Amazon Elastic Compute Cloud - Compute': 'EC2 Compute Instances',
        'AWS Lambda': 'Lambda Functions',
        
        # Database Services
        'Amazon Relational Database Service': 'RDS Databases',
        
        # Monitoring & Management
        'Amazon CloudWatch': 'CloudWatch Monitoring',
        'AWS CloudTrail': 'CloudTrail Audit Logs',
        'AWS Config': 'Config Compliance',
        
        # Security Services
        'AWS Key Management Service': 'KMS Encryption Keys',
        'AWS Secrets Manager': 'Secrets Manager',
        'AWS Identity and Access Management': 'IAM Identity Services',
        
        # Networking Services
        'Amazon Virtual Private Cloud': 'VPC Networking',
        'Amazon CloudFront': 'CloudFront CDN',
        'Amazon Route 53': 'Route 53 DNS',
        
        # Other Services
        'Amazon Location Service': 'Location Services',
        'AWS CloudShell': 'CloudShell Terminal',
        'Amazon Simple Notification Service': 'SNS Notifications',
        'Amazon Simple Queue Service': 'SQS Message Queues',
        'AWS Glue': 'Glue Data Processing',
        'AWS Support (Business)': 'Business Support Plan',
        'AWS Support (Developer)': 'Developer Support Plan',
        'Tax': 'AWS Taxes & Fees'
    }
    
    return friendly_names.get(aws_service_name, aws_service_name)


async def detailed_cost_breakdown():
    """Show detailed breakdown of all AWS costs"""
    print("💰 Detailed AWS Cost Breakdown")
    print("=" * 60)
    
    # Initialize container
    config = Config()
    container = DependencyContainer(config)
    cost_provider = container.get('cost_provider')
    
    # Get total costs
    current_costs = await cost_provider.get_current_costs()
    print(f"📊 Total AWS Spend: ${current_costs.amount:.6f}")
    print()
    
    # Get detailed service costs
    service_costs = await cost_provider.get_service_costs()
    print(f"🔍 Service Breakdown ({len(service_costs)} services):")
    print("-" * 60)
    
    total_from_services = 0
    service_details = {}
    
    for service_cost in service_costs:
        service_name = service_cost.service_type.value
        amount = service_cost.cost.amount
        
        # Group by service type
        if service_name not in service_details:
            service_details[service_name] = []
        
        # Get the actual AWS service name or use a user-friendly name
        actual_service_name = getattr(service_cost.cost, 'service_name', None)
        if actual_service_name:
            display_name = get_user_friendly_service_name(actual_service_name)
        else:
            display_name = service_name
        
        # Get additional cost details
        pre_tax = getattr(service_cost.cost, 'pre_tax_amount', None)
        tax = getattr(service_cost.cost, 'tax_amount', None)
        usage = getattr(service_cost.cost, 'usage_quantity', None)
        
        service_details[service_name].append({
            'amount': amount,
            'actual_name': display_name,
            'pre_tax_amount': pre_tax,
            'tax_amount': tax,
            'usage_quantity': usage
        })
        
        total_from_services += amount
    
    # Sort by cost (highest first)
    sorted_services = sorted(service_details.items(), 
                           key=lambda x: sum(s['amount'] for s in x[1]), 
                           reverse=True)
    
    for service_type, services in sorted_services:
        total_service_cost = sum(s['amount'] for s in services)
        total_pre_tax = sum(s.get('pre_tax_amount', 0) or 0 for s in services)
        total_tax = sum(s.get('tax_amount', 0) or 0 for s in services)
        
        if total_service_cost > 0:
            # Show main service cost
            print(f"💳 {service_type}: ${total_service_cost:.6f}")
            
            # Show tax breakdown if there's tax
            if total_tax > 0:
                print(f"   💰 Pre-tax: ${total_pre_tax:.6f} | 🏛️ Tax: ${total_tax:.6f}")
            
            # Show individual services with detailed information
            if len(services) > 1:
                for service in services:
                    if service['amount'] > 0:
                        service_line = f"   └─ {service['actual_name']}: ${service['amount']:.6f}"
                        
                        # Add usage info if available
                        if service.get('usage_quantity') and service['usage_quantity'] > 0:
                            usage = service['usage_quantity']
                            if usage >= 1:
                                service_line += f" ({usage:.0f} units)"
                            else:
                                service_line += f" ({usage:.3f} units)"
                        
                        # Add tax breakdown if significant
                        if service.get('tax_amount') and service['tax_amount'] > 0.001:
                            service_line += f" [Pre-tax: ${service['pre_tax_amount']:.6f}]"
                        
                        print(service_line)
            else:
                # Show single service with details
                service = services[0]
                friendly_name = service['actual_name']
                if friendly_name and friendly_name != service_type:
                    service_line = f"   └─ {friendly_name}: ${service['amount']:.6f}"
                    
                    # Add usage info if available
                    if service.get('usage_quantity') and service['usage_quantity'] > 0:
                        usage = service['usage_quantity']
                        if usage >= 1:
                            service_line += f" ({usage:.0f} units)"
                        else:
                            service_line += f" ({usage:.3f} units)"
                    
                    # Add tax breakdown if significant
                    if service.get('tax_amount') and service['tax_amount'] > 0.001:
                        service_line += f" [Pre-tax: ${service['pre_tax_amount']:.6f}]"
                    
                    print(service_line)
        else:
            # Show zero-cost services for completeness
            print(f"💸 {service_type}: ${total_service_cost:.6f} (free tier/micro-usage)")
    
    print("-" * 60)
    
    # Calculate totals including tax breakdown
    total_pre_tax_all = sum(getattr(sc.cost, 'pre_tax_amount', 0) or 0 for sc in service_costs)
    total_tax_all = sum(getattr(sc.cost, 'tax_amount', 0) or 0 for sc in service_costs)
    
    print(f"📈 Total from Services: ${total_from_services:.6f}")
    print(f"📊 Total from AWS: ${current_costs.amount:.6f}")
    
    # Show tax breakdown if available
    if total_tax_all > 0:
        print(f"💰 Pre-tax Total: ${total_pre_tax_all:.6f}")
        print(f"🏛️ Tax Total: ${total_tax_all:.6f}")
        tax_rate = (total_tax_all / total_pre_tax_all * 100) if total_pre_tax_all > 0 else 0
        print(f"📊 Effective Tax Rate: {tax_rate:.2f}%")
    
    # Calculate and explain any difference
    difference = current_costs.amount - total_from_services
    if abs(difference) > 0.000001:  # More than 0.0001 cents
        print(f"🔍 Difference: ${difference:.6f}")
        
        if difference > 0:
            print("   ℹ️  This difference could be due to:")
            print("      • Rounding in AWS Cost Explorer")
            print("      • Taxes or fees not itemized by service")
            print("      • Cross-service data transfer charges")
            print("      • Very small charges rounded to $0.00 in service breakdown")
        else:
            print("   ℹ️  Service breakdown total exceeds AWS total (rounding)")
    else:
        print("✅ Perfect match! All costs accounted for.")
    
    print()
    print("🎯 Cost Analysis:")
    
    # Identify the main cost drivers
    if total_from_services > 0:
        for service_type, services in sorted_services[:3]:  # Top 3 services
            total_service_cost = sum(s['amount'] for s in services)
            if total_service_cost > 0:
                percentage = (total_service_cost / current_costs.amount) * 100
                print(f"   • {service_type}: {percentage:.1f}% of total spend")
                
                # Show usage details for top services
                for service in services:
                    if service['amount'] > 0 and service.get('usage_quantity'):
                        usage = service['usage_quantity']
                        cost_per_unit = service['amount'] / usage if usage > 0 else 0
                        if cost_per_unit > 0:
                            print(f"     └─ {service['actual_name']}: ${cost_per_unit:.6f} per unit")
    
    # Show Bedrock usage specifically
    bedrock_services = [s for s in service_costs if 'bedrock' in s.service_type.value.lower()]
    if bedrock_services:
        bedrock_total = sum(s.cost.amount for s in bedrock_services)
        bedrock_usage = sum(getattr(s.cost, 'usage_quantity', 0) or 0 for s in bedrock_services)
        print(f"   • Bedrock AI Usage: ${bedrock_total:.6f}")
        if bedrock_usage > 0:
            print(f"     └─ Total AI requests/tokens: {bedrock_usage:.0f}")
    
    # Show tax impact if significant
    if total_tax_all > 0.01:  # More than 1 cent in tax
        print(f"   • Tax Impact: ${total_tax_all:.6f} ({(total_tax_all/current_costs.amount*100):.1f}% of total)")
    
    print()
    print("💡 Recommendations:")
    print("   • Cost Explorer API calls are your main expense ($0.01 each)")
    print("   • Bedrock usage is very cost-effective for AI features")
    print("   • Most AWS services are in free tier (CloudTrail, Lambda, etc.)")
    print("   • Consider caching Cost Explorer results to reduce API calls")
    
    if total_tax_all > 0:
        print(f"   • Tax rate is {(total_tax_all/total_pre_tax_all*100):.1f}% - factor this into budget planning")


if __name__ == "__main__":
    asyncio.run(detailed_cost_breakdown())