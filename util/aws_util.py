import boto3


def image_ocr_bytes_to_text(image_bytes):
    # Create an Amazon Textract client
    textract = boto3.client('textract')

    # Call Amazon Textract to extract text from the image
    response = textract.detect_document_text(Document={'Bytes': image_bytes})

    # Extract the text from the response
    extracted_text = ""
    for item in response['Blocks']:
        if item['BlockType'] == 'LINE':
            extracted_text += item['Text'] + "\n"

    return extracted_text
