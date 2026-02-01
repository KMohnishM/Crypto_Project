````markdown
# Digital Assignment - Phase I (DA-1)
## Cloud-Based Healthcare Monitoring System on AWS

**Team Members:**
- [Your Name] - Team Lead & AWS Infrastructure
- [Partner Name] - Application Development & Monitoring

**Project:** Healthcare Network Traffic Monitoring and Anomaly Detection System

---

## 1. Executive Summary

This report documents the AWS foundation setup for deploying a cloud-native healthcare monitoring system that provides real-time patient vital monitoring, anomaly detection, and alerting capabilities. The system leverages AWS services to create a scalable, secure, and highly available infrastructure for healthcare data processing.

### Key Objectives:
- Deploy multi-tier healthcare monitoring architecture on AWS
- Implement comprehensive security measures for healthcare data
- Establish monitoring and alerting infrastructure
- Ensure compliance with healthcare data protection standards

---

## 2. AWS Account Setup & Foundation

### 2.1 AWS Account Configuration
- **Account Type:** AWS Free Tier Account
- **Region:** us-east-1 (N. Virginia) - Primary region
- **Account Owner:** [Your Name]
- **Billing Alert:** Configured at $5 threshold
- **Root User:** MFA enabled with Google Authenticator

### 2.2 Cost Optimization Strategy
- Utilize AWS Free Tier benefits (12 months)
- Implement auto-scaling to minimize costs
- Use Spot Instances for non-critical workloads
- Monitor usage with AWS Cost Explorer

---

## 3. Identity and Access Management (IAM)

### 3.1 IAM Users and Groups

#### Admin Group
```json
{
  "GroupName": "Healthcare-Admins",
  "Policies": [
    "AdministratorAccess",
    "HealthcareSecurityPolicy"
  ]
}
```

#### Developers Group
```json
{
  "GroupName": "Healthcare-Developers", 
  "Policies": [
    "EC2FullAccess",
    "S3ReadWriteAccess",
    "CloudWatchFullAccess"
  ]
}
```

#### Monitoring Group
```json
{
  "GroupName": "Healthcare-Monitoring",
  "Policies": [
    "CloudWatchReadOnlyAccess",
    "S3ReadOnlyAccess"
  ]
}
```

### 3.2 IAM Roles

#### EC2 Instance Role
```json
{
  "RoleName": "Healthcare-EC2-Role",
  "TrustedEntities": "ec2.amazonaws.com",
  "Policies": [
    "CloudWatchAgentServerPolicy",
    "S3ReadWriteAccess",
    "SSMManagedInstanceCore"
  ]
}
```

#### Application Role
```json
{
  "RoleName": "Healthcare-App-Role",
  "TrustedEntities": "ecs-tasks.amazonaws.com",
  "Policies": [
    "S3ReadWriteAccess",
    "CloudWatchLogsFullAccess"
  ]
}
```

### 3.3 Multi-Factor Authentication (MFA)
- **Root User:** Hardware MFA device enabled
- **Admin Users:** Virtual MFA (Google Authenticator) required
- **Console Access:** MFA enforced for all users
- **API Access:** Access keys with rotation policy

### 3.4 Security Policies

#### Healthcare Data Protection Policy
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::healthcare-data-*/*",
      "Condition": {
        "StringEquals": {
          "aws:RequestTag/Environment": "Production"
        }
      }
    }
  ]
}
```

---

## 4. Virtual Private Cloud (VPC) Architecture

### 4.1 VPC Design
```
VPC: healthcare-monitoring-vpc (10.0.0.0/16)
├── Public Subnets (2 AZs)
│   ├── us-east-1a: 10.0.1.0/24 (Load Balancer)
│   └── us-east-1b: 10.0.2.0/24 (Bastion Host)
├── Private Subnets (2 AZs)
│   ├── us-east-1a: 10.0.10.0/24 (Application Tier)
│   └── us-east-1b: 10.0.11.0/24 (Application Tier)
└── Database Subnets (2 AZs)
    ├── us-east-1a: 10.0.20.0/24 (Database Tier)
    └── us-east-1b: 10.0.21.0/24 (Database Tier)
```

### 4.2 Network Security Groups

#### Load Balancer Security Group
```yaml
SecurityGroup: sg-loadbalancer
- Inbound: 80, 443 (HTTP/HTTPS)
- Outbound: All traffic to private subnets
```

#### Application Security Group
```yaml
SecurityGroup: sg-application
- Inbound: 8000, 6000 (from Load Balancer)
- Outbound: Database, S3, CloudWatch
```

#### Database Security Group
```yaml
SecurityGroup: sg-database
- Inbound: 5432 (from Application Tier only)
- Outbound: None
```

### 4.3 Route Tables
- **Public Route Table:** Internet Gateway for public subnets
- **Private Route Table:** NAT Gateway for private subnets
- **Database Route Table:** No internet access

---

## 5. AWS Services Implementation

### 5.1 Amazon EC2 Instances

#### Application Server (t3.micro - Free Tier)
```yaml
Instance: healthcare-app-server
- Type: t3.micro
- OS: Amazon Linux 2
- Storage: 8GB GP2 EBS
- IAM Role: Healthcare-EC2-Role
- Security Group: sg-application
- User Data: Docker installation script
```

#### Monitoring Server (t3.micro - Free Tier)
```yaml
Instance: healthcare-monitoring-server
- Type: t3.micro
- OS: Ubuntu 20.04
- Storage: 8GB GP2 EBS
- IAM Role: Healthcare-EC2-Role
- Security Group: sg-application
- Services: Prometheus, Grafana, Alertmanager
```

### 5.2 Amazon S3 Buckets

#### Data Storage Bucket
```yaml
Bucket: healthcare-patient-data-[account-id]
- Versioning: Enabled
- Encryption: SSE-S3
- Lifecycle: Move to IA after 30 days
- Access: Private with IAM policies
```

#### Log Storage Bucket
```yaml
Bucket: healthcare-logs-[account-id]
- Versioning: Enabled
- Encryption: SSE-S3
- Lifecycle: Delete after 90 days
- Access: CloudWatch Logs integration
```

#### Backup Bucket
```yaml
Bucket: healthcare-backups-[account-id]
- Versioning: Enabled
- Encryption: SSE-S3
- Cross-Region Replication: Enabled
- Access: Backup service only
```

### 5.3 CloudWatch Monitoring

#### Custom Metrics
```yaml
Namespace: Healthcare/Monitoring
Metrics:
- PatientVitals
- AnomalyScores
- SystemHealth
- ResponseTimes
```

#### Dashboards
- **Patient Monitoring Dashboard:** Real-time vital signs
- **System Health Dashboard:** Infrastructure metrics
- **Security Dashboard:** Access logs and alerts

#### Alarms
```yaml
Alarms:
- HighCPU: CPU > 80% for 5 minutes
- LowDiskSpace: Disk < 20% available
- HighMemory: Memory > 85% for 5 minutes
- ApplicationErrors: Error rate > 5%
```

---

## 6. Shared Responsibility Model Implementation

### 6.1 AWS Responsibilities (Security OF the Cloud)
- **Physical Security:** Data center security
- **Hardware Security:** Compute, storage, database
- **Network Security:** VPC, security groups
- **Virtualization Security:** Hypervisor security
- **Software Security:** AWS managed services

### 6.2 Customer Responsibilities (Security IN the Cloud)
- **Application Security:** Code security, input validation
- **Data Security:** Encryption, access control
- **Network Security:** Security group configuration
- **Identity Management:** IAM users, roles, policies
- **Compliance:** Healthcare data protection (HIPAA)

### 6.3 Implementation Checklist
- [x] Enable CloudTrail for audit logging
- [x] Configure VPC Flow Logs
- [x] Enable S3 access logging
- [x] Implement encryption at rest and in transit
- [x] Regular security group reviews
- [x] IAM access key rotation
- [x] MFA enforcement
- [x] Backup and disaster recovery

---

## 7. Proposed Architecture Block Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        AWS Cloud                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │   Route 53      │    │  CloudFront     │                    │
│  │   (DNS)         │    │  (CDN)         │                    │
│  └─────────────────┘    └─────────────────┘                    │
│           │                       │                            │
│           ▼                       ▼                            │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              Application Load Balancer                      │ │
│  │                    (ALB)                                 │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                              │                                 │
│                              ▼                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    Public Subnets                         │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │ │
│  │  │   Bastion   │  │   Load      │  │   NAT       │      │ │
│  │  │    Host     │  │ Balancer    │  │  Gateway    │      │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘      │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                              │                                 │
│                              ▼                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                   Private Subnets                         │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │ │
│  │  │   Main      │  │   Patient   │  │    ML       │      │ │
│  │  │   Host      │  │   Service   │  │  Service    │      │ │
│  │  │  (Flask)   │  │ (Data Gen) │  │(Anomaly)   │      │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘      │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                              │                                 │
│                              ▼                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                  Database Subnets                         │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │ │
│  │  │   RDS       │  │   ElastiCache│  │   Document  │      │ │
│  │  │ PostgreSQL  │  │    Redis    │  │     DB      │      │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘      │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    Monitoring Stack                       │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │ │
│  │  │ Prometheus  │  │   Grafana   │  │ Alertmanager│      │ │
│  │  │ (Metrics)   │  │(Dashboard) │  │ (Alerts)   │      │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘      │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    Storage Layer                          │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │ │
│  │  │   S3        │  │   S3        │  │   S3        │      │ │
│  │  │ Patient Data│  │    Logs     │  │  Backups    │      │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘      │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. Security Implementation

### 8.1 Data Encryption
- **At Rest:** S3 SSE-S3, RDS encryption
- **In Transit:** TLS 1.2+ for all communications
- **Application Level:** End-to-end encryption for patient data

### 8.2 Network Security
- **VPC:** Isolated network environment
- **Security Groups:** Least privilege access
- **NACLs:** Additional network layer protection
- **VPN:** Site-to-site VPN for secure access

### 8.3 Access Control
- **IAM:** Role-based access control
- **MFA:** Multi-factor authentication
- **Session Management:** Temporary credentials
- **Audit Logging:** CloudTrail and VPC Flow Logs

---

## 9. Cost Analysis (Free Tier)

### 9.1 Monthly Costs (Free Tier)
- **EC2:** 750 hours/month (t3.micro) - $0
- **S3:** 5GB storage - $0
- **RDS:** 750 hours/month (db.t3.micro) - $0
- **CloudWatch:** Basic monitoring - $0
- **Load Balancer:** 750 hours/month - $0

### 9.2 Estimated Post-Free Tier Costs
- **EC2:** ~$15/month (2 t3.micro instances)
- **S3:** ~$0.50/month (10GB storage)
- **RDS:** ~$15/month (db.t3.micro)
- **Load Balancer:** ~$20/month
- **Total:** ~$50/month

---

## 10. Compliance & Governance

### 10.1 Healthcare Compliance
- **HIPAA:** Data protection and privacy
- **HITECH:** Electronic health records
- **SOC 2:** Security controls
- **GDPR:** Data protection (if applicable)

### 10.2 Governance Framework
- **Access Reviews:** Quarterly IAM reviews
- **Security Audits:** Monthly security assessments
- **Backup Testing:** Weekly backup verification
- **Disaster Recovery:** Annual DR testing

---

## 11. Monitoring & Alerting

### 11.1 Infrastructure Monitoring
- **CloudWatch:** AWS service metrics
- **Prometheus:** Application metrics
- **Grafana:** Visualization dashboards
- **Alertmanager:** Incident response

### 11.2 Key Performance Indicators
- **Availability:** 99.9% uptime target
- **Response Time:** < 200ms API response
- **Error Rate:** < 1% application errors
- **Security:** Zero security incidents

---

## 12. Next Steps (Phase II)

### 12.1 Planned Enhancements
- **Auto Scaling:** Implement auto-scaling groups
- **Container Orchestration:** Migrate to ECS/EKS
- **Advanced Monitoring:** Implement APM tools
- **Disaster Recovery:** Multi-region deployment

### 12.2 Advanced AWS Services
- **Lambda:** Serverless functions
- **API Gateway:** RESTful API management
- **SQS/SNS:** Message queuing
- **CloudFormation:** Infrastructure as Code

---

## 13. Conclusion

This AWS foundation provides a robust, scalable, and secure platform for the healthcare monitoring system. The implementation follows AWS best practices and ensures compliance with healthcare data protection requirements. The architecture supports future growth and can be easily extended with additional AWS services.

### Key Achievements:
- ✅ Secure multi-tier architecture
- ✅ Comprehensive IAM implementation
- ✅ Healthcare-compliant security measures
- ✅ Cost-optimized Free Tier deployment
- ✅ Monitoring and alerting infrastructure

---

## 14. Appendices

### Appendix A: AWS CLI Commands
```bash
# Create VPC
aws ec2 create-vpc --cidr-block 10.0.0.0/16

# Create IAM Role
aws iam create-role --role-name Healthcare-EC2-Role

# Create S3 Bucket
aws s3 mb s3://healthcare-patient-data-[account-id]
```

### Appendix B: CloudFormation Template
[Include YAML template for infrastructure as code]

### Appendix C: Security Checklist
[Include detailed security implementation checklist]

---

**Document Version:** 1.0  
**Last Updated:** [Current Date]  
**Next Review:** [Date + 3 months] 
````