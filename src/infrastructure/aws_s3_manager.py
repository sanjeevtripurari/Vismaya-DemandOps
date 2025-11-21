"""
AWS S3 Manager for Agentic AI System
Manages S3 buckets for document and artifact storage
"""

import logging
import boto3
import json
import os
import tempfile
from typing import Dict, List, Optional, Any, BinaryIO
from datetime import datetime, timedelta
import uuid
from urllib.parse import urlparse
import mimetypes

from .aws_session_factory import AWSSessionFactory

logger = logging.getLogger(__name__)


class AWSS3Manager:
    """
    Manages S3 buckets for agentic AI system document and artifact storage
    Handles bucket creation, file operations, and lifecycle management
    """
    
    def __init__(self, aws_session_factory: AWSSessionFactory, config: Dict[str, Any]):
        self.session_factory = aws_session_factory
        self.config = config
        self.session = None
        self.s3_client = None
        self.s3_resource = None
        
        # S3 configuration
        self.bucket_prefix = config.get("bucket_prefix", "vismaya-agentic")
        self.region = config.get("aws_region", "us-east-1")
        self.encryption_type = config.get("encryption_type", "AES256")
        self.versioning_enabled = config.get("versioning_enabled", True)
        
        # Bucket definitions
        self.bucket_definitions = {
            "decision_artifacts": {
                "bucket_name": f"{self.bucket_prefix}-decision-artifacts",
                "purpose": "Store decision proposals, approval documents, and related artifacts",
                "lifecycle_rules": [
                    {
                        "id": "decision_artifacts_lifecycle",
                        "status": "Enabled",
                        "transitions": [
                            {"days": 30, "storage_class": "STANDARD_IA"},
                            {"days": 90, "storage_class": "GLACIER"},
                            {"days": 365, "storage_class": "DEEP_ARCHIVE"}
                        ]
                    }
                ]
            },
            "reports": {
                "bucket_name": f"{self.bucket_prefix}-reports",
                "purpose": "Store generated reports, analytics, and dashboards",
                "lifecycle_rules": [
                    {
                        "id": "reports_lifecycle",
                        "status": "Enabled",
                        "transitions": [
                            {"days": 7, "storage_class": "STANDARD_IA"},
                            {"days": 30, "storage_class": "GLACIER"}
                        ]
                    }
                ]
            },
            "audit_trails": {
                "bucket_name": f"{self.bucket_prefix}-audit-trails",
                "purpose": "Store audit logs, compliance documents, and system traces",
                "lifecycle_rules": [
                    {
                        "id": "audit_trails_lifecycle",
                        "status": "Enabled",
                        "transitions": [
                            {"days": 90, "storage_class": "STANDARD_IA"},
                            {"days": 365, "storage_class": "GLACIER"},
                            {"days": 2555, "storage_class": "DEEP_ARCHIVE"}  # 7 years
                        ]
                    }
                ]
            },
            "agent_artifacts": {
                "bucket_name": f"{self.bucket_prefix}-agent-artifacts",
                "purpose": "Store agent-generated content, models, and temporary files",
                "lifecycle_rules": [
                    {
                        "id": "agent_artifacts_lifecycle",
                        "status": "Enabled",
                        "transitions": [
                            {"days": 14, "storage_class": "STANDARD_IA"},
                            {"days": 60, "storage_class": "GLACIER"}
                        ],
                        "expiration": {"days": 180}  # Delete after 6 months
                    }
                ]
            },
            "backups": {
                "bucket_name": f"{self.bucket_prefix}-backups",
                "purpose": "Store system backups and recovery data",
                "lifecycle_rules": [
                    {
                        "id": "backups_lifecycle",
                        "status": "Enabled",
                        "transitions": [
                            {"days": 1, "storage_class": "STANDARD_IA"},
                            {"days": 30, "storage_class": "GLACIER"},
                            {"days": 90, "storage_class": "DEEP_ARCHIVE"}
                        ]
                    }
                ]
            }
        }
        
        self._initialize_clients()
    
    def _initialize_clients(self) -> None:
        """Initialize S3 clients"""
        try:
            self.session = self.session_factory.get_session()
            self.s3_client = self.session.client('s3')
            self.s3_resource = self.session.resource('s3')
            logger.info("S3 clients initialized")
        except Exception as e:
            logger.error(f"Failed to initialize S3 clients: {e}")
            raise
    
    async def create_all_buckets(self) -> Dict[str, bool]:
        """Create all required S3 buckets"""
        results = {}
        
        for bucket_key, bucket_def in self.bucket_definitions.items():
            try:
                success = await self._create_bucket(bucket_def)
                results[bucket_key] = success
                
                if success:
                    logger.info(f"Successfully created/verified bucket: {bucket_def['bucket_name']}")
                else:
                    logger.error(f"Failed to create bucket: {bucket_def['bucket_name']}")
                    
            except Exception as e:
                logger.error(f"Error creating bucket {bucket_key}: {e}")
                results[bucket_key] = False
        
        return results
    
    async def _create_bucket(self, bucket_def: Dict[str, Any]) -> bool:
        """Create individual S3 bucket"""
        try:
            bucket_name = bucket_def["bucket_name"]
            
            # Check if bucket already exists
            try:
                self.s3_client.head_bucket(Bucket=bucket_name)
                logger.info(f"Bucket {bucket_name} already exists")
                
                # Verify bucket configuration
                await self._verify_bucket_configuration(bucket_name, bucket_def)
                return True
                
            except self.s3_client.exceptions.NoSuchBucket:
                # Bucket doesn't exist, create it
                pass
            except Exception as e:
                logger.error(f"Error checking bucket {bucket_name}: {e}")
                return False
            
            # Create bucket
            create_params = {"Bucket": bucket_name}
            
            # Add location constraint if not in us-east-1
            if self.region != "us-east-1":
                create_params["CreateBucketConfiguration"] = {
                    "LocationConstraint": self.region
                }
            
            self.s3_client.create_bucket(**create_params)
            logger.info(f"Created bucket: {bucket_name}")
            
            # Configure bucket
            await self._configure_bucket(bucket_name, bucket_def)
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating bucket {bucket_def['bucket_name']}: {e}")
            return False
    
    async def _configure_bucket(self, bucket_name: str, bucket_def: Dict[str, Any]) -> None:
        """Configure S3 bucket with security and lifecycle settings"""
        try:
            # Enable versioning
            if self.versioning_enabled:
                self.s3_client.put_bucket_versioning(
                    Bucket=bucket_name,
                    VersioningConfiguration={"Status": "Enabled"}
                )
                logger.debug(f"Enabled versioning for {bucket_name}")
            
            # Configure server-side encryption
            encryption_config = {
                "Rules": [
                    {
                        "ApplyServerSideEncryptionByDefault": {
                            "SSEAlgorithm": self.encryption_type
                        },
                        "BucketKeyEnabled": True
                    }
                ]
            }
            
            self.s3_client.put_bucket_encryption(
                Bucket=bucket_name,
                ServerSideEncryptionConfiguration=encryption_config
            )
            logger.debug(f"Configured encryption for {bucket_name}")
            
            # Block public access
            self.s3_client.put_public_access_block(
                Bucket=bucket_name,
                PublicAccessBlockConfiguration={
                    "BlockPublicAcls": True,
                    "IgnorePublicAcls": True,
                    "BlockPublicPolicy": True,
                    "RestrictPublicBuckets": True
                }
            )
            logger.debug(f"Blocked public access for {bucket_name}")
            
            # Configure lifecycle rules
            if bucket_def.get("lifecycle_rules"):
                await self._configure_lifecycle_rules(bucket_name, bucket_def["lifecycle_rules"])
            
            # Add bucket tags
            await self._tag_bucket(bucket_name, bucket_def)
            
            # Configure CORS if needed
            await self._configure_cors(bucket_name)
            
        except Exception as e:
            logger.error(f"Error configuring bucket {bucket_name}: {e}")
            raise
    
    async def _configure_lifecycle_rules(self, bucket_name: str, lifecycle_rules: List[Dict[str, Any]]) -> None:
        """Configure S3 lifecycle rules"""
        try:
            rules = []
            
            for rule in lifecycle_rules:
                s3_rule = {
                    "ID": rule["id"],
                    "Status": rule["status"],
                    "Filter": {"Prefix": ""}
                }
                
                # Add transitions
                if rule.get("transitions"):
                    s3_rule["Transitions"] = []
                    for transition in rule["transitions"]:
                        s3_rule["Transitions"].append({
                            "Days": transition["days"],
                            "StorageClass": transition["storage_class"]
                        })
                
                # Add expiration
                if rule.get("expiration"):
                    s3_rule["Expiration"] = {"Days": rule["expiration"]["days"]}
                
                rules.append(s3_rule)
            
            self.s3_client.put_bucket_lifecycle_configuration(
                Bucket=bucket_name,
                LifecycleConfiguration={"Rules": rules}
            )
            
            logger.debug(f"Configured lifecycle rules for {bucket_name}")
            
        except Exception as e:
            logger.error(f"Error configuring lifecycle rules for {bucket_name}: {e}")
            raise
    
    async def _tag_bucket(self, bucket_name: str, bucket_def: Dict[str, Any]) -> None:
        """Add tags to S3 bucket"""
        try:
            tags = [
                {"Key": "Project", "Value": "Vismaya-DemandOps"},
                {"Key": "Component", "Value": "Agentic-AI"},
                {"Key": "Purpose", "Value": bucket_def.get("purpose", "General storage")},
                {"Key": "Environment", "Value": self.config.get("environment", "development")},
                {"Key": "CreatedBy", "Value": "AWSS3Manager"},
                {"Key": "CreatedAt", "Value": datetime.now().isoformat()}
            ]
            
            self.s3_client.put_bucket_tagging(
                Bucket=bucket_name,
                Tagging={"TagSet": tags}
            )
            
            logger.debug(f"Tagged bucket: {bucket_name}")
            
        except Exception as e:
            logger.warning(f"Could not tag bucket {bucket_name}: {e}")
    
    async def _configure_cors(self, bucket_name: str) -> None:
        """Configure CORS for bucket"""
        try:
            cors_configuration = {
                "CORSRules": [
                    {
                        "AllowedHeaders": ["*"],
                        "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
                        "AllowedOrigins": ["*"],
                        "ExposeHeaders": ["ETag"],
                        "MaxAgeSeconds": 3000
                    }
                ]
            }
            
            self.s3_client.put_bucket_cors(
                Bucket=bucket_name,
                CORSConfiguration=cors_configuration
            )
            
            logger.debug(f"Configured CORS for {bucket_name}")
            
        except Exception as e:
            logger.warning(f"Could not configure CORS for {bucket_name}: {e}")
    
    async def _verify_bucket_configuration(self, bucket_name: str, bucket_def: Dict[str, Any]) -> None:
        """Verify existing bucket configuration"""
        try:
            # Check versioning
            versioning = self.s3_client.get_bucket_versioning(Bucket=bucket_name)
            if versioning.get("Status") != "Enabled" and self.versioning_enabled:
                self.s3_client.put_bucket_versioning(
                    Bucket=bucket_name,
                    VersioningConfiguration={"Status": "Enabled"}
                )
            
            # Check encryption
            try:
                self.s3_client.get_bucket_encryption(Bucket=bucket_name)
            except self.s3_client.exceptions.ClientError as e:
                if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
                    # Configure encryption
                    encryption_config = {
                        "Rules": [
                            {
                                "ApplyServerSideEncryptionByDefault": {
                                    "SSEAlgorithm": self.encryption_type
                                },
                                "BucketKeyEnabled": True
                            }
                        ]
                    }
                    self.s3_client.put_bucket_encryption(
                        Bucket=bucket_name,
                        ServerSideEncryptionConfiguration=encryption_config
                    )
            
            logger.debug(f"Verified configuration for bucket: {bucket_name}")
            
        except Exception as e:
            logger.warning(f"Error verifying bucket configuration: {e}")
    
    async def upload_file(
        self, 
        bucket_type: str, 
        file_path: str, 
        content: bytes,
        metadata: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = None
    ) -> Optional[str]:
        """Upload file to S3 bucket"""
        try:
            if bucket_type not in self.bucket_definitions:
                raise ValueError(f"Unknown bucket type: {bucket_type}")
            
            bucket_name = self.bucket_definitions[bucket_type]["bucket_name"]
            
            # Generate unique key if not provided
            if not file_path.startswith("/"):
                file_path = f"/{file_path}"
            
            # Add timestamp prefix for organization
            timestamp_prefix = datetime.now().strftime("%Y/%m/%d")
            s3_key = f"{timestamp_prefix}{file_path}"
            
            # Determine content type
            if not content_type:
                content_type, _ = mimetypes.guess_type(file_path)
                if not content_type:
                    content_type = "application/octet-stream"
            
            # Prepare upload parameters
            upload_params = {
                "Bucket": bucket_name,
                "Key": s3_key,
                "Body": content,
                "ContentType": content_type,
                "ServerSideEncryption": self.encryption_type
            }
            
            # Add metadata
            if metadata:
                upload_params["Metadata"] = metadata
            
            # Upload file
            self.s3_client.put_object(**upload_params)
            
            # Generate S3 URL
            s3_url = f"s3://{bucket_name}/{s3_key}"
            
            logger.info(f"Uploaded file to S3: {s3_url}")
            return s3_url
            
        except Exception as e:
            logger.error(f"Error uploading file to S3: {e}")
            return None
    
    async def download_file(self, s3_url: str) -> Optional[bytes]:
        """Download file from S3"""
        try:
            # Parse S3 URL
            parsed = urlparse(s3_url)
            if parsed.scheme != "s3":
                raise ValueError(f"Invalid S3 URL: {s3_url}")
            
            bucket_name = parsed.netloc
            s3_key = parsed.path.lstrip("/")
            
            # Download file
            response = self.s3_client.get_object(Bucket=bucket_name, Key=s3_key)
            content = response["Body"].read()
            
            logger.debug(f"Downloaded file from S3: {s3_url}")
            return content
            
        except Exception as e:
            logger.error(f"Error downloading file from S3: {e}")
            return None
    
    async def delete_file(self, s3_url: str) -> bool:
        """Delete file from S3"""
        try:
            # Parse S3 URL
            parsed = urlparse(s3_url)
            if parsed.scheme != "s3":
                raise ValueError(f"Invalid S3 URL: {s3_url}")
            
            bucket_name = parsed.netloc
            s3_key = parsed.path.lstrip("/")
            
            # Delete file
            self.s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
            
            logger.info(f"Deleted file from S3: {s3_url}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file from S3: {e}")
            return False
    
    async def list_files(
        self, 
        bucket_type: str, 
        prefix: str = "", 
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """List files in S3 bucket"""
        try:
            if bucket_type not in self.bucket_definitions:
                raise ValueError(f"Unknown bucket type: {bucket_type}")
            
            bucket_name = self.bucket_definitions[bucket_type]["bucket_name"]
            
            # List objects
            response = self.s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix,
                MaxKeys=limit
            )
            
            files = []
            for obj in response.get("Contents", []):
                file_info = {
                    "key": obj["Key"],
                    "size": obj["Size"],
                    "last_modified": obj["LastModified"].isoformat(),
                    "etag": obj["ETag"].strip('"'),
                    "storage_class": obj.get("StorageClass", "STANDARD"),
                    "s3_url": f"s3://{bucket_name}/{obj['Key']}"
                }
                files.append(file_info)
            
            return files
            
        except Exception as e:
            logger.error(f"Error listing files in S3: {e}")
            return []
    
    async def generate_presigned_url(
        self, 
        s3_url: str, 
        expiration: int = 3600,
        http_method: str = "GET"
    ) -> Optional[str]:
        """Generate presigned URL for S3 object"""
        try:
            # Parse S3 URL
            parsed = urlparse(s3_url)
            if parsed.scheme != "s3":
                raise ValueError(f"Invalid S3 URL: {s3_url}")
            
            bucket_name = parsed.netloc
            s3_key = parsed.path.lstrip("/")
            
            # Generate presigned URL
            presigned_url = self.s3_client.generate_presigned_url(
                ClientMethod="get_object" if http_method == "GET" else "put_object",
                Params={"Bucket": bucket_name, "Key": s3_key},
                ExpiresIn=expiration
            )
            
            logger.debug(f"Generated presigned URL for {s3_url}")
            return presigned_url
            
        except Exception as e:
            logger.error(f"Error generating presigned URL: {e}")
            return None
    
    async def create_backup(self, data: Dict[str, Any], backup_name: str) -> Optional[str]:
        """Create system backup in S3"""
        try:
            # Serialize data
            backup_data = json.dumps(data, indent=2, default=str).encode('utf-8')
            
            # Create backup file path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"/system_backups/{backup_name}_{timestamp}.json"
            
            # Upload backup
            s3_url = await self.upload_file(
                bucket_type="backups",
                file_path=backup_path,
                content=backup_data,
                metadata={
                    "backup_name": backup_name,
                    "created_at": datetime.now().isoformat(),
                    "backup_type": "system_backup"
                },
                content_type="application/json"
            )
            
            if s3_url:
                logger.info(f"Created system backup: {backup_name}")
            
            return s3_url
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return None
    
    async def restore_backup(self, s3_url: str) -> Optional[Dict[str, Any]]:
        """Restore system backup from S3"""
        try:
            # Download backup
            backup_data = await self.download_file(s3_url)
            
            if not backup_data:
                return None
            
            # Parse backup data
            data = json.loads(backup_data.decode('utf-8'))
            
            logger.info(f"Restored backup from: {s3_url}")
            return data
            
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            return None
    
    async def get_bucket_metrics(self, hours: int = 24) -> Dict[str, Dict[str, Any]]:
        """Get CloudWatch metrics for S3 buckets"""
        try:
            cloudwatch = self.session.client('cloudwatch')
            end_time = datetime.now()
            start_time = datetime.now().replace(hour=end_time.hour - hours)
            
            metrics = {}
            
            for bucket_key, bucket_def in self.bucket_definitions.items():
                bucket_name = bucket_def["bucket_name"]
                
                try:
                    # Get bucket size
                    bucket_size = cloudwatch.get_metric_statistics(
                        Namespace='AWS/S3',
                        MetricName='BucketSizeBytes',
                        Dimensions=[
                            {'Name': 'BucketName', 'Value': bucket_name},
                            {'Name': 'StorageType', 'Value': 'StandardStorage'}
                        ],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=86400,  # Daily
                        Statistics=['Average']
                    )
                    
                    # Get number of objects
                    object_count = cloudwatch.get_metric_statistics(
                        Namespace='AWS/S3',
                        MetricName='NumberOfObjects',
                        Dimensions=[
                            {'Name': 'BucketName', 'Value': bucket_name},
                            {'Name': 'StorageType', 'Value': 'AllStorageTypes'}
                        ],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=86400,
                        Statistics=['Average']
                    )
                    
                    # Get requests
                    requests = cloudwatch.get_metric_statistics(
                        Namespace='AWS/S3',
                        MetricName='AllRequests',
                        Dimensions=[{'Name': 'BucketName', 'Value': bucket_name}],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=3600,
                        Statistics=['Sum']
                    )
                    
                    metrics[bucket_key] = {
                        "bucket_name": bucket_name,
                        "size_bytes": bucket_size['Datapoints'][-1]['Average'] if bucket_size['Datapoints'] else 0,
                        "object_count": int(object_count['Datapoints'][-1]['Average']) if object_count['Datapoints'] else 0,
                        "total_requests": sum(point['Sum'] for point in requests['Datapoints'])
                    }
                    
                except Exception as e:
                    logger.warning(f"Could not get metrics for {bucket_name}: {e}")
                    metrics[bucket_key] = {"error": str(e)}
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting bucket metrics: {e}")
            return {"error": str(e)}
    
    def get_bucket_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all configured buckets"""
        return {
            bucket_key: {
                "bucket_name": bucket_def["bucket_name"],
                "purpose": bucket_def["purpose"],
                "lifecycle_rules_count": len(bucket_def.get("lifecycle_rules", [])),
                "s3_url": f"s3://{bucket_def['bucket_name']}"
            }
            for bucket_key, bucket_def in self.bucket_definitions.items()
        }


class S3DocumentManager:
    """
    High-level document management interface for S3
    Provides simplified methods for common document operations
    """
    
    def __init__(self, s3_manager: AWSS3Manager):
        self.s3_manager = s3_manager
    
    async def store_decision_artifact(
        self, 
        proposal_id: str, 
        artifact_type: str,
        content: bytes,
        filename: str
    ) -> Optional[str]:
        """Store decision-related artifact"""
        file_path = f"/decisions/{proposal_id}/{artifact_type}/{filename}"
        
        return await self.s3_manager.upload_file(
            bucket_type="decision_artifacts",
            file_path=file_path,
            content=content,
            metadata={
                "proposal_id": proposal_id,
                "artifact_type": artifact_type,
                "filename": filename,
                "uploaded_at": datetime.now().isoformat()
            }
        )
    
    async def store_report(
        self, 
        report_type: str, 
        content: bytes,
        filename: str,
        agent_id: Optional[str] = None
    ) -> Optional[str]:
        """Store generated report"""
        agent_prefix = f"/{agent_id}" if agent_id else ""
        file_path = f"/reports{agent_prefix}/{report_type}/{filename}"
        
        return await self.s3_manager.upload_file(
            bucket_type="reports",
            file_path=file_path,
            content=content,
            metadata={
                "report_type": report_type,
                "agent_id": agent_id or "system",
                "filename": filename,
                "generated_at": datetime.now().isoformat()
            }
        )
    
    async def store_audit_log(
        self, 
        log_type: str, 
        content: bytes,
        filename: str
    ) -> Optional[str]:
        """Store audit log"""
        file_path = f"/audit_logs/{log_type}/{filename}"
        
        return await self.s3_manager.upload_file(
            bucket_type="audit_trails",
            file_path=file_path,
            content=content,
            metadata={
                "log_type": log_type,
                "filename": filename,
                "logged_at": datetime.now().isoformat()
            }
        )
    
    async def store_agent_artifact(
        self, 
        agent_id: str, 
        artifact_type: str,
        content: bytes,
        filename: str
    ) -> Optional[str]:
        """Store agent-generated artifact"""
        file_path = f"/agents/{agent_id}/{artifact_type}/{filename}"
        
        return await self.s3_manager.upload_file(
            bucket_type="agent_artifacts",
            file_path=file_path,
            content=content,
            metadata={
                "agent_id": agent_id,
                "artifact_type": artifact_type,
                "filename": filename,
                "created_at": datetime.now().isoformat()
            }
        )
    
    async def get_decision_artifacts(self, proposal_id: str) -> List[Dict[str, Any]]:
        """Get all artifacts for a decision proposal"""
        return await self.s3_manager.list_files(
            bucket_type="decision_artifacts",
            prefix=f"decisions/{proposal_id}/"
        )
    
    async def get_agent_artifacts(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all artifacts for an agent"""
        return await self.s3_manager.list_files(
            bucket_type="agent_artifacts",
            prefix=f"agents/{agent_id}/"
        )