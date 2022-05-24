import numpy as np
import torch
from transformers import AutoModel, BertTokenizerFast
from kafka import KafkaConsumer
import os
import json
from elasticsearch import Elasticsearch
from uuid import uuid4

from utils.util import clean_tweet, extract_indicator_of_compromise, BERT_Arch

TOPIC_NAME = "TwitterIOC"
KAFKA_SERVER = os.environ["KAFKA_ADDRESS"]
ELASTIC_SERVER= os.environ["ELASTIC_SERVER"]
ELASTIC_PASSWORD = os.environ["ELASTIC_PASSWORD"]
index_name = 'twitter_stream_test_1'

consumer = KafkaConsumer(TOPIC_NAME, bootstrap_servers = KAFKA_SERVER, value_deserializer=lambda m: json.loads(m.decode('utf-8')))


es = Elasticsearch([ELASTIC_SERVER], ca_certs="ca.crt", verify_certs=False, http_auth=('elastic', ELASTIC_PASSWORD,))

mappings = {
  "mappings": {
    "properties": {
      "text": {
        "type": "text"
      }
    }
  }
}

if not es.indices.exists(index=index_name):
    es.indices.create(index=index_name, body=mappings)
    print('created elasticsearch index {}'.format(index_name))



bert = AutoModel.from_pretrained('bert-base-uncased',return_dict=False)
tokenizer = BertTokenizerFast.from_pretrained('bert-base-uncased',return_dict=False)


device = torch.device("cpu")
path = 'saved_weights.pt'
model = BERT_Arch(bert)
model = model.to(device)
model.load_state_dict(torch.load(path, map_location=device))
print('model loaded')


def classify_tweet(tweet):
    text = [tweet]
    sent_id = tokenizer.batch_encode_plus(text, padding=True)
    test_seq = torch.tensor(sent_id['input_ids'])
    test_mask = torch.tensor(sent_id['attention_mask'])
    with torch.no_grad():
      preds = model(test_seq.to(device), test_mask.to(device))
      preds = preds.detach().cpu().numpy()
    preds = np.argmax(preds, axis = 1)
    return preds[0]


def analyze_data(data):
    if data['text'] is None or data['text'] == '':
        print('data is none')
        return
    cleaned_tweet = clean_tweet(data['text'])
    if cleaned_tweet is None:
      return
    print('TWEET: ', data['text'])
    if classify_tweet(cleaned_tweet) == 1:
        print(f'RELEVANT - {data["text"]} \n list of IOCs: ')
        iocs = extract_indicator_of_compromise(data['text'])
        print(iocs)
        id = str(uuid4())
        for ioc in iocs:
          try:
            data_dict = {"ioc": ioc}
            res = es.index(index=index_name, id=id, document=data_dict)
          except Exception as e:
            print('Error : ', e)
    else:
        print('NOT RELEVANT')


for data in consumer:
    
    value = data.value
    print('data is received')

    analyze_data(value)