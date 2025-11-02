#!/usr/bin/env python3
"""
Test script to verify cost calculation logic
"""

import pandas as pd
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

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
        from ui.enhanced_dashboard import EnhancedDashboard
        
        dashboard = EnhancedDashboard()
        processed_df = dashboard._enhanced_fallback_estimation(df, 'us-east-2')
        
        print("Processed DataFrame with Cost Calculations:")
        print(processed_df[['Resource Type', 'Quantity / Size', 'Cost Estimation']])
        
        # Calculate total cost
        total_cost = 0
        for cost_str in processed_df['Cost Estimation']:
            try:
                # Extract monthly cost from string like "$123.45/month"
                import re
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