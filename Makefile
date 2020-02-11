CHECK=ecs-containder-instance-check
BUCKET=my-bucket
STACKNAME=ecs-containder-instance-check
COMMIT=$(shell git rev-parse --verify HEAD)

build-image:
	echo "docker image not required"

build:
	zip "${COMMIT}.zip" "src/handler.py"

unit-test:
	echo "no python unit tests yet"
	
deploy:
	sam package --template-file template.yaml --output-template-file packaged.yaml --s3-bucket ${BUCKET}
	sam deploy --template-file packaged.yaml --stack-name ${STACKNAME}-${COMMIT} --capabilities CAPABILITY_IAM
	aws cloudformation wait stack-create-complete --stack-name ${STACKNAME}-${COMMIT}
	
lambda-test:
	aws lambda invoke --function-name ${CHECK} --payload file://./event-sample.json lambda-test-1.json --log-type Tail --query 'LogResult' --output text | base64 -d
	if grep -q "errorMessage" lambda-test-*.json; then echo "\nLambda tests failed"; exit 1; else echo "\nLambda tests passed";	fi

destroy:
	aws cloudformation delete-stack --stack-name ${STACKNAME}-${COMMIT}