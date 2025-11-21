#!/usr/bin/env python3
"""
Vismaya DemandOps Application Benchmarking Suite
Comprehensive performance testing for dashboard components
"""

import time
import psutil
import sys
import os
import tracemalloc
from datetime import datetime
import pandas as pd
import json

class VismayaBenchmark:
    def __init__(self):
        self.results = {}
        self.start_time = None
        self.start_memory = None
        
    def start_benchmark(self, test_name):
        """Start benchmarking a specific test"""
        print(f"\n🔄 Starting benchmark: {test_name}")
        self.start_time = time.time()
        self.start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        tracemalloc.start()
        
    def end_benchmark(self, test_name):
        """End benchmarking and record results"""
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        duration = end_time - self.start_time
        memory_used = end_memory - self.start_memory
        peak_memory = peak / 1024 / 1024  # MB
        
        self.results[test_name] = {
            'duration_seconds': round(duration, 3),
            'memory_used_mb': round(memory_used, 2),
            'peak_memory_mb': round(peak_memory, 2),
            'status': 'success'
        }
        
        print(f"✅ {test_name}: {duration:.3f}s, Memory: {memory_used:.2f}MB")
        
    def benchmark_imports(self):
        """Benchmark application imports"""
        self.start_benchmark("Module Imports")
        
        try:
            # Core imports
            import streamlit as st
            import plotly.graph_objects as go
            import pandas as pd
            import numpy as np
            
            # Application imports
            from src.ui.enhanced_dashboard import EnhancedDashboard
            from src.services.tabular_data_service import TabularDataService
            from config import Config
            
        except Exception as e:
            self.results["Module Imports"] = {
                'duration_seconds': 0,
                'memory_used_mb': 0,
                'peak_memory_mb': 0,
                'status': f'error: {str(e)}'
            }
            print(f"❌ Import error: {e}")
            return False
            
        self.end_benchmark("Module Imports")
        return True
        
    def benchmark_config_loading(self):
        """Benchmark configuration loading"""
        self.start_benchmark("Config Loading")
        
        try:
            from config import Config
            
            # Test multiple config loads
            for i in range(10):
                config = Config.get_fresh_config()
                budget = config.DEFAULT_BUDGET
                warning = config.BUDGET_WARNING_LIMIT
                maximum = config.BUDGET_MAXIMUM_LIMIT
                
        except Exception as e:
            self.results["Config Loading"] = {
                'duration_seconds': 0,
                'memory_used_mb': 0,
                'peak_memory_mb': 0,
                'status': f'error: {str(e)}'
            }
            print(f"❌ Config loading error: {e}")
            return False
            
        self.end_benchmark("Config Loading")
        return True
        
    def benchmark_data_generation(self):
        """Benchmark data generation for charts"""
        self.start_benchmark("Data Generation")
        
        try:
            import random
            from datetime import datetime, timedelta
            
            # Simulate forecast data generation (similar to dashboard)
            services = ['EC2', 'EBS Storage', 'Cost Explorer', 'Bedrock', 'Compute', 'Data Science', 'S3 Storage']
            current_costs = [56.00, 1.60, 0.15, 0.30, 0.15, 0.01, 0.00]
            growth_rates = [0.08, 0.12, 0.02, 0.25, 0.15, 0.20, 0.30]
            
            # Generate 6 months of data
            forecast_data = []
            for i in range(6):
                monthly_total = 0
                for j, base_cost in enumerate(current_costs):
                    service_growth_rate = growth_rates[j]
                    growth_factor = (1 + service_growth_rate) ** i
                    
                    random.seed(i * j + 42)
                    variation = 1 + (random.random() - 0.5) * 0.04
                    
                    cost = base_cost * growth_factor * variation
                    monthly_total += cost
                    
                    forecast_data.append({
                        'month': i + 1,
                        'service': services[j],
                        'cost': cost,
                        'growth_factor': growth_factor
                    })
            
            # Convert to DataFrame
            df = pd.DataFrame(forecast_data)
            
        except Exception as e:
            self.results["Data Generation"] = {
                'duration_seconds': 0,
                'memory_used_mb': 0,
                'peak_memory_mb': 0,
                'status': f'error: {str(e)}'
            }
            print(f"❌ Data generation error: {e}")
            return False
            
        self.end_benchmark("Data Generation")
        return True
        
    def benchmark_chart_creation(self):
        """Benchmark chart creation"""
        self.start_benchmark("Chart Creation")
        
        try:
            import plotly.graph_objects as go
            from datetime import datetime
            
            # Create sample data
            months = ['Oct 2025', 'Nov 2025', 'Dec 2025', 'Jan 2026', 'Feb 2026', 'Mar 2026']
            costs = [58.21, 62.87, 67.90, 73.33, 79.20, 85.54]
            
            # Create multiple chart types
            for chart_type in ['bar', 'line', 'scatter']:
                fig = go.Figure()
                
                if chart_type == 'bar':
                    fig.add_trace(go.Bar(
                        x=months,
                        y=costs,
                        name='Monthly Cost',
                        marker_color='#FF6B6B'
                    ))
                elif chart_type == 'line':
                    fig.add_trace(go.Scatter(
                        x=months,
                        y=costs,
                        mode='lines+markers',
                        name='Cost Trend',
                        line=dict(color='#4A90E2', width=3)
                    ))
                elif chart_type == 'scatter':
                    fig.add_trace(go.Scatter(
                        x=months,
                        y=costs,
                        mode='markers',
                        name='Cost Points',
                        marker=dict(size=10, color='#4ECDC4')
                    ))
                
                fig.update_layout(
                    title=f"Test {chart_type.title()} Chart",
                    xaxis_title="Month",
                    yaxis_title="Cost ($)",
                    height=400
                )
                
        except Exception as e:
            self.results["Chart Creation"] = {
                'duration_seconds': 0,
                'memory_used_mb': 0,
                'peak_memory_mb': 0,
                'status': f'error: {str(e)}'
            }
            print(f"❌ Chart creation error: {e}")
            return False
            
        self.end_benchmark("Chart Creation")
        return True
        
    def benchmark_csv_processing(self):
        """Benchmark CSV processing"""
        self.start_benchmark("CSV Processing")
        
        try:
            # Create sample CSV data
            sample_data = {
                'Resource Type': ['EC2 Instance', 'EBS Volume', 'RDS Database'] * 100,
                'Resource Name': [f'Resource-{i}' for i in range(300)],
                'Monthly Cost': [50.0 + i * 0.1 for i in range(300)],
                'Duration (if temporary)': ['6 months'] * 300,
                'Priority': ['High', 'Medium', 'Low'] * 100
            }
            
            df = pd.DataFrame(sample_data)
            
            # Simulate CSV processing operations
            # Filter operations
            high_priority = df[df['Priority'] == 'High']
            
            # Aggregation operations
            cost_by_type = df.groupby('Resource Type')['Monthly Cost'].sum()
            
            # Sorting operations
            sorted_df = df.sort_values('Monthly Cost', ascending=False)
            
            # Statistical operations
            total_cost = df['Monthly Cost'].sum()
            avg_cost = df['Monthly Cost'].mean()
            max_cost = df['Monthly Cost'].max()
            
        except Exception as e:
            self.results["CSV Processing"] = {
                'duration_seconds': 0,
                'memory_used_mb': 0,
                'peak_memory_mb': 0,
                'status': f'error: {str(e)}'
            }
            print(f"❌ CSV processing error: {e}")
            return False
            
        self.end_benchmark("CSV Processing")
        return True
        
    def benchmark_database_operations(self):
        """Benchmark database operations"""
        self.start_benchmark("Database Operations")
        
        try:
            from src.services.tabular_data_service import TabularDataService
            
            # Initialize service
            tabular_service = TabularDataService()
            
            # Test database operations (if available)
            # Note: This will use SQLite, so it's safe to test
            try:
                current_df = tabular_service.get_current_usage_table(limit=50)
                forecast_df = tabular_service.get_forecasting_table(limit=50)
            except Exception as db_error:
                print(f"⚠️ Database operations limited: {db_error}")
                
        except Exception as e:
            self.results["Database Operations"] = {
                'duration_seconds': 0,
                'memory_used_mb': 0,
                'peak_memory_mb': 0,
                'status': f'error: {str(e)}'
            }
            print(f"❌ Database operations error: {e}")
            return False
            
        self.end_benchmark("Database Operations")
        return True
        
    def benchmark_memory_usage(self):
        """Benchmark memory usage patterns"""
        self.start_benchmark("Memory Usage Test")
        
        try:
            # Create large datasets to test memory handling
            large_data = []
            
            # Simulate dashboard data structures
            for i in range(1000):
                large_data.append({
                    'id': i,
                    'resource_type': f'EC2-{i}',
                    'cost': 50.0 + i * 0.1,
                    'timestamp': datetime.now(),
                    'metadata': {'tags': [f'tag-{j}' for j in range(10)]}
                })
            
            # Convert to DataFrame and perform operations
            df = pd.DataFrame(large_data)
            
            # Memory-intensive operations
            grouped = df.groupby('resource_type').agg({
                'cost': ['sum', 'mean', 'max', 'min'],
                'id': 'count'
            })
            
            # Clean up
            del large_data
            del df
            del grouped
            
        except Exception as e:
            self.results["Memory Usage Test"] = {
                'duration_seconds': 0,
                'memory_used_mb': 0,
                'peak_memory_mb': 0,
                'status': f'error: {str(e)}'
            }
            print(f"❌ Memory usage test error: {e}")
            return False
            
        self.end_benchmark("Memory Usage Test")
        return True
        
    def run_all_benchmarks(self):
        """Run all benchmark tests"""
        print("🚀 Starting Vismaya DemandOps Benchmarking Suite")
        print("=" * 60)
        
        # System information
        print(f"📊 System Information:")
        print(f"   Python Version: {sys.version.split()[0]}")
        print(f"   CPU Count: {psutil.cpu_count()}")
        print(f"   Total Memory: {psutil.virtual_memory().total / 1024 / 1024 / 1024:.1f} GB")
        print(f"   Available Memory: {psutil.virtual_memory().available / 1024 / 1024 / 1024:.1f} GB")
        
        # Run benchmarks
        benchmarks = [
            self.benchmark_imports,
            self.benchmark_config_loading,
            self.benchmark_data_generation,
            self.benchmark_chart_creation,
            self.benchmark_csv_processing,
            self.benchmark_database_operations,
            self.benchmark_memory_usage
        ]
        
        success_count = 0
        for benchmark in benchmarks:
            try:
                if benchmark():
                    success_count += 1
            except Exception as e:
                print(f"❌ Benchmark failed: {e}")
        
        print(f"\n📈 Benchmark Summary:")
        print(f"   Tests Run: {len(benchmarks)}")
        print(f"   Successful: {success_count}")
        print(f"   Failed: {len(benchmarks) - success_count}")
        
        return self.results
        
    def generate_report(self):
        """Generate detailed benchmark report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'system_info': {
                'python_version': sys.version.split()[0],
                'cpu_count': psutil.cpu_count(),
                'total_memory_gb': round(psutil.virtual_memory().total / 1024 / 1024 / 1024, 1),
                'available_memory_gb': round(psutil.virtual_memory().available / 1024 / 1024 / 1024, 1)
            },
            'benchmark_results': self.results,
            'summary': {
                'total_tests': len(self.results),
                'successful_tests': len([r for r in self.results.values() if r['status'] == 'success']),
                'total_duration': sum([r['duration_seconds'] for r in self.results.values() if isinstance(r['duration_seconds'], (int, float))]),
                'total_memory_used': sum([r['memory_used_mb'] for r in self.results.values() if isinstance(r['memory_used_mb'], (int, float))]),
                'peak_memory': max([r['peak_memory_mb'] for r in self.results.values() if isinstance(r['peak_memory_mb'], (int, float))], default=0)
            }
        }
        
        return report

def main():
    """Main benchmarking function"""
    benchmark = VismayaBenchmark()
    
    # Run all benchmarks
    results = benchmark.run_all_benchmarks()
    
    # Generate report
    report = benchmark.generate_report()
    
    # Save report to file
    report_filename = f"vismaya_benchmark_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: {report_filename}")
    
    # Display summary
    print(f"\n🎯 Performance Summary:")
    print(f"   Total Duration: {report['summary']['total_duration']:.3f} seconds")
    print(f"   Total Memory Used: {report['summary']['total_memory_used']:.2f} MB")
    print(f"   Peak Memory: {report['summary']['peak_memory']:.2f} MB")
    
    # Performance ratings
    total_time = report['summary']['total_duration']
    if total_time < 1.0:
        rating = "🟢 Excellent"
    elif total_time < 3.0:
        rating = "🟡 Good"
    elif total_time < 5.0:
        rating = "🟠 Fair"
    else:
        rating = "🔴 Needs Optimization"
    
    print(f"   Performance Rating: {rating}")
    
    return report

if __name__ == "__main__":
    main()