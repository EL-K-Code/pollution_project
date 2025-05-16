from constructs import Construct
from cdktf import App, TerraformStack, TerraformAsset, AssetType, TerraformOutput
from cdktf_cdktf_provider_aws.provider import AwsProvider
from cdktf_cdktf_provider_aws.dynamodb_table import DynamodbTable
from cdktf_cdktf_provider_aws.iam_role import IamRole
from cdktf_cdktf_provider_aws.iam_role_policy import IamRolePolicy
from cdktf_cdktf_provider_aws.data_aws_caller_identity import DataAwsCallerIdentity
from cdktf_cdktf_provider_aws.lambda_function import LambdaFunction
from cdktf_cdktf_provider_aws.lambda_permission import LambdaPermission
from cdktf_cdktf_provider_aws.cloudwatch_event_rule import CloudwatchEventRule
from cdktf_cdktf_provider_aws.cloudwatch_event_target import CloudwatchEventTarget



class PollutionStack(TerraformStack):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)

        AwsProvider(self, "AWS", region="us-east-1")

        account_id = DataAwsCallerIdentity(self, "acount_id").account_id

        # DynamoDB table
        table = DynamodbTable(self, "PollutionTable",
            name="PollutionData",
            hash_key="city",
            attribute=[{
                "name": "city",
                "type": "S"
            }],
            billing_mode="PAY_PER_REQUEST"
        )

        # # IAM Role pour Lambda
        # role = IamRole(self, "LambdaRole",
        #     name="PollutionLambdaRole",
        #     assume_role_policy='''{
        #         "Version": "2012-10-17",
        #         "Statement": [{
        #             "Action": "sts:AssumeRole",
        #             "Effect": "Allow",
        #             "Principal": {
        #                 "Service": "lambda.amazonaws.com"
        #             }
        #         }]
        #     }'''
        # )

        # # Politique inline pour DynamoDB & CloudWatch logs
        # policy = IamRolePolicy(self, "LambdaPolicy",
        #     name="PollutionLambdaPolicy",
        #     role=role.id,
        #     policy=f'''{{
        #         "Version": "2012-10-17",
        #         "Statement": [
        #             {{
        #                 "Effect": "Allow",
        #                 "Action": [
        #                     "dynamodb:PutItem",
        #                     "dynamodb:UpdateItem"
        #                 ],
        #                 "Resource": "{table.arn}"
        #             }},
        #             {{
        #                 "Effect": "Allow",
        #                 "Action": [
        #                     "logs:CreateLogGroup",
        #                     "logs:CreateLogStream",
        #                     "logs:PutLogEvents"
        #                 ],
        #                 "Resource": "arn:aws:logs:*:*:*"
        #             }}
        #         ]
        #     }}'''
        # )

        # Package le code Lambda (dossier lambda/)
        asset = TerraformAsset(self, "LambdaCode",
            path="./lambda",
            type=AssetType.ARCHIVE
        )

        # Fonction Lambda
        function = LambdaFunction(self, "PollutionLambda",
            function_name="PollutionDataFetcher",
            role=f"arn:aws:iam::{account_id}:role/LabRole",
            runtime="python3.9",
            handler="lambda_function.lambda_handler",
            filename=asset.path,
            timeout=60,
            environment={
                "variables": {
                    "TABLE_NAME": table.name,
                    "API_KEY": "e1130114774b984a50bbbcae57c22e32"
                }
            }
        )

        # Règle EventBridge - déclenchement toutes les heures
        rule = CloudwatchEventRule(self, "HourlyRule",
            name="HourlyLambdaTrigger",
            schedule_expression="rate(1 hour)"
        )

        # Cible EventBridge = ta Lambda
        target = CloudwatchEventTarget(self, "LambdaTarget",
            rule=rule.name,
            arn=function.arn
        )

        # Permission pour EventBridge d’invoquer la Lambda
        LambdaPermission(self, "EventBridgeInvokePermission",
            action="lambda:InvokeFunction",
            function_name=function.function_name,
            principal="events.amazonaws.com",
            source_arn=rule.arn
        )
        # Outputs
        TerraformOutput(self, "dynamodb_table_name", value=table.name)
        TerraformOutput(self, "lambda_function_name", value=function.function_name)

app = App()
PollutionStack(app, "pollution_stack")
app.synth()
