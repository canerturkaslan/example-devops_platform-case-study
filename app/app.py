from flask import Flask, request

from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
metrics = PrometheusMetrics(app)


@app.route('/api')
def print_query_parameters():
    query_parameters = request.args
    
    for key, values in query_parameters.items():
        print(f"{key}: {values}")

    return "Query parameters printed in the console."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)