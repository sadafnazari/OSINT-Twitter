# OSINT-Twitter

We implemented an end-to-end pipeline for detecting 0-day Indicators of compromise (IoC) on Twitter data.
We have collected a large number of tweets by experts in CyberSecurity feild, trained a model to classify if a tweet contains IoC (using transfer learning based on BERT), and implemented a microservice that as input gets streams of tweets, manages them in a Kafka broker, classifies them, and indexes them in Elasticsearch.

# Architecture

