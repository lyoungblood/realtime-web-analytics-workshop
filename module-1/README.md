#  Configure a fleet of Web Servers to send Clickstream data to a Kinesis Firehose delivery stream

## Introduction

In this module, you will start with an AutoScaling group of Apache web servers, and configure them to stream their log data in realtime to a Kinesis Firehose delivery stream. This will prepare for us to perform realtime analytics on the events being captured in these logs.

## Architecture Overview

![module-1-diagram](../images/module-1.png)

## 1. Deploy Web Servers using CloudFormation Template

First we need to deploy our web servers in an AutoScaling group, with an Application Load Balancer to accept incoming connections, and scaling policies to scale out (and back in) based on incoming network traffic.

<details>
<summary><strong>CloudFormation Launch Instructions (expand for details)</strong></summary><p>

1.	Right click the **Launch Stack** link below and "open in new tab"

Region| Launch
------|-----
US West (Oregon) | [![Launch Module 1 in ](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/images/cloudformation-launch-stack-button.png)](https://console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/new?stackName=realtime-analytics-workshop&templateURL=https://s3-us-west-2.amazonaws.com/realtime-analytics-workshop/1-frontend-module-start.yaml)
US West (N. Virginia) | [![Launch Module 1 in ](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/images/cloudformation-launch-stack-button.png)](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=realtime-analytics-workshop&templateURL=https://s3-us-west-2.amazonaws.com/realtime-analytics-workshop/1-frontend-module-start.yaml)

2.	Click **Next** on the Select Template page.
3.	**(Optional)** If you'd like to login to the web servers, select an **SSH Keypair** for this region, select True next to **Enable SSH**, and enter a CIDR block such as `0.0.0.0/0` next to **Enable SSH From**. If you don't have a key pair already created, see ([Creating a key pair using amazon EC2](http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html#having-ec2-create-your-key-pair))

![Configuring SSH access](../images/module-1-ssh.png)

![Configuring CloudFormation Stack](../images/module-1-next.png)

4.	Click **Next**.
5.	Click **Next** Again. (skipping IAM advanced section)
6.	On the Review page, check the box to acknowledge that CloudFormation will create IAM resources and click **Create**.

![iam-accept](../images/iam-accept.png)

7. While you wait for the CloudFormation stack to be created, download the CloudFormation template by right-clicking here and selecting **Save Link As...**: ([Module 1 Starting Template](https://s3-us-west-2.amazonaws.com/realtime-analytics-workshop/1-frontend-module-start.yaml))
8. Open the template you just downloaded in a text editor.  If you don't have a text editor, you can download a trial of Sublime Text here: ([Sublime Text](https://www.sublimetext.com))

When you see the stack showing a CREATE_COMPLETE status, you are ready to move on to the next step.

</p></details>

## 2. Add the Kinesis Resources to the CloudFormation Template 

<details>
<summary><strong>Edit the CloudFormation template (expand for details)</strong></summary><p>

1.	Open the CloudFormation template you downloaded in the previous step in an editor.  
2.	At the bottom of the **Resources** section, directly above the **Outputs** section, add the resource for the analytics S3 bucket that will receive messages delivered by the Kinesis Delivery Stream:

<details>
<summary><strong>AnalyticsBucket Resource (expand for code)</strong></summary>

```
# Kinesis Application
  AnalyticsBucket:
    Type: AWS::S3::Bucket
    DeletionPolicy: Retain
```

</details>

3.	Add the IAM Role and Policy that will give the Kinesis Delivery Stream permissions to deliver the events directly below the S3 bucket resource:

<details>
<summary><strong>DeliveryStreamRole Resource (expand for code)</strong></summary>

```
  DeliveryStreamRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service:
                - firehose.amazonaws.com
            Action:
              - sts:AssumeRole
      Policies:
        - PolicyName: s3Access
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Sid: ''
                Effect: Allow
                Action:
                  - s3:AbortMultipartUpload
                  - s3:GetBucketLocation
                  - s3:GetObject
                  - s3:ListBucket
                  - s3:ListBucketMultipartUploads
                  - s3:PutObject
                Resource:
                  - !Sub '${AnalyticsBucket.Arn}'
                  - !Sub '${AnalyticsBucket.Arn}/*'
              - Sid: ''
                Effect: Allow
                Action:
                  - logs:PutLogEvents
                Resource:
                  - !Sub 'arn:aws:logs:${AWS::Region}:${AWS::AccountId}:log-group:/aws/kinesisfirehose/*:log-stream:*'
```
Note: We are following the _principle of least privilege_ by enabling resource-level permissions and referencing the `AnalyticsBucket` as `!Sub '${AnalyticsBucket.Arn}'`

</details>

4. Next, add the Kinesis Delivery Stream resource directly below the IAM Role:

<details>
<summary><strong>DeliveryStream Resource (expand for code)</strong></summary>

```
  DeliveryStream:
    Type: AWS::KinesisFirehose::DeliveryStream
    Properties:
      DeliveryStreamType: DirectPut
      S3DestinationConfiguration:
        BucketARN: !Sub '${AnalyticsBucket.Arn}'
        BufferingHints:
          IntervalInSeconds: '60'
          SizeInMBs: '1'
        CompressionFormat: UNCOMPRESSED
        RoleARN: !GetAtt 'DeliveryStreamRole.Arn'
```
Note: By setting `IntervalInSeconds` to `60` and `SizeInMBs` to `1`, we are configuring the Kinesis Delivery Stream to deliver events to the S3 bucket whenever either 60 seconds has elapsed, or more than 1MB of event data is in the stream.  Whenever either of these conditions is met, the events will be delivered.

</details>

</p></details>

## Validation Step

<details>
<summary><strong>Verify sample data exists on your EC2 instance (expand for details)</strong></summary><p>

Once you have connected to the Windows Instance via RDP, open the File Explorer and verify that there is a C: drive and a D: drive and that there are JPEG files in the D: drive.

(Optionally) You can add your own unqiue file data to the d: volume by creating a text file or downloading images via firefox within the RDP session.

![scenario-1-module-1-Picture5](../../images/scenario-1-module-1-Picture5.png)

You now have a Windows instance in Ireland (eu-west-1) that contains a boot volume and a data volume. The secondary volume and it's data will be used as sample data for the other modules in this workshop.
</p></details>

### Start next module

Module 2: [Migrate data to an AWS Storage Gateway volume](../module-2/README.md)

## License

This library is licensed under the Amazon Software License.

[Back to the main workshop scenarios page](../../README.md)
