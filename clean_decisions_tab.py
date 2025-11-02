"""
Clean implementation of Decisions Tab with proper CSV upload requirements
"""

def _render_budgeting_tab(self):
    """Render budgeting tab with budget allocation and analysis - CSV upload required"""
    st.markdown("#### 💰 Budgeting - Resource Allocation Based on Budget")
    st.markdown("*Upload your project budget CSV to get optimal resource allocation recommendations*")
    
    # Budget CSV Upload Section
    st.markdown("##### 📤 Upload Budget Planning CSV")
    
    # Show expected budget CSV format
    with st.expander("📋 Expected Budget CSV Format", expanded=True):
        st.markdown("""
        **Required Columns:**
        - `Field`: Budget category or description
        - `Description`: Detailed description of the budget item  
        - `Example`: Example value or amount
        
        **Sample Structure:**
        ```csv
        Field,Description,Example
        Estimated Monthly Cost,Total AWS spend expected,8000
        Project Duration,Duration of the project in months,6
        Priority Services,Critical services that must be included,EC2 RDS
        Optional Services,Services that can be scaled down if needed,S3 Lambda
        ```
        
        **Important Notes:**
        - Use numeric values without currency symbols for costs
        - Separate multiple services with spaces
        - Duration should be in months as a number
        """)
    
    budget_file = st.file_uploader(
        "Choose Budget CSV file",
        type=['csv'],
        help="Upload a CSV file with your budget planning data",
        key="budget_upload"
    )
    
    if budget_file is None:
        st.info("👆 Please upload a budget CSV file to proceed with budget-based resource allocation.")
        st.warning("⚠️ No sample data provided. You must upload a properly structured budget CSV file to use this feature.")
        
        # Show what happens after upload
        with st.expander("🔍 What happens after you upload?", expanded=False):
            st.markdown("""
            **After uploading your budget CSV, you will get:**
            
            1. **📊 Budget Analysis**
               - Budget vs current usage comparison
               - Available budget calculation
               - Budget utilization metrics
            
            2. **🎯 Resource Allocation Recommendations**
               - Optimal resource mix within your budget
               - Priority-based allocation
               - Budget allocation breakdown charts
            
            3. **⚡ Optimization Opportunities**
               - Cost-saving recommendations if over budget
               - Reserved Instance suggestions
               - Right-sizing recommendations
            
            4. **✅ Approval Workflow**
               - Quick action buttons for approval
               - Team templates (FinOps, DevOps, CTO)
               - Budget compliance validation
            """)
        return
    
    try:
        import pandas as pd
        
        # Read budget CSV
        budget_df = pd.read_csv(budget_file)
        
        # Validate required columns
        required_columns = ['Field', 'Description', 'Example']
        missing_columns = [col for col in required_columns if col not in budget_df.columns]
        
        if missing_columns:
            st.error(f"❌ Missing required columns: {', '.join(missing_columns)}")
            st.info("Please ensure your CSV file has the columns: Field, Description, Example")
            return
        
        # Validate data content
        if len(budget_df) == 0:
            st.error("❌ CSV file is empty. Please provide budget data.")
            return
        
        # Display uploaded data
        st.success("✅ Budget CSV uploaded successfully!")
        st.markdown("##### 📊 Uploaded Budget Data")
        st.dataframe(budget_df, use_container_width=True)
        
        # Process budget data
        budget_analysis = self._process_budget_csv(budget_df)
        st.session_state.decision_budget_data = budget_analysis
        
        # Display budget analysis
        self._render_budget_analysis(budget_analysis)
        
        # Budget-based resource allocation
        self._render_budget_resource_allocation(budget_analysis)
        
        # Budget approval workflow
        self._render_budget_approval_workflow(budget_analysis)
        
    except Exception as e:
        st.error(f"❌ Error processing budget CSV file: {str(e)}")
        st.info("Please ensure your CSV file follows the expected format and contains valid data.")

def _render_resource_sheet_tab_clean(self):
    """Clean resource sheet tab implementation with mandatory CSV upload"""
    st.markdown("#### 📋 Resource Sheet - Cost Estimation & Analysis")
    st.markdown("*Upload your resource planning CSV to get cost estimations, comparisons, and optimization recommendations*")
    
    # CSV Upload Section
    st.markdown("##### 📤 Upload Resource Planning CSV")
    
    # Show expected CSV format
    with st.expander("📋 Expected CSV Format", expanded=True):
        st.markdown("""
        **Required Columns:**
        - `Resource Type`: Type of AWS resource (e.g., Compute (EC2), Storage (EBS), Database (RDS))
        - `Quantity / Size`: Number of instances or size specification
        - `Description or Use Case`: Purpose of the resource
        - `Duration (if temporary)`: Duration in months (leave empty for permanent)
        - `Cost Estimation`: Will be calculated automatically (leave empty)
        
        **Sample Structure:**
        ```csv
        Resource Type,Quantity / Size,Description or Use Case,Duration (if temporary),Cost Estimation
        Compute (EC2),2 instances (m6i.large),Application servers for API backend,6,
        Storage (EBS),100 GB (gp3),Database storage,,
        Database (RDS),1 instances (db.r6g.large),PostgreSQL production,12,
        ```
        
        **Important Notes:**
        - Use standard AWS instance types (t3.medium, m6i.large, db.r6g.large, etc.)
        - Specify quantities clearly (e.g., "2 instances", "100 GB")
        - Leave Cost Estimation column empty - it will be calculated automatically
        - Duration should be in months as a number, or leave empty for permanent resources
        """)
    
    uploaded_file = st.file_uploader(
        "Choose CSV file",
        type=['csv'],
        help="Upload a CSV file with your resource planning data"
    )
    
    if uploaded_file is None:
        st.info("👆 Please upload a CSV file to proceed with resource planning and cost estimation.")
        st.warning("⚠️ No sample data provided. You must upload a properly structured CSV file to use this feature.")
        
        # Show what happens after upload
        with st.expander("🔍 What happens after you upload?", expanded=False):
            st.markdown("""
            **After uploading your resource CSV, you will get:**
            
            1. **💰 Automatic Cost Calculation**
               - Real AWS pricing for all resource types
               - Monthly and total cost estimations
               - Updated CSV with calculated costs
            
            2. **📊 Interactive Analysis**
               - Current vs planned resource comparison
               - Cost impact visualization
               - 6-month trending analysis
            
            3. **⚡ Optimization Recommendations**
               - Reserved Instance savings opportunities
               - Spot Instance recommendations
               - Storage optimization suggestions
               - Right-sizing recommendations
            
            4. **✅ Approval Workflow**
               - Quick action buttons (Approve/Reject/Review)
               - Team templates for FinOps, DevOps, and CTO
               - Professional reports ready for stakeholders
            """)
        return
    
    try:
        # Read and process CSV
        import pandas as pd
        import io
        
        # Read CSV
        df = pd.read_csv(uploaded_file)
        
        # Validate required columns
        required_columns = ['Resource Type', 'Quantity / Size', 'Description or Use Case', 'Duration (if temporary)', 'Cost Estimation']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.error(f"❌ Missing required columns: {', '.join(missing_columns)}")
            st.info("Please ensure your CSV file has all required columns as shown in the format example.")
            return
        
        # Validate data content
        if len(df) == 0:
            st.error("❌ CSV file is empty. Please provide resource planning data.")
            return
        
        # Check for required data in key columns
        empty_resource_types = df['Resource Type'].isna().sum()
        empty_quantities = df['Quantity / Size'].isna().sum()
        
        if empty_resource_types > 0 or empty_quantities > 0:
            st.error("❌ Missing data in required columns. Please ensure Resource Type and Quantity/Size are filled for all rows.")
            return
        
        # Display uploaded data
        st.success("✅ Resource CSV uploaded successfully!")
        st.markdown("##### 📊 Uploaded Resource Data")
        st.dataframe(df, use_container_width=True)
        
        # Process and calculate costs
        processed_df = self._process_resource_csv(df)
        st.session_state.decision_resource_data = processed_df
        
        # Display processed data
        st.markdown("##### 💰 Processed Resource Data with Cost Estimations")
        st.dataframe(processed_df, use_container_width=True)
        
        # Download processed CSV
        csv_data = processed_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Updated CSV with Cost Estimations",
            data=csv_data,
            file_name=f"resource_plan_with_costs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        # Analysis and Graphs
        self._render_resource_analysis_graphs(processed_df)
        
        # Optimization Recommendations
        optimized_df = self._generate_optimization_recommendations(processed_df)
        
        # Approval Workflow
        self._render_resource_approval_workflow(processed_df, optimized_df)
        
    except Exception as e:
        st.error(f"❌ Error processing CSV file: {str(e)}")
        st.info("Please ensure your CSV file follows the expected format and contains valid data.")
        
        # Show common error solutions
        with st.expander("🔧 Common Issues and Solutions", expanded=False):
            st.markdown("""
            **Common CSV Issues:**
            
            1. **Encoding Problems**: Save your CSV as UTF-8 encoding
            2. **Column Names**: Ensure exact column names as shown in format
            3. **Data Format**: Use proper instance types (t3.medium, not T3-Medium)
            4. **Empty Cells**: Fill all required fields, leave Cost Estimation empty
            5. **Special Characters**: Avoid special characters in resource descriptions
            
            **Supported Resource Types:**
            - Compute (EC2): t3.micro, t3.small, t3.medium, t3.large, m6i.large, etc.
            - Storage (EBS): Specify size in GB (e.g., "100 GB", "500 GB")
            - Database (RDS): db.t3.micro, db.t3.small, db.r6g.large, etc.
            - S3 Storage: Specify size in GB
            """)