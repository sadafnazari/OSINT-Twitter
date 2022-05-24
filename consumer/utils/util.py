import re
from iocextract import extract_iocs, extract_hashes
from langdetect import detect
import torch.nn as nn


def clean_tweet(tweet): 
  temp = tweet.lower()
  temp = temp.replace('\n', ' ')
  temp = re.sub("@[A-Za-z0-9_]+","", temp)
  temp = re.sub("#","", temp)
  for ioc in extract_iocs(temp):
      temp = temp.replace(ioc, '')
  temp = re.sub("[^a-z0-9]"," ", temp)
  temp = temp.split()
  temp = " ".join(word for word in temp)
  if len(temp) == 0:
      return
  return temp


def extract_indicator_of_compromise(tweet):
  list_of_incdicators = ['[.', '(.)', '\.', '{.}', '[@]', '(@)', '{@}', ':\\', 'hxxp', '[/]']
  iocs = []
  for ioc in extract_iocs(tweet):
    for real_ioc in list_of_incdicators:
      if real_ioc in ioc:
        iocs.append([x for x in extract_iocs(ioc, refang=True)][0])
  for ioc in extract_hashes(tweet):
    iocs.append(ioc)
  ioc_set = set(iocs)
  return list(ioc_set)


class BERT_Arch(nn.Module):

    def __init__(self, bert):
      
      super(BERT_Arch, self).__init__()

      self.bert = bert 
      
      # dropout layer
      self.dropout = nn.Dropout(0.1)
      
      # relu activation function
      self.relu =  nn.ReLU()

      # dense layer 1
      self.fc1 = nn.Linear(768,512)
      
      # dense layer 2 (Output layer)
      self.fc2 = nn.Linear(512,2)

      #softmax activation function
      self.softmax = nn.LogSoftmax(dim=1)

    #define the forward pass
    def forward(self, sent_id, mask):

      #pass the inputs to the model  
      _, cls_hs = self.bert(sent_id, attention_mask=mask)
      
      x = self.fc1(cls_hs)

      x = self.relu(x)

      x = self.dropout(x)

      # output layer
      x = self.fc2(x)
      
      # apply softmax activation
      x = self.softmax(x)

      return x