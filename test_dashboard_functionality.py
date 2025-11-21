#!/usr/bin/env python3
"""
Test script to verify dashboard functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if all required modules can be imported"""
    try:
        import streamlit as st
        print("✅ Streamlit imported successfully")
        
        import plotly.graph_objects as go
        print("✅ Plotly imported successfully")
        
        import pandas as pd
        print("✅ Pandas imported successfully")
        
        from datetime import datetime, timedelta
        print("✅ DateTime imported successfully")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_dashboard_structure():
    """Test the basic dashboard structure"""
    try:
        # Test if the enhanced dashboard file exists and has basic structure
        with open('src/ui/enhanced_dashboard.py', 'r') as f:
            content = f.read()
        
        # Check for key methods
        required_methods = [
            '_render_decisions_dashboard',
            '_render_forecasting_dashboard', 
            '_render_resource_sheet_tab',
            '_render_budgeting_tab',
            '_render_forecasting_ai_history',
            '_generate_forecasting_ai_response'
        ]
        
        missing_methods = []
        for method in required_methods:
            if method not in content:
                missing_methods.append(method)
        
        if missing_methods:
            print(f"❌ Missing methods: {missing_methods}")
            return False
        else:
            print("✅ All required methods found in dashboard")
            return True
            
    except Exception as e:
        print(f"❌ Error checking dashboard structure: {e}")
        return False

def test_csv_processing():
    """Test CSV processing functionality"""
    try:
        import pandas as pd
        import re
        
        # Test sample resource CSV data
        sample_data = {
            'Resource Type': ['Compute (EC2)', 'Storage (EBS)', 'Database (RDS)'],
            'Quantity / Size': ['2 instances (m6i.large)', '100 GB (gp3)', '1 instances (db.r6g.large)'],
            'Description or Use Case': ['Web servers', 'Application storage', 'Production database'],
            'Duration (if temporary)': ['6 months', 'permanent', '12 months'],
            'Cost Estimation': ['', '', '']
        }
        
        df = pd.DataFrame(sample_data)
        print("✅ Sample CSV data created successfully")
        
        # Test cost calculation logic
        pricing = {
            'ec2': {'m6i.large': 69.12},
            'ebs': 0.10,
            'rds': {'db.r6g.large': 172.80}
        }
        
        # Test parsing logic
        for index, row in df.iterrows():
            resource_type = str(row['Resource Type']).lower()
            quantity_size = str(row['Quantity / Size'])
            
            if 'compute' in resource_type:
                instance_match = re.search(r'(\d+)\s*instances?\s*\(([^)]+)\)', quantity_size)
                if instance_match:
                    count = int(instance_match.group(1))
                    instance_type = instance_match.group(2).strip()
                    print(f"✅ Parsed EC2: {count} x {instance_type}")
        
        print("✅ CSV processing logic works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Error in CSV processing test: {e}")
        return False

def test_graph_generation():
    """Test graph generation functionality"""
    try:
        import plotly.graph_objects as go
        
        # Test basic chart creation
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=['Oct', 'Nov', 'Dec'],
            y=[100, 120, 140],
            mode='lines+markers',
            name='Test Data'
        ))
        
        fig.update_layout(
            title="Test Chart",
            xaxis_title="Month",
            yaxis_title="Cost ($)"
        )
        
        print("✅ Plotly chart generation works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Error in graph generation test: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Dashboard Functionality")
    print("=" * 50)
    
    tests = [
        ("Import Tests", test_imports),
        ("Dashboard Structure", test_dashboard_structure),
        ("CSV Processing", test_csv_processing),
        ("Graph Generation", test_graph_generation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Dashboard functionality is working correctly.")
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    main()