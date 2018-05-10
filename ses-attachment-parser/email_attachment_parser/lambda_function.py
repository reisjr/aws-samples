import boto3
import os
import json
import uuid
import traceback
import sys
import base64
import email
import urllib
import re

'''
Read an email, find CSV attachments and save each attachment (CSV) on the destination bucket.
'''

S3_WORK_BUCKET = os.environ['S3_WORK_BUCKET']
S3_PROCESSED_FOLDER = os.environ['S3_PROCESSED_FOLDER']
S3_CSV_FOLDER = os.environ['S3_CSV_FOLDER']

s3 = boto3.client('s3')


def extract_folder(key):
    return extract_key_paths(key, 1)


def extract_object_key(key):
    return extract_key_paths(key, 2)


def extract_key_paths(key, group_number):
    p = re.compile('(.*)/(.*)')
    m = p.match(key)
    return m.group(group_number)


def is_csv(cname):
    return cname is not None and cname.upper().endswith('.CSV')


def copy_file_to_s3(filename):
    tmp_file = '/tmp/{}'.format(filename)
    s3_dest = "{}/{}".format(S3_CSV_FOLDER, filename)
    
    print("Copying '{}' to '{}'...".format(tmp_file, s3_dest))
    s3.upload_file(tmp_file, S3_WORK_BUCKET, s3_dest)


def move_file_to_processed(bucket, key):
    filename = extract_object_key(key)
    s3_dst_key = "{}/{}".format(S3_PROCESSED_FOLDER, filename)
    s3_src_url = "{}/{}".format(bucket, key) 

    print("Moving file from 's3://{}/{}' to 's3://{}/{}'...".format(bucket, key, bucket, s3_dst_key))

    s3_res = boto3.resource('s3')
    s3_res.Object(bucket, s3_dst_key).copy_from(CopySource=s3_src_url)
    s3_res.Object(bucket, key).delete()


def delete_temp_file(filename):
    print("Removing temp file '/tmp/{}'...".format(filename))
    os.remove("/tmp/{}".format(filename))


def lambda_handler(event, context): 
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.unquote_plus(event['Records'][0]['s3']['object']['key']).decode('utf8')
    csv_found = False

    try:
        print("Processing file s3://{}/{}".format(bucket, key))
        response = s3.get_object(Bucket=bucket, Key=key)
        body = response['Body']
        msg = email.message_from_string(body.read())
        
        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                cname = part.get_filename()
                print("Attachment Type: {} Name: {}".format(ctype, cname))
                
                if is_csv(cname):
                    csv_found = True
                    filename = str(uuid.uuid4()) + ".csv"
                    print("Saving data in '/tmp/{}' ...".format(filename))
                    open('/tmp/{}'.format(filename), 'wb').write(part.get_payload(decode=True))
                    copy_file_to_s3(filename)
                    delete_temp_file(filename)
                else:
                    print("Ignoring part")
                
        else:
            print("Not a multipart email.")
        
        # Move file from staging folder to processed folder
        move_file_to_processed(bucket, key)
        
    except Exception as e:
        print("Error processing file 's3://{}/{}'.".format(bucket, key))
        traceback.print_exc(file=sys.stdout)
        raise e

    return "Found CSV in e-mail: {}".format(csv_found)