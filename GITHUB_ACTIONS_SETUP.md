# GitHub Actions Setup for EC2 Deployment

## 🔐 Required GitHub Secrets

You need to add these secrets to your GitHub repository at:
`https://github.com/sanjeevtripurari/Vismaya-DemandOps/settings/secrets/actions`

### AWS Credentials
You'll need to get fresh AWS credentials from the correct account. 

**To get credentials for account 559928724862:**
1. Go to: https://superopsglobalhackathon.awsapps.com/start/#/console?account_id=559928724862&role_name=AdministratorAccess
2. Click on "Command line or programmatic access"
3. Copy the temporary credentials and add them as GitHub secrets:

**Example format (get current credentials from SSO):**
```
AWS_ACCESS_KEY_ID = [Your current access key from SSO]
AWS_SECRET_ACCESS_KEY = [Your current secret key from SSO]
AWS_SESSION_TOKEN = [Your current session token from SSO]
```

**Note**: These credentials expire, so you'll need to update them periodically.

### Application Configuration
```
BEDROCK_MODEL_ID = us.anthropic.claude-3-haiku-20240307-v1:0
DEFAULT_BUDGET = 80
BUDGET_WARNING_LIMIT = 80
BUDGET_MAXIMUM_LIMIT = 100
```

### AWS SSO Configuration
```
SSO_START_URL = https://superopsglobalhackathon.awsapps.com/start/#
SSO_ACCOUNT_ID = 559928724862
SSO_ROLE_NAME = AdministratorAccess
AWS_USER_EMAIL = sanjeevtripurari@gmail.com
```

## 🚀 How to Add Secrets

1. Go to your GitHub repository
2. Click on **Settings** tab
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Add each secret with the exact name and value shown above

## 📋 Prerequisites for GitHub Actions

### 1. EC2 Instance Setup
Your EC2 instance must have:
- **Tag**: `Name = vismaya-demandops`
- **SSM Agent** installed and running (comes pre-installed on Amazon Linux 2)
- **IAM Role** attached with these policies:
  - `AmazonSSMManagedInstanceCore`
  - `AmazonS3ReadOnlyAccess`
  - Your custom Bedrock and Cost Explorer policies

### 2. IAM Role for EC2 Instance

Create an IAM role with these policies:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::vismaya-deployments-*",
        "arn:aws:s3:::vismaya-deployments-*/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "ce:GetCostAndUsage",
        "ce:GetUsageReport",
        "ce:GetReservationCoverage",
        "ce:GetReservationUtilization"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:ListFoundationModels"
      ],
      "Resource": "*"
    }
  ]
}
```

### 3. Security Group Configuration
Ensure your EC2 security group allows:
- **Port 8503** (inbound from 0.0.0.0/0) - for application access
- **Port 22** (inbound from your IP) - for SSH access

## 🔄 Deployment Workflow

The GitHub Actions workflow will:

1. **Trigger** on push to `v2-dev` branch
2. **Package** your application with production configuration
3. **Upload** deployment package to S3
4. **Deploy** to your tagged EC2 instance using SSM
5. **Verify** deployment health
6. **Cleanup** temporary resources

## 🎯 Manual Deployment Trigger

You can also trigger deployment manually:

1. Go to **Actions** tab in your GitHub repository
2. Select **Deploy to EC2** workflow
3. Click **Run workflow**
4. Choose environment (production/staging)
5. Click **Run workflow**

## 🔍 Monitoring Deployment

1. **GitHub Actions**: Monitor progress in the Actions tab
2. **EC2 Console**: Check SSM Run Command history
3. **Application Logs**: SSH to instance and run `docker-compose logs -f`

## 🚨 Troubleshooting

### Common Issues:

1. **No EC2 instance found**
   - Ensure instance is running and tagged with `Name=vismaya-demandops`

2. **SSM command fails**
   - Check if SSM agent is running: `sudo systemctl status amazon-ssm-agent`
   - Verify IAM role has `AmazonSSMManagedInstanceCore` policy

3. **S3 access denied**
   - Ensure EC2 IAM role has S3 read permissions
   - Check if deployment bucket exists

4. **Application health check fails**
   - Check security group allows port 8503
   - Verify application is running: `docker-compose ps`
   - Check logs: `docker-compose logs`

### Debug Commands:

```bash
# On EC2 instance
sudo systemctl status amazon-ssm-agent
docker-compose ps
docker-compose logs
curl http://localhost:8503/_stcore/health
```

## 🔄 Updating Secrets

When AWS credentials expire, update these secrets:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY` 
- `AWS_SESSION_TOKEN`

The workflow will automatically use the updated credentials on the next deployment.

## 🎉 Success!

Once setup is complete, every push to the `v2-dev` branch will automatically deploy your application to EC2!

Your application will be available at: `http://your-ec2-public-ip:8503`