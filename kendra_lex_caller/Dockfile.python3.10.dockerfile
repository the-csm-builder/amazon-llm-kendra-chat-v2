FROM public.ecr.aws/lambda/python:3.10

#Copy requirements
COPY requirements.txt .
RUN  pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

#Copy function code
#COPY /kendra_lex_caller/app_lambda.py ${LAMBDA_TASK_ROOT}
# Copy function code
COPY . ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler
CMD ["app_lambda.lambda_handler"]