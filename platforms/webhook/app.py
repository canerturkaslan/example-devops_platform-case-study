from flask import Flask, request, abort
import json
import ssl

app = Flask(__name__)


@app.route("/validate/deployment", methods=["POST"])
def validate_deployment():
    # Parse the admission review request
    admission_review = json.loads(request.data)
    request_object = admission_review["request"]
    resource = request_object["object"]

    # Check if the resource is a Deployment
    if resource["kind"] == "Deployment":
        # Check if resource requests are specified
        spec = resource.get("spec", {})
        containers = spec.get("template", {}).get("spec", {}).get("containers", [])
        for container in containers:
            if not container.get("resources", {}).get("requests"):
                # Return an error response if resource requests are missing
                return {
                    "apiVersion": "admission.k8s.io/v1",
                    "kind": "AdmissionReview",
                    "response": {
                        "allowed": False,
                        "uid": request_object['uid'],
                        "status": {
                            "code": 400,
                            "message": "Resource requests must be specified for containers in the deployment."
                        }
                    }
                }

    # Return a success response if the deployment is valid
    return {
        "apiVersion": "admission.k8s.io/v1",
        "kind": "AdmissionReview",
        "response": {
            "allowed": True,
            "uid": request_object['uid'],
            "status": {
                "code": 200,
                "message": "Deployment is valid."
            }
        }
    }

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4430, ssl_context=("certs/webhook.crt", "certs/ca.key"))
