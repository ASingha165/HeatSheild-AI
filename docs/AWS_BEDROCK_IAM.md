# AWS IAM Configuration for Amazon Bedrock Inference

This document outlines the security architecture, least-privilege IAM policies, and execution roles required for **HeatShield AI** to perform generative environmental reasoning via Amazon Bedrock.

---

## 1. Security Architecture & Principles

1. **No Static Credentials**: Long-lived access keys (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`) must never be hard-coded into source code or committed to Git.
2. **IAM Roles in Deployment**: When hosted on **AWS EC2**, **ECS**, or **EKS**, HeatShield AI uses the AWS Instance Profile / Execution Role to automatically authenticate via temporary credentials through `boto3`.
3. **Least Privilege**: The IAM policy restricts access strictly to the foundation models used for municipal reasoning (`bedrock:InvokeModel` and `bedrock:Converse`).

---

## 2. Least-Privilege IAM Policy

Attach the following policy to your EC2 IAM Role (`HeatShield-EC2-Role`):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "HeatShieldBedrockInference",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:*::foundation-model/amazon.nova-lite-v1:0",
        "arn:aws:bedrock:*:*:inference-profile/*",
        "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-haiku-20240307-v1:0",
        "arn:aws:bedrock:*::foundation-model/amazon.titan-text-express-v1"
      ]
    }
  ]
}
```

---

## 3. EC2 Instance Profile Setup

### Step 1: Create IAM Role for EC2
```bash
aws iam create-role \
  --role-name HeatShield-EC2-Role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {"Service": "ec2.amazonaws.com"},
        "Action": "sts:AssumeRole"
      }
    ]
  }'
```

### Step 2: Attach the Bedrock Policy
```bash
aws iam put-role-policy \
  --role-name HeatShield-EC2-Role \
  --policy-name HeatShieldBedrockAccess \
  --policy-document file://docs/bedrock-policy.json
```

### Step 3: Create Instance Profile and Attach to EC2
```bash
aws iam create-instance-profile --instance-profile-name HeatShield-Instance-Profile
aws iam add-role-to-instance-profile \
  --instance-profile-name HeatShield-Instance-Profile \
  --role-name HeatShield-EC2-Role

aws ec2 associate-iam-instance-profile \
  --instance-id <YOUR-EC2-INSTANCE-ID> \
  --iam-instance-profile Name=HeatShield-Instance-Profile
```

---

## 4. Local Development Fallback & Transparent Dev Mode

When running locally without active AWS credentials:
* HeatShield AI automatically identifies that credentials are absent.
* The system reports `is_configured: false` and `auth_mechanism: "unconfigured"`.
* It safely runs in **Transparent Dev Mode**, synthesizing structured recommendations directly from verified tool results and marking `is_live_bedrock: false` without fabricating API responses.
