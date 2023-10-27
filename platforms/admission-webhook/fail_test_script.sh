curl -v -k -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "apiVersion": "admission.k8s.io/v1",
    "kind": "AdmissionReview",
    "request": {
      "uid": "12345",
      "object": {
        "kind": "Deployment",
        "metadata": {
          "name": "my-deployment",
          "namespace": "my-namespace"
        },
        "spec": {
          "template": {
            "spec": {
              "containers": [
                {
                  "name": "my-container",
                  "image": "nginx"
                }
              ]
            }
          }
        }
      }
    }
  }' \
  https://0.0.0.0:4430/validate/deployment
