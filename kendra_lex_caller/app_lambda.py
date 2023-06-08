# this code works with Lex tested on June 5th
import boto3
import json
import os

class ContentHandler:
    content_type = "application/json"
    accepts = "application/json"

    def transform_input(self, prompt: str, model_kwargs: dict) -> bytes:
        input_str = json.dumps({"text_inputs": prompt, **model_kwargs})
        return input_str.encode('utf-8')
   
    def transform_output(self, output: bytes) -> str:
        response_json = json.loads(output.read().decode("utf-8"))
        return response_json["generated_texts"][0]

content_handler = ContentHandler()

def close(intent_request, session_attributes, fulfillment_state, message):
    intent_request['sessionState']['intent']['state'] = fulfillment_state
    return {
        'sessionState': {
            'sessionAttributes': session_attributes,
            'dialogAction': {
                'type': 'Close',    
        },
        'intent': intent_request['sessionState']['intent']
    },
        'messages': [message],
        'sessionId': intent_request['sessionId'],
        'requestAttributes': intent_request['requestAttributes'] if 'requestAttributes' in intent_request else None
        }

def lambda_handler(event, context):
    # Get kendra index id and sagemaker end point from envirnoment variables
    kendra_index_id = os.environ['KENDRA_INDEX_ID']
    sagemaker_endpoint = os.environ['SAGEMAKER_ENDPOINT']
   
    # Define the Kendra, SageMaker, and Lex clients
    kendra_client = boto3.client('kendra')
    sagemaker_runtime_client = boto3.client('sagemaker-runtime')

    # Extract the user input from the event
    user_input = event['inputTranscript']

    # Get the current session attributes
    session_attributes = event['sessionAttributes'] if 'sessionAttributes' in event else {}

    # Get the conversation history from the session attributes
    conversation_history = json.loads(session_attributes.get('conversationHistory', '[]'))

    # Add the user input to the conversation history
    conversation_history.append({'user': user_input})

    # Query Kendra with the user input
    kendra_response = kendra_client.query(
        IndexId=kendra_index_id,
        QueryText=user_input
    )
   
    # Extract the top document text from the Kendra response
    document_text = kendra_response['ResultItems'][0]['DocumentExcerpt']['Text']

    # Add the document text to the conversation history
    conversation_history.append({'user': document_text})
   
    # Construct the LLM prompt
    llm_prompt = f"""
    The following is a friendly conversation between a human and an AI.
    The AI is talkative and provides lots of specific details from its context.
    If the AI does not know the answer to a question, it truthfully says it
    does not know.
    {document_text}
    Instruction: Based on the above documents, provide a detailed answer for, {user_input} Answer "don't know" if not present in the document. Solution:
    """

    # Transform the LLM prompt to the SageMaker LLM input format
    transformed_input = content_handler.transform_input(
        llm_prompt, {"max_length": 500})

    # Send the transformed input to the SageMaker LLM endpoint
    sagemaker_response = sagemaker_runtime_client.invoke_endpoint(
        EndpointName=sagemaker_endpoint,
        Body=transformed_input,
        ContentType=content_handler.content_type,
        Accept=content_handler.accepts
    )

    # Transform the SageMaker LLM output back into a usable form
    sagemaker_output = content_handler.transform_output(
        sagemaker_response['Body'])

    # Add the bot response to the conversation history
    conversation_history.append({'bot': sagemaker_output})

    # Convert the conversation history to a string before storing it in the session attributes
    session_attributes['conversationHistory'] = json.dumps(conversation_history)

    message = {
        'contentType': 'PlainText',
        'content': sagemaker_output
        }
    fullfillment_state = 'Fulfilled'

    # call close function
    return close(event, session_attributes, fullfillment_state, message)