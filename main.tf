provider "aws" {
  region = "ap-south-1"

}

import {
  to = aws_instance.myinstance
  id = "i-0e012efcecf741e50"
}

import {
  to = aws_s3_bucket.mybucket
  id = "irfan07-test-bucket"
}

import {
  to = aws_instance.mynewinstance
  id = "i-0adb5d24d0bddecde"
}

import {
  to = aws_dynamodb_table.mytable
  id = "mydbtable"
}