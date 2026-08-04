from general_process.SourceProcess import ProcessParams, SourceProcess

class Arnia2024Process(SourceProcess):
    def __init__(self,params:ProcessParams):
        super().__init__("arnia_2024",params=params)

    def _url_init(self):
        super()._url_init()

    def get(self):
        super().get()

    def convert(self):
        super().convert()

    def fix(self):
        super().fix()

