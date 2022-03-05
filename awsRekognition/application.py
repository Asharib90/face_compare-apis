from flask import Flask, request, jsonify, flash
import boto3
# EB looks for an 'application' callable by default.
application = Flask(__name__)

@application.route("/",methods=["POST", "GET"]) 

def init():
    return ('hello world')
  

@application.route("/register",methods=["POST"])

def register():
  
    try:        
      empCode = request.form['empCode'] 
      image = request.files.get('image')
      
      
      threshold=70
      path = 'register/'+ empCode +'.jpg'
      region_name='us-east-2'
      bucket ='attandence-bucket'
      TableName='attandence_collection'
      collection_id = "attandence_collection"
  
      rekognition = boto3.client('rekognition', region_name = region_name)
      dynamodb = boto3.client('dynamodb', region_name = region_name)
      s3 = boto3.resource('s3')
      
      object = s3.Object(bucket,path)
      s3_upload = object.put(Body=image,
                      Metadata={'empCode':empCode}
                      )
      
      if s3_upload['ResponseMetadata']['HTTPStatusCode'] ==  200:
          
          try :                                       
                search_faces_by_image_response = rekognition.search_faces_by_image(
                    Image={
                        "S3Object": {
                            "Bucket": bucket,
                            "Name": path,
                        }
                    },
                    CollectionId=collection_id,
                    FaceMatchThreshold=threshold)
                            
                if search_faces_by_image_response['ResponseMetadata']['HTTPStatusCode'] ==  200:
                    try :                                       
                        faceId = search_faces_by_image_response['FaceMatches'][0]['Face']['FaceId']
                        
                        dynamodb_response = dynamodb.get_item(
                            TableName=TableName,  
                            Key={'RekognitionId':{'S': faceId}})
                        
                        if dynamodb_response['ResponseMetadata']['HTTPStatusCode'] ==  200 :
                            
                            if dynamodb_response['Item']['empCode']['S'] == empCode:
                                index_face_response=rekognition.index_faces(CollectionId=collection_id,
                                            Image={'S3Object':{'Bucket':bucket,'Name':path}},
                                            MaxFaces=1,
                                            QualityFilter="AUTO",
                                            DetectionAttributes=['ALL'])

                                if index_face_response['ResponseMetadata']['HTTPStatusCode'] ==  200:
                                
                                    try:               
                                        faceId = index_face_response['FaceRecords'][0]['Face']['FaceId']
                                        dynamodb_response = dynamodb.put_item(
                                            TableName = TableName,
                                            Item={
                                                'RekognitionId': {'S': faceId},
                                                'empCode': {'S': empCode}
                                                }
                                            )                            
                                        if dynamodb_response['ResponseMetadata']['HTTPStatusCode'] ==  200:
                                            return jsonify({"response": "Face successfully registered"})             
                                        else:
                                            return jsonify({'error':"image not added to dynamoDB"}), 404
                                    except:
                                        return jsonify({'error':"image does not contain face"}), 404            
                                else:
                                    return jsonify({'error':"image not added to index_faces"}), 404                           
                                    
                            return jsonify({'error':"Face already registered on ID: " +  dynamodb_response['Item']['empCode']['S'],}), 422 
                        else:
                            return jsonify({'error':"Image not added to index_faces"}), 404
                    
                    except:                  
                        index_face_response=rekognition.index_faces(CollectionId=collection_id,
                                            Image={'S3Object':{'Bucket':bucket,'Name':path}},
                                            MaxFaces=1,
                                            QualityFilter="AUTO",
                                            DetectionAttributes=['ALL'])

                        if index_face_response['ResponseMetadata']['HTTPStatusCode'] ==  200:
                        
                            try:               
                                faceId = index_face_response['FaceRecords'][0]['Face']['FaceId']
                                dynamodb_response = dynamodb.put_item(
                                    TableName = TableName,
                                    Item={
                                        'RekognitionId': {'S': faceId},
                                        'empCode': {'S': empCode}
                                        }
                                    )                            
                                if dynamodb_response['ResponseMetadata']['HTTPStatusCode'] ==  200:
                                    return jsonify({"response": "Face successfully registered"})             
                                else:
                                    return jsonify({'error':"image not added to dynamoDB"}), 404
                            except:
                                return jsonify({'error':"image does not contain face"}), 404            
                        else:
                            return jsonify({'error':"image not added to index_faces"}), 404
                else:
                    return jsonify({'error':"Search faces by image not working"}), 404  
          except:
              return jsonify({'error':"Image does not contain face"}), 404      
      else:
          return jsonify({'error':"image not uploaded on S3"}), 404
    except:
        return jsonify({'error':"image not found"}), 404
    

@application.route("/verify",methods=["POST"])

def verify():
    try:        
        empCode = request.form['empCode'] 
        image = request.files.get('image')
        
        threshold=70
        path = 'verify/'+ empCode +'.jpg'
        region_name='us-east-2'
        bucket ='attandence-bucket'
        TableName='attandence_collection'
        collection_id = "attandence_collection"
    
        rekognition = boto3.client('rekognition', region_name = region_name)
        dynamodb = boto3.client('dynamodb', region_name = region_name)
        s3 = boto3.resource('s3')
        
        object = s3.Object(bucket,path)
        s3_upload = object.put(Body=image,
                        Metadata={'empCode':empCode}
                        )
        
        if s3_upload['ResponseMetadata']['HTTPStatusCode'] ==  200:

            try :                                       
                search_faces_by_image_response = rekognition.search_faces_by_image(
                    Image={
                        "S3Object": {
                            "Bucket": bucket,
                            "Name": path,
                        }
                    },
                    CollectionId=collection_id,
                    FaceMatchThreshold=threshold)
                            
                if search_faces_by_image_response['ResponseMetadata']['HTTPStatusCode'] ==  200:
                    
                    print(search_faces_by_image_response['FaceMatches'])

                    try :               
                        faceId = search_faces_by_image_response['FaceMatches'][0]['Face']['FaceId']

                        dynamodb_response = dynamodb.get_item(
                            TableName=TableName,  
                            Key={'RekognitionId':{'S': faceId}})
                        
                        if dynamodb_response['ResponseMetadata']['HTTPStatusCode'] ==  200 :
                            
                            if dynamodb_response['Item']['empCode']['S']==empCode:
                            
                                return jsonify({"response": "Face verification succeded"}), 200
                            else:
                                return jsonify({'error':"User face does not match with employee ID"}), 404             
                        else:
                            return jsonify({'error':"image not added to index_faces"}), 404
                    except:
                        return jsonify({'error':"face verification failed"}), 404  
                else:
                    return jsonify({'error':"search faces by image not working"}), 404  
            except:
                return jsonify({'error':"image does not contain face"}), 404      
        else:
            return jsonify({'error':"image not uploaded on S3"}), 404      
    except:
        return jsonify({'error':"image not found"}), 404


if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.
    application.debug = True
    application.run()