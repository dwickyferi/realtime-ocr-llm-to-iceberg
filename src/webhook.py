from flask import Flask, jsonify, request
from pydantic import BaseModel
from datetime import datetime
import boto3
from botocore.client import Config
import json
from pydantic import BaseModel, Field
from typing import Optional
from groq import Groq
import base64
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import os

GROQ_KEY_API = "YOUR_GROQ_API_KEY"  # Replace with your actual Groq API key
client = Groq(api_key=GROQ_KEY_API)

# Database connection
DATABASE_URL = "postgresql://postgres:postgres@localhost:5566/postgres"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Define SQLAlchemy models
class ReceiptHeader(Base):
    __tablename__ = "receipt_headers"
    
    id = Column(Integer, primary_key=True)
    businessName = Column(String)
    date = Column(String)
    total = Column(Float)
    tax = Column(Float)
    items = relationship("ReceiptItem", back_populates="header")

class ReceiptItem(Base):
    __tablename__ = "receipt_items"
    
    id = Column(Integer, primary_key=True)
    header_id = Column(Integer, ForeignKey('receipt_headers.id'))
    name = Column(String)
    price = Column(Float)
    header = relationship("ReceiptHeader", back_populates="items")

# Create tables
Base.metadata.create_all(engine)

# Function to save receipt data to database
def save_receipt_to_db(receipt_data: dict):
    session = SessionLocal()
    try:
        # Create header record
        header = ReceiptHeader(
            businessName=receipt_data.get('businessName'),
            date=receipt_data.get('date'),
            total=receipt_data.get('total'),
            tax=receipt_data.get('tax')
        )
        session.add(header)
        session.flush()  # Get the header ID
        
        # Create item records
        for item in receipt_data.get('items', []):
            detail = ReceiptItem(
                header_id=header.id,
                name=item.get('name'),
                price=item.get('price')
            )
            session.add(detail)
        
        session.commit()
        return header.id
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

# Define the schema for receipt data matching the Next.js example
class Receipt(BaseModel):
    businessName: Optional[str] = Field(None, description="Name of the business on the receipt")
    date: Optional[str] = Field(None, description="Date when the receipt was created")
    total: Optional[float] = Field(None, description="Total amount on the receipt")
    tax: Optional[float] = Field(None, description="Tax amount on the receipt")
    items: Optional[list] = Field(None, description="List of items purchased, each with name and price")

def extract_receipt_info(image_path: str) -> dict:
    """
    Extract receipt information from an image using Together AI's vision capabilities.
    
    Args:
        image_url: URL of the receipt image to process
        
    Returns:
        A dictionary containing the extracted receipt information
    """
    # Call the Together AI API with the image URL and schema
    # Read and encode the local image
    
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    # Get base64 representation of the image
    base64_image = encode_image(image_path)
    
    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {
                "role": "system",
                "content": f"You are an expert at extracting information from receipts. Extract the relevant information and format it as JSON with the following schema: {Receipt.model_json_schema()}"
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract receipt information"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        response_format={
            "type": "json_object",
            "schema": Receipt.model_json_schema()
        }
    )
    
    # Parse and return the response
    if response and response.choices and response.choices[0].message.content:
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            return {"error": "Failed to parse response as JSON"}
    
    return {"error": "Failed to extract receipt information"}

class S3EventData(BaseModel):
    event_name: str
    bucket_name: str
    object_key: str
    object_size: int
    content_type: str
    event_time: datetime

    @classmethod
    def from_raw_event(cls, data: dict):
        return cls(
            event_name=data.get('EventName'),
            bucket_name=data['Records'][0]['s3']['bucket']['name'],
            object_key=data['Records'][0]['s3']['object']['key'],
            object_size=data['Records'][0]['s3']['object']['size'],
            content_type=data['Records'][0]['s3']['object']['contentType'],
            event_time=data['Records'][0]['eventTime']
        )

app = Flask(__name__)

@app.route("/minio/receipt/event", methods=["POST"])
def get_notif_receipt():
    data = request.get_json()
    event_data = S3EventData.from_raw_event(data)
    data = event_data.model_dump()
    
    # Initialize MinIO client
    s3_client = boto3.client('s3',
        endpoint_url='http://localhost:9000',  # Replace with your MinIO server URL
        aws_access_key_id='admin',           # Replace with your access key
        aws_secret_access_key='password',       # Replace with your secret key
        config=Config(signature_version='s3v4'),
        region_name='us-east-1'
    )

    # Download file from MinIO
    local_path = f"./tmp/{event_data.object_key}"
    s3_client.download_file(
        event_data.bucket_name,
        event_data.object_key,
        local_path
    )

    result = extract_receipt_info(local_path)
    print(json.dumps(result, indent=2))
    # Save the extracted receipt data to the database
    receipt_id = save_receipt_to_db(result)
    print(f"Receipt saved with ID: {receipt_id}")

    # Here you can process the downloaded file
    # Add your processing logic here

    return jsonify({
        "status": "success",
        "message": f"File {event_data.object_key} processed successfully",
        "data": data
    }), 200

if __name__ == "__main__":
    app.run(debug=True, port="5010", host="0.0.0.0")