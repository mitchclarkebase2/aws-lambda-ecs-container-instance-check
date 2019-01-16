from invoke import run, task

@task
def test(c):
    c.run("sam local invoke EcsContainerInstanceCheck --event tests/cloudwatch-scheduled.json")

@task
def deploy(c,bucket,stack_name="ecs-check"):
    c.run(f"sam package --template-file template.yaml --output-template-file packaged.yaml --s3-bucket {bucket}")
    c.run(f"sam deploy --template-file packaged.yaml --stack-name {stack_name} --capabilities CAPABILITY_IAM")
