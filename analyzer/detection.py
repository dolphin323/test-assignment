import logging
from analyzer.jaeger_analyzer import JaegerAnalyzer


def analyze_traces(service_name, analyzer):
    traces = analyzer.load_traces(service_name)
    n_plus_one_issues = analyzer.detect_n_plus_one(traces)
    return {
        "n_plus_one_issues": n_plus_one_issues,
    }


if __name__ == "__main__":
    analyzer = JaegerAnalyzer()
    service_name = "cat-api"
    issues = analyze_traces(service_name, analyzer)
    for issue in issues["n_plus_one_issues"]:
        print(f"Detected issue n_plus_one_issues: {issue}")
