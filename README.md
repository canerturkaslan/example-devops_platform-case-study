## Dream Games Case Study

### Step 1 : Flask-App

I don't know much about Java, when I looked at the repository on github, I realized that someone else had fork here and solved the case. I chose to develop from scratch using Python so that the things we do are not the same. 

All the steps are as requested, I have written the Dockerfile in multistage structure and returned the parameters of the query to the endpoint to stdout.

### Step 2.1 Kubernetes Cluster:

I created Kubernetes with vagrantfile on my local computer using Libvirt(KVM/QEMU). 

Master and worker nodes each have 2 CPUs.  
Master node has 4096MB ram, worker nodes have 5192 MB ram.

Kubernetes version 1.26.0 was installed using kubeadm and shell scripts.

Containerd is selected as the container runtime, calico is selected as the Container network interface plugin.

#TODO OPTIMIZATION AND TUNING PERFORMANCE, CONFIG FILE CHANGES FOR METRICS

### Step 2.2 Jenkins :

I installed Jenkins by customizing helm chart values.yaml and giving nodeSelector-label to run on **NODE 3** only.  
I used localPath for persistentVolume (jenkinsData).

### Step 2.3 Prometheus-Alertmanager-Grafana Stack :

I made customizations with the kube-prometheus-stack community chart and installed it with values.yaml.  
Here, I created the application's grafana dashboards with configmap and made it permanent.

### Step 2.4 Elasticsearch, Kibana, Fluent-bit:

Using elastic/elasticsearch, elastic/kibana and fluent/fluen-bit helm charts, I have set up an EFK stack with values.yamls separately. 

I installed Elasticsearch as 1 node with master-ingest-data roles. (due to lack of resources)

When I tried to install with default values, my computer froze and most of what I did was wasted.

### Step 2.4.a

I created the "fluent-bit" index written by fluent-bit via kibana.

### Step 2.4.b

Here I made settings such as xpack security and certificates and made it permanent. (to see if it works as a result of restarts.)

### Step 2.4.c Log Rotate, Elasticsearch :

I would like to suggest two different approaches to the problem here.  
First, it is possible to write log files to filesystem instead of stdout in any language.  
Required libraries and sample codes can be found. I am giving an example in python.

```python
import logging
from flask import Flask

app = Flask(__name__)

log_file = "/app/logs/app.log"

logger = logging.getLogger("flask-app")
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)

@app.route("/")
def hello():
    logger.info("Hello, World!")
    return "Hello, World!"

if __name__ == "__main__":
    app.run()
```

*   **Filebeat Sidecar Architecture**

I am using Python's logging module. I create the logger object and define the file\_handler that will write to the log file. I specify the location of the log file and the log level (setLevel) in file\_handler. Next, I create a formatter that determines how the log messages will be formatted and pass this formatter to the file\_handler.

With logger.addHandler(file\_handler) I add file\_handler to the logger object so that log messages are written to the log file.

In this example, I'm having log messages written to /app/logs/app.log instead of stdout. Thus, we can work integrated with Filebeat, which controls the log file size and performs log rotation.

Filebeat must be in the same pod as the application container (sidecar)  
It can read these files over a same mountPath volume.  
Of course, technologies such as nfs or cephfs should not be used, as it will make network calls again, which will lead to a great loss of performance.  
(This is why we encountered an incident in Türk Telekom.) here I suggest to use localpath or block volume as persistentVolume

```plaintext
    spec:
      containers:
        - name: flask-app
          image: flask-app/hello
          ports:
            - containerPort: 80
          volumeMounts:
            - name: app-logs
              mountPath: /app/logs
        - name: filebeat-sidecar
          image: docker.elastic.co/beats/filebeat:7.5.0
          volumeMounts:
            - name: app-logs
              mountPath: /app/logs
            - name: filebeat-config
              mountPath: /usr/share/filebeat/filebeat.yml
              subPath: filebeat.yml 
      volumes:
        - name: app-logs
        - name: filebeat-config
          configMap:
            name: filebeat-configmap
            items:
              - key: filebeat.yml
                path: filebeat.yml
```

```plaintext
filebeat.inputs:
- type: log
  paths:
    - /app/logs/*.log
  fields:
    app_name: flask-app
  close_inactive: 5m
  clean_inactive: 24h
  clean_removed: true
  harvester_buffer_size: 16mb
  max_bytes: 1gb
  rotate_every_bytes: 1gb

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  index: "flask-app_logs-%{+yyyy.MM.dd}"

logging.level: info
```

*   **Logstash S3 Architecture**

In this example, it uploads the log file to S3 by checking the size of the log file and rotating it if it exceeds the maximum 1GB.  
A function named rotate\_log\_file is defined. This function performs the rotation of the log file. It rotates the original log file with a new name and uploads the rotated file to S3. If the rotate operation is successful, the rotated file is deleted.

```python
import os
import logging
import boto3
from botocore.exceptions import ClientError

from flask import Flask

app = Flask(__name__)

log_file = "/app/logs/app.log"

s3_bucket = "flask-app-logs"
s3_key_prefix = "log-files/"

# 1GB
max_log_file_size = 1024 * 1024 * 1024


logger = logging.getLogger("flask-app")
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)

def upload_log_file_to_s3(log_file_path, s3_bucket, s3_key):
    s3_client = boto3.client("s3")
    try:
        s3_client.upload_file(log_file_path, s3_bucket, s3_key)
        return True
    except ClientError as e:
        logger.error("Failed to upload log file to S3: %s", str(e))
        return False

def rotate_log_file(log_file_path):
    rotated_file_path = log_file_path + ".old"
    os.rename(log_file_path, rotated_file_path)

    s3_key = s3_key_prefix + os.path.basename(rotated_file_path)
    if upload_log_file_to_s3(rotated_file_path, s3_bucket, s3_key):
        os.remove(rotated_file_path)

@app.route("/")
def hello():
    logger.info("Hello, World!")

    if os.path.getsize(log_file) > max_log_file_size:
        rotate_log_file(log_file)

    return "Hello, World!"

if __name__ == "__main__":
    app.run()
```

For a longer storage or analysis afterwards; With logstash, we can get log files in the format and size we want. An example can be given as input s3 output as elasticsearch.

```plaintext
input {
  s3 {
    bucket => "flask-app-logs"
    access_key_id => ""
    secret_access_key => ""
    region => "eu-west2"
    prefix => "log-files/"
    type => "logs"
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "flask-app-logs-%{+YYYY.MM.dd}"
  }
}
```