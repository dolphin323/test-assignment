class Detector:
    def __init__(self, analyzer):
        self.analyzer = analyzer

    def load_traces(self, service_name):
        traces = self.analyzer.load_traces(service_name)

        return traces

    def detect_n_plus_one(self, traces):
        n_plus_one_issues = self.analyzer.detect_n_plus_one(traces)

        return n_plus_one_issues
