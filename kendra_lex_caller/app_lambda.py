from langchain.docstore.document import Document
from langchain.llms.sagemaker_endpoint import LLMContentHandler
from langchain import PromptTemplate, SagemakerEndpoint
from langchain.chains.question_answering import load_qa_chain
import json
import boto3
from datetime import datetime
import os # added 6/22 to eliminate hard coded values

class ContentHandler(LLMContentHandler):
    content_type = "application/json"
    accepts = "application/json"

    def transform_input(self, prompt: str, model_kwargs: dict) -> bytes:
        input_str = json.dumps({"text_inputs": prompt, **model_kwargs})
        return input_str.encode('utf-8')

    def transform_output(self, output: bytes) -> str:
        response_json = json.loads(output.read().decode("utf-8"))
        #print(response_json)
        print(response_json)
        return response_json["generated_texts"][0]

content_handler = ContentHandler()

# prompt_template = """Use the following pieces of context to answer the question at the end.

# {context}

# Question: {question}
# Answer:"""

prompt_template = """
The following is a friendly conversation between a human and an AI. 
The AI is talkative and provides lots of specific details from its context.
If the AI does not know the answer to a question, it truthfully says it 
does not know.
{context}
Instruction: Based on the above documents, provide a detailed answer for, {question} Answer "don't know" if not present in the document. Solution:
"""

PROMPT = PromptTemplate(
    template=prompt_template, input_variables=["context", "question"]
)

# retrieve the endpoint name and region from the environment variables
endpoint_name = os.environ['SAGEMAKER_ENDPOINT_NAME']
region_name = os.environ['AWS_REGION_NAME']

chain = load_qa_chain(
    llm=SagemakerEndpoint(
        endpoint_name=endpoint_name,
        region_name=region_name,
        model_kwargs={"temperature":1e-10, "max_length":500},
        content_handler=content_handler
    ),
    prompt=PROMPT
)

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

# add converstion history logic to dynamo db
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('conversation_history')

# add current date
created_date = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

# add QnA pair to dynamod db table called conversation_history
def add_to_history(question, answer):
    table.put_item(
        Item={
            'question': question,
            'answer': answer,
            'created_date': created_date,
        }
    )
# Function to retrieve to scan conversation_history
def get_history():
    response = table.scan()
    return response['Items']

def lambda_handler(event, context):
    # Define the Kendra client
    kendra_client = boto3.client('kendra')

    # Extract the user input from the event
    user_input = event['inputTranscript']

    # Get the current session attributes
    session_attributes = event['sessionAttributes'] if 'sessionAttributes' in event else {}

    # retrieve the kendra index id from environment variables
    kendra_index_id = os.environ['KENDRA_INDEX_ID']

    # Query Kendra with the user input
    kendra_response = kendra_client.query(
        IndexId=kendra_index_id,
        QueryText=user_input
    )

    # Extract the top document text from the Kendra response
    document_text = kendra_response['ResultItems'][0]['DocumentExcerpt']['Text']
    document_source = kendra_response['ResultItems'][0]['DocumentURI']

    # Create a Document object from the Kendra result
    doc = Document(page_content=document_text, metadata={"source": document_source})

    # Generate context from the conversation history
    # history = get_history()
    # history_text =''.join([f"Question: {item['question']}\nAnswer: {item['answer']}\n\n" for item in history])

    # Run the QA chain
    output = chain({"input_documents": [doc], "question": user_input}, return_only_outputs=True)

    # Add the question and answer to the conversation_history ddb table
    add_to_history(user_input, output["output_text"])

    # Exract the output_text value
    output_text = output["output_text"]

    message = {
    'contentType': 'PlainText',
    #'content': f"{output}\n\nSource: {document_source}"
    # add content, and a sentence for the document source
    #'content': f"{output_text}. /n/n For more details click on this URL {document_source}"
    'content': f"{output_text}."
    }
    fullfillment_state = 'Fulfilled'

    # call close function
    return close(event, session_attributes, fullfillment_state, message)