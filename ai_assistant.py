import json
import boto3
from config import Config
import logging

logger = logging.getLogger(__name__)

class AIAssistant:
    def __init__(self):
        self.session = self._create_session()
        try:
            self.bedrock = self.session.client('bedrock-runtime')
            self.model_id = Config.BEDROCK_MODEL_ID
            logger.info("AI Assistant initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing AI Assistant: {e}")
            self.bedrock = None
    
    def _create_session(self):
        """Create AWS session with appropriate authentication method"""
        try:
            if Config.use_sso():
                return boto3.Session(
                    profile_name=Config.AWS_PROFILE,
                    region_name=Config.AWS_REGION
                )
            else:
                return boto3.Session(
                    aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
                    aws_session_token=Config.AWS_SESSION_TOKEN,
                    region_name=Config.AWS_REGION
                )
        except Exception as e:
            logger.warning(f"Error creating AWS session: {e}. Using default session.")
            return boto3.Session(region_name=Config.AWS_REGION)
    
    def analyze_costs(self, current_spend, budget, forecast, service_costs):
        """Analyze costs and provide AI insights"""
        try:
            prompt = f"""
            You are Vismaya, an AI FinOps assistant. Analyze the following AWS cost data and provide insights:
            
            Current Spend: ${current_spend:,.2f}
            Monthly Budget: ${budget:,.2f}
            Forecasted Spend: ${forecast:,.2f}
            Budget Utilization: {(current_spend/budget)*100:.1f}%
            
            Service Costs:
            {json.dumps(service_costs, indent=2)}
            
            Provide a concise analysis including:
            1. Budget status and overspend risk
            2. Cost optimization suggestions
            3. Specific recommendations for high-cost services
            
            Keep response under 200 words and actionable.
            """
            
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 300,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
            
            response = self.bedrock.invoke_model(
                body=body,
                modelId=self.model_id,
                accept='application/json',
                contentType='application/json'
            )
            
            response_body = json.loads(response.get('body').read())
            return response_body['content'][0]['text']
            
        except Exception as e:
            logger.error(f"Error calling Bedrock: {e}")
            return self._get_mock_analysis(current_spend, budget, forecast)
    
    def chat_response(self, user_message, context_data):
        """Handle chat interactions with the AI assistant"""
        try:
            prompt = f"""
            You are Vismaya, an AI FinOps assistant for AWS cost management. 
            
            Current Context:
            {json.dumps(context_data, indent=2)}
            
            User Question: {user_message}
            
            Provide a helpful, specific response about AWS costs, optimization, or forecasting.
            Be conversational but professional. Keep responses under 150 words.
            """
            
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 250,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
            
            response = self.bedrock.invoke_model(
                body=body,
                modelId=self.model_id,
                accept='application/json',
                contentType='application/json'
            )
            
            response_body = json.loads(response.get('body').read())
            return response_body['content'][0]['text']
            
        except Exception as e:
            logger.error(f"Error in chat response: {e}")
            if self.bedrock is None:
                return "I'm having trouble connecting to AWS Bedrock. Please check your AWS credentials and permissions."
            return "I'm experiencing some technical difficulties. Please try again in a moment."
    
    def _get_mock_analysis(self, current_spend, budget, forecast):
        """Mock analysis for demo purposes"""
        budget_pct = (current_spend / budget) * 100
        overspend = forecast - budget
        
        if budget_pct > 80:
            return f"""You have spent ${current_spend:,.0f} of ${budget:,.0f} budget ({budget_pct:.0f}%).
            
At this rate, you'll overshoot by ${overspend:,.0f}.

Suggested:
Move 3 EC2 to Spot → Save $120.
Optimize RDS storage → Save $200.
Review unused EBS volumes → Save $150."""
        else:
            return f"""You're at {budget_pct:.0f}% of your ${budget:,.0f} budget. Good progress!

Recommendations:
- Monitor EC2 usage patterns
- Consider Reserved Instances for steady workloads
- Set up cost alerts at 90% budget"""