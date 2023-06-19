 ## Kendra Search Bot ##

The Kendra Search Bot is a solution that integrates Amazon Kendra, Amazon Lex, AWS Lambda, and Amazon SageMaker to create a smart, conversational bot. The bot is designed to provide detailed answers based on user queries by leveraging the powerful search capabilities of Amazon Kendra and the natural language processing capabilities of Lex and SageMaker.

### Overview ###

This bot receives a user query, searches a Kendra index for relevant documents, then uses a Language Model to generate a detailed response to the query based on the documents found. This solution is designed to offer a conversational and context-aware search experience.

### Components ###

 - Amazon Kendra: Kendra is a highly accurate and easy-to-use enterprise search service powered by machine learning. Kendra delivers powerful natural language search capabilities to websites and applications so end users can more easily find the information they need within the vast amount of content spread across an organization.

- Amazon Lex: Lex is a service for building conversational interfaces using voice and text. Lex provides advanced deep learning functionalities of automatic speech recognition (ASR) for converting speech to text, and natural language understanding (NLU) to recognize the intent of the text.

-  AWS Lambda: Lambda is an event-driven, serverless computing platform. It is a computing service that runs code in response to events and automatically manages the computing resources required by that code.

-  Amazon SageMaker: SageMaker is a fully managed machine learning service. With SageMaker, data scientists and developers can build and train machine learning models and deploy them directly into a production-ready hosted environment.

## Setup ##

You can deploy the code using docker, ECR, and lambda image. I setup the lambda manually for testing purposes. You can automate the deployment with sam, cloud formation or the cli. 

## Limitations ##
Flan XXL is terse with responses, and good for QnA scenarios, but not generation scenarios. Context awareness and conversation history are Work in progress, and not fully deployed. 