# AWS Provider Configuration

provider "aws" {
  region = "ap-south-1"                        # Replace with your preferred AWS Region

}

# Import Existing EC2 Instance

import {
  to = aws_instance.myinstance
  id = "instance_id"                   # Replace with your EC2 Instance ID
}

# Import Existing S3 Bucket

import {
  to = aws_s3_bucket.mybucket
  id = "irfan07-test-bucket"                  # Replace with your S3 Bucket Name
}

# Import Newly Added EC2 Instance

import {
  to = aws_instance.mynewinstance            # Replace with your EC2 Instance ID
  id = "instance_id"
}

# Import Existing DynamoDB Table

import {
  to = aws_dynamodb_table.mytable            # Replace with your DynamoDB Table Name
  id = "dynamodb_table_name"
}