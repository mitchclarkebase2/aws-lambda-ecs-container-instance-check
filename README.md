# Ecs Container Instance AWS Lambda Check

Lambda function to check the agent status of a ECS cluster instance for a given cluster


Optionally, it can record metrics to CloudWatch.

## Inputs

All inputs are either defined as environment variables or as part of event data. Event data
will take priority over environment variables

`CLUSTER` - cluster name to be checked

`REPORT_AS_CW_METRICS` - set to 1 if you wish to store reported data as CW
custom metrics, 0 otherwise, defaults to 1

`CW_METRICS_NAMESPACE` - if CW custom metrics are being reported, this will determine
their namespace, defaults to 'EcsCICheck'


## Testing

Using sam cli local to test the function using the events in [tests](tests)

```bash
invoke test
```

## Deploy

Deploy using sam template

```bash
invoke deploy [s3 bucket] [stack name]
```
