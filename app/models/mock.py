class MockModel:
    def __init__(self, *a, **kw):
        for k, v in kw.items():
            setattr(self, k, v)