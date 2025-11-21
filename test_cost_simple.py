#!/usr/bin/env python3
"""
Simple test script to verify cost calculation logic
"""

import pandas as pd
import re

def enhanced_fallback_estimation(df, region='us-east-2'):
    """Enhanced fallback cost estimation with better accuracy"""
    processed_df = df.copy()
    
    # Enhanced AWS pricing with regional variations
    region_multipliers = {
        'us-east-1': 1.0, 'us-east-2': 1.0, 'us-west-1': 1.1, 
        'us-west-2': 1.05, 'eu-west-1': 1.15, 'ap-southeast-1': 1.2
    }
    
    multiplier = region_multipliers.get(region, 1.0)
    
    # Updated pricing based on current AWS rates
    pricing = {
        'ec2': {
            't3.nano': 3.80, 't3.micro': 7.59, 't3.small': 15.18, 
            't3.medium': 30.37, 't3.large': 60.74, 't3.xlarge': 121.47,
            'm6i.large': 69.12, 'm6i.xlarge': 138.24, 'm6i.2xlarge': 276.48,
            'c6i.large': 61.56, 'c6i.xlarge': 123.12, 'c6i.2xlarge': 246.24,
            'r6g.large': 96.48, 'r6g.xlarge': 192.96
        },
        'ebs': {
            'gp3': 0.08, 'gp2': 0.10, 'io2': 0.125, 'st1': 0.045, 'sc1': 0.025
        },
        'rds': {
            'db.t3.micro': 14.60, 'db.t3.small': 29.20, 'db.t3.medium': 58.40,
            'db.t3.large': 116.80, 'db.r6g.large': 172.80, 'db.r6g.xlarge': 345.60
        },
        's3': {
            'standard': 0.023, 'ia': 0.0125, 'glacier': 0.004, 'deep_archive': 0.00099
        }
    }
    
    cost_estimations = []
    optimization_suggestions = []
    confidence_levels = []
    
    for index, row in processed_df.iterrows():
        resource_type = str(row['Resource Type']).lower()
        quantity_size = str(row['Quantity / Size'])
        duration = str(row['Duration (if temporary)']).lower()
        
        print(f"\nProcessing: {resource_type} - {quantity_size}")
        
        # Parse duration
        duration_months = 1
        if 'month' in duration:
            duration_match = re.search(r'(\d+)', duration)
            if duration_match:
                duration_months = int(duration_match.group(1))
        
        monthly_cost = 0
        optimization = []
        confidence = 0.8
        
        # Enhanced cost calculation with better parsing
        if 'compute' in resource_type or 'ec2' in resource_type:
            # Multiple parsing patterns for different formats
            patterns = [
                r'(\d+)\s*instances?\s*\(([^)]+)\)',  # "12 instances (m6i.large)"
                r'(\d+)\s*x\s*([^\s,]+)',            # "1 x db.r6g.large" 
                r'(\d+)\s*([a-z0-9]+\.[a-z0-9]+)',   # "2 m6i.large"
                r'(\d+)\s*(?:instances?|x)?\s*\(?([^)]*(?:t3|m6i|c6i|r6g|t2|m5|c5|r5)[^)]*)\)?',  # General pattern
                r'(\d+)',  # Just a number, assume 1 instance of default type
            ]
            
            count = 1
            instance_type = 'm6i.large'  # Default
            
            for pattern in patterns:
                match = re.search(pattern, quantity_size, re.IGNORECASE)
                if match:
                    count = int(match.group(1))
                    if len(match.groups()) > 1 and match.group(2):
                        instance_type = match.group(2).strip().lower()
                    break
            
            # Clean up instance type and handle common variations
            instance_type = re.sub(r'[^\w\.]', '', instance_type)
            
            # Handle common instance type variations
            if not instance_type or instance_type.isdigit():
                instance_type = 'm6i.large'  # Default if no type found
            
            # Map common variations
            instance_mapping = {
                'db.r6g.large': 'm6i.large',  # If DB instance type is used for EC2
                'db.t3.medium': 't3.medium',
                'db.t3.small': 't3.small'
            }
            
            if instance_type.startswith('db.'):
                instance_type = instance_mapping.get(instance_type, instance_type.replace('db.', ''))
            
            # Get unit cost with fallback
            unit_cost = pricing['ec2'].get(instance_type, pricing['ec2']['m6i.large'])
            monthly_cost = count * unit_cost * multiplier
            
            # Ensure we have a valid cost
            if monthly_cost <= 0:
                monthly_cost = count * pricing['ec2']['m6i.large'] * multiplier
            
            # Add optimization suggestions
            if duration_months >= 12:
                optimization.append("Reserved Instances (30% savings)")
                confidence = 0.95
            if count > 1:
                optimization.append("Consider Spot Instances (70% savings)")
            optimization.append("Right-sizing analysis recommended")
            
            print(f"  EC2: '{quantity_size}' → {count} x '{instance_type}' = ${monthly_cost:.2f}/month (unit: ${unit_cost:.2f})")
                    
        elif 'storage' in resource_type or 'ebs' in resource_type or 'efs' in resource_type or 's3' in resource_type:
            size_match = re.search(r'(\d+)\s*(?:TB|GB)', quantity_size)
            if size_match:
                size_value = int(size_match.group(1))
                # Convert TB to GB if needed
                if 'TB' in quantity_size.upper():
                    size_gb = size_value * 1024
                else:
                    size_gb = size_value
                
                # EFS pricing is higher than S3
                if 'efs' in quantity_size.lower():
                    monthly_cost = size_gb * 0.30 * multiplier  # EFS Standard pricing
                else:
                    storage_type = 'gp3'  # Default to GP3
                    if 'gp2' in quantity_size.lower():
                        storage_type = 'gp2'
                    elif 'io2' in quantity_size.lower():
                        storage_type = 'io2'
                    monthly_cost = size_gb * pricing['ebs'].get(storage_type, 0.08) * multiplier
                
                optimization.append("Consider GP3 for better price-performance")
                if size_gb > 100:
                    optimization.append("Lifecycle policies for cost optimization")
                confidence = 0.9
                
                print(f"  Storage: {size_gb}GB = ${monthly_cost:.2f}/month")
                
        elif 'database' in resource_type or 'rds' in resource_type:
            # Multiple patterns for database parsing
            db_patterns = [
                r'(\d+)\s*instances?\s*\(([^)]+)\)',  # "1 instances (db.r6g.large)"
                r'(\d+)\s*x\s*([^\s,]+)',            # "1 x db.r6g.large"
                r'(\d+)\s*([a-z0-9]+\.[a-z0-9]+)',   # "1 db.r6g.large"
            ]
            
            count = 1
            db_type = 'db.t3.small'  # Default
            
            for pattern in db_patterns:
                db_match = re.search(pattern, quantity_size, re.IGNORECASE)
                if db_match:
                    count = int(db_match.group(1))
                    db_type = db_match.group(2).strip().lower()
                    break
            
            # Clean up db type
            db_type = re.sub(r'[^\w\.]', '', db_type)
            if not db_type.startswith('db.'):
                db_type = 'db.' + db_type
            
            unit_cost = pricing['rds'].get(db_type, pricing['rds']['db.t3.small'])
            monthly_cost = count * unit_cost * multiplier
            
            if duration_months >= 12:
                optimization.append("RDS Reserved Instances (40% savings)")
                confidence = 0.95
            optimization.append("Multi-AZ consideration for production")
            
            print(f"  RDS: '{quantity_size}' → {count} x '{db_type}' = ${monthly_cost:.2f}/month (unit: ${unit_cost:.2f})")
            
        elif 'networking' in resource_type or 'load' in resource_type or 'nlb' in resource_type or 'alb' in resource_type:
            # Load balancer pricing
            nlb_count = len(re.findall(r'(\d+)\s*nlb', quantity_size, re.IGNORECASE))
            alb_count = len(re.findall(r'(\d+)\s*alb', quantity_size, re.IGNORECASE))
            
            if nlb_count == 0 and alb_count == 0:
                # Try to parse general load balancer count
                lb_match = re.search(r'(\d+)', quantity_size)
                if lb_match:
                    alb_count = int(lb_match.group(1))  # Default to ALB
            
            # ALB: ~$16/month, NLB: ~$16/month base + data processing
            monthly_cost = (alb_count * 16.43 + nlb_count * 16.43) * multiplier
            
            optimization.append("Consider consolidating load balancers")
            optimization.append("Review target group configurations")
            confidence = 0.85
            
            print(f"  Load Balancers: {alb_count} ALB + {nlb_count} NLB = ${monthly_cost:.2f}/month")
            
        elif 'container' in resource_type or 'cluster' in resource_type or 'ecs' in resource_type or 'eks' in resource_type:
            cluster_match = re.search(r'(\d+)\s*cluster', quantity_size)
            if cluster_match:
                cluster_count = int(cluster_match.group(1))
                # EKS control plane: $73/month per cluster, ECS: free (pay for EC2)
                if 'eks' in resource_type.lower():
                    monthly_cost = cluster_count * 73.0 * multiplier
                else:
                    monthly_cost = cluster_count * 20.0 * multiplier  # Estimated ECS costs
                
                optimization.append("Consider Fargate for serverless containers")
                optimization.append("Right-size worker nodes")
                confidence = 0.80
                
                print(f"  Containers: {cluster_count} clusters = ${monthly_cost:.2f}/month")
                
        elif 'lambda' in resource_type or 'function' in resource_type or 'serverless' in resource_type:
            func_match = re.search(r'(\d+)\s*function', quantity_size)
            if func_match:
                func_count = int(func_match.group(1))
                # Lambda: $0.20 per 1M requests + compute time
                monthly_cost = func_count * 5.0 * multiplier  # Estimated $5/function/month
                
                optimization.append("Optimize memory allocation")
                optimization.append("Consider provisioned concurrency")
                confidence = 0.75
                
                print(f"  Lambda: {func_count} functions = ${monthly_cost:.2f}/month")
                
        elif 'other' in resource_type or 'cloudfront' in resource_type or 'route53' in resource_type or 'ses' in resource_type:
            # Mixed services - estimate based on description
            services = quantity_size.lower()
            monthly_cost = 0
            
            if 'cloudfront' in services:
                monthly_cost += 10.0  # CloudFront base cost
            if 'route53' in services:
                monthly_cost += 0.50  # Route53 hosted zone
            if 'ses' in services:
                monthly_cost += 5.0   # SES estimated cost
            
            if monthly_cost == 0:
                monthly_cost = 15.0  # Default for other services
                
            monthly_cost *= multiplier
            
            optimization.append("Review service usage patterns")
            optimization.append("Consider service consolidation")
            confidence = 0.70
            
            print(f"  Other Services: ${monthly_cost:.2f}/month")
        
        # Ensure we have a valid monthly cost (fallback to minimum cost)
        if monthly_cost <= 0:
            monthly_cost = 10.0  # Minimum $10/month for any resource
            optimization.append("Cost estimation needs review")
            confidence = 0.5
        
        # Format cost estimation
        if duration_months > 1 and 'permanent' not in duration:
            total_cost = monthly_cost * duration_months
            cost_estimation = f"${monthly_cost:.2f}/month (${total_cost:.2f} total for {duration_months} months)"
        else:
            cost_estimation = f"${monthly_cost:.2f}/month"
        
        cost_estimations.append(cost_estimation)
        optimization_suggestions.append('; '.join(optimization[:2]) if optimization else 'No specific recommendations')
        confidence_levels.append(f"{confidence*100:.0f}%")
    
    # Force overwrite the Cost Estimation column even if it exists
    if 'Cost Estimation' in processed_df.columns:
        processed_df.drop('Cost Estimation', axis=1, inplace=True)
    processed_df['Cost Estimation'] = cost_estimations
    
    # Add optimization columns
    processed_df['Optimization Suggestions'] = optimization_suggestions
    processed_df['Confidence Level'] = confidence_levels
    
    return processed_df

def test_cost_calculation():
    """Test the cost calculation with sample data"""
    
    # Create test data similar to what's shown in the screenshot
    test_data = {
        'Resource Type': [
            'Compute (EC2)',
            'Database (RDS / Aurora)',
            'Storage (S3 / EFS / FSx)',
            'Networking (NLB / Load Balancer)',
            'Containers (ECS / EKS)',
            'Lambda / Serverless',
            'Other Services'
        ],
        'Quantity / Size': [
            '12 instances (m6i.large)',
            '1 x db.r6g.large',
            '10 TB x 1 TB EFS',
            '2 NLBs, 1 ALB',
            '2 clusters',
            '5 functions',
            'CloudFront, Route53, SES'
        ],
        'Description or Use Case': [
            'Application servers for API backend',
            'Main PostgreSQL DB',
            'Object & file storage',
            'For microservices orchestration',
            'For microservices orchestration',
            'Image processing, event triggers',
            'CDN, DNS, Email services'
        ],
        'Duration (if temporary)': [
            '3 months',
            '2 months',
            '4 months',
            '2 months',
            '2 months',
            '2 months',
            '2 months'
        ],
        'Cost Estimation': [
            '$0.00/month',
            '$0.00/month',
            '$0.00/month',
            '$0.00/month',
            '$0.00/month',
            '$0.00/month',
            '$0.00/month'
        ]
    }
    
    df = pd.DataFrame(test_data)
    print("Original DataFrame:")
    print(df)
    print("\n" + "="*80 + "\n")
    
    # Test the enhanced fallback estimation
    try:
        processed_df = enhanced_fallback_estimation(df, 'us-east-2')
        
        print("\n" + "="*80)
        print("FINAL RESULTS:")
        print("="*80)
        print(processed_df[['Resource Type', 'Quantity / Size', 'Cost Estimation', 'Optimization Suggestions']])
        
        # Calculate total cost
        total_cost = 0
        for cost_str in processed_df['Cost Estimation']:
            try:
                # Extract monthly cost from string like "$123.45/month"
                cost_match = re.search(r'\$(\d+\.?\d*)/month', str(cost_str))
                if cost_match:
                    total_cost += float(cost_match.group(1))
            except:
                pass
        
        print(f"\nTotal Monthly Cost: ${total_cost:.2f}")
        
        return processed_df
        
    except Exception as e:
        print(f"Error during cost calculation: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_cost_calculation()