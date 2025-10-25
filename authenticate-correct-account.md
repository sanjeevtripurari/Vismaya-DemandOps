# AWS Authentication for Correct Account

## 🔐 Account Information
- **Account ID**: 559928724862
- **SSO URL**: https://superopsglobalhackathon.awsapps.com/start/#/console?account_id=559928724862&role_name=AdministratorAccess
- **Role**: AdministratorAccess
- **User**: sanjeevtripurari@gmail.com

## 🚀 Quick Authentication Steps

### Step 1: Access AWS Console
Click this link: https://superopsglobalhackathon.awsapps.com/start/#/console?account_id=559928724862&role_name=AdministratorAccess

### Step 2: Get CLI Credentials
1. In the AWS Console, click on your user name (top right)
2. Click "Command line or programmatic access"
3. Copy the credentials for your preferred method

### Step 3: Configure AWS CLI
Choose one of these methods:

**Option A: Environment Variables (Temporary)**
```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_SESSION_TOKEN="your-session-token"
export AWS_DEFAULT_REGION="us-east-2"
```

**Option B: AWS CLI Profile**
```bash
aws configure set aws_access_key_id "your-access-key" --profile vismaya
aws configure set aws_secret_access_key "your-secret-key" --profile vismaya
aws configure set aws_session_token "your-session-token" --profile vismaya
aws configure set region us-east-2 --profile vismaya

# Use the profile
export AWS_PROFILE=vismaya
```

### Step 4: Verify Authentication
```bash
aws sts get-caller-identity
```

You should see:
```json
{
    "UserId": "AROABC123...:sanjeevtripurari@gmail.com",
    "Account": "559928724862",
    "Arn": "arn:aws:sts::559928724862:assumed-role/AWSReservedSSO_AdministratorAccess_.../sanjeevtripurari@gmail.com"
}
```

### Step 5: Deploy
Once authenticated, you can run:
```bash
# Check setup
./setup-correct-account.sh

# Deploy using CloudFormation
./deploy.sh

# Or follow manual deployment steps
```

## 🔄 Credential Refresh
SSO credentials expire after a few hours. When they expire:
1. Go back to the SSO URL
2. Get new credentials
3. Update your environment variables or profile
4. Continue deployment

## 🎯 Ready to Deploy!
Once authenticated with account 559928724862, all deployment scripts will work correctly.