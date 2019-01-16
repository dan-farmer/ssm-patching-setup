# ssm-patching-setup
Automated creation of AWS SSM Patch Manager resources for simple automated patching

## Usage
```
export AWS_ACCESS_KEY_ID=foo
export AWS_SECRET_ACCESS_KEY=bar
export AWS_SESSION_TOKEN=baz
./ssm_patching_setup.py -b BASELINE_FILE
```
The defaults will create 8 Maintenance Windows. In human terms, these are:
* 03:00, first Tuesday of the month
* 04:00, first Tuesday of the month
* 03:00, first Wednesday of the month
* 04:00, first Wednesday of the month
* 03:00, second Tuesday of the month
* 04:00, second Tuesday of the month
* 03:00, second Wednesday of the month
* 04:00, second Wednesday of the month

Optional parameters to control the Maintenance Window schedules and other options:

| Short Option | Long Option | Default  | Notes |
| ------------ | ----------- | -------- | ----- |
| -w           | --week      | 1 2      | [See note below](#Week) |
| -d           | --days      | 2 3      | Tue, Wed |
| -t           | --hours     | 3 4      | 03:00, 04:00 |
| -z           | --timezone  |          | Use tzdata zones |
| -r           | --region    | [See note below](#Region) | Short region alias (e.g. 'us-east-1') |
| -b           | --baseline-file |      | REQUIRED; [See note below](#baseline-file) |
| -h           | --help      |          |       |
| -l           | --loglevel  |          | DEBUG, INFO, WARNING, ERROR, CRITICAL |

### Authentication
By design, these scripts do not handle authentication. Use one of the following methods for authentication with the AWS APIs:
1. [AWS Environment variables](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#environment-variables)
1. [AWS Credentials file](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#shared-credentials-file)
1. [AWS Config file](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#aws-config-file)
1. Wrap around or customise the scripts

### Region
If region is not specified, the script will attempt to proceed with the user's default region configured for the AWS SDK:
1. [AWS Environment variables](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#environment-variable-configuration)
1. [AWS Credentials file](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#shared-credentials-file)
1. [AWS Config file](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#aws-config-file)

### Baseline File
A JSON-formatted file containing the properties of the baseline to create is required. See the [baselines](baselines) directory for samples/examples.

### Week
It's important to note that the week is specified as (for example) 'the second week of the month' and not 'the second full week'; That is to say, the Maintenance Window schedule is specified as 'the second Tuesday of the month' and not 'the Tuesday of the second full week of the month'.

The practical implications of this are that Maintenance Windows for 'week 1' will always occur before 'week 2', but 'Tuesday, week 1' might occur after 'Wednesday, week 1'.

## Cleanup
`ssm_patching_cleanup.py` will destroy all SSM Patch Manager resources in the region:
* All Maintenance Window Tasks for `AWS-ApplyPatchBaseline` or `AWS-RunPatchBaseline`
* All Maintenance Windows with no tasks or only patching tasks as above
* All Patch Baseline registrations for Patch Groups
* All custom Patch Baselines

## FAQ
1. Why not implement this idempotently, so that the script can be run repeatedly and will always converge to the same configuration?
   * Doing this reliably would require tracking some state - essentially, recording the physical ID of the resources we create, and using this to ensure we update the same resources every time
   * Practically, this would mean implementing with an IaC (Infrastructure as Code) tool, e.g. CloudFormation or Terraform
2. Why not implement this as IaC (Infrastructure as Code)?
   * This project was developed to meet a requirement for implementing patching outside of IaC management
   * Example CloudFormation templates or Terraform modules may be added in future
