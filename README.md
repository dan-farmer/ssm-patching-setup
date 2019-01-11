# ssm-patching-setup
Automated creation of AWS SSM Patch Manager resources for simple automated patching

## Usage
```
export AWS_DEFAULT_REGION=foo
export AWS_ACCESS_KEY_ID=bar
export AWS_SECRET_ACCESS_KEY=baz
export AWS_SESSION_TOKEN=qux
./ssm_patching_setup.py
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
| -h           | --help      |          |       |
| -l           | --loglevel  |          | DEBUG, INFO, WARNING, ERROR, CRITICAL |

### Week
It's important to note that the week is specified as (for example) 'the second week of the month' and not 'the second full week'; That is to say, the Maintenance Window schedule is specified as 'the second Tuesday of the month' and not 'the Tuesday of the second full week of the month'.

The practical implications of this are that Maintenance Windows for 'week 1' will always occur before 'week 2', but 'Tuesday, week 1' might occur after 'Wednesday, week 1'.

## Cleanup
`ssm_patching_cleanup.py` will destroy all SSM Patch Manager resources in the current region:
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
