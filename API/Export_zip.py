from label_studio_sdk import Client

class ExportZipProject:
    def __init__(self, url: str, api_key: str, project_id: int):
        self.url = url  # URL do Label Studio
        self.api_key = api_key  # Token de autenticação
        self.project_id = project_id  # ID do projeto
        self.client = Client(url=self.url, api_key=self.api_key)  # Instancia o cliente da API

        print(f"[INFO] ExportZipProject inicializado para o projeto {self.project_id}")

    def export_project(self):
        # Exporta o projeto no formato YOLO
        try:
            print('[ExportZipProject] Conectando ao projeto...')
            project = self.client.get_project(self.project_id)

            print('[INFO] Iniciando exportação no formato YOLO...')
            export_data = project.export(export_type='YOLO')  # Faz a exportação

            print('[INFO] Exportação finalizada com sucesso!')
            return export_data

        except Exception as e:
            print(f"[ERRO] ExportZipProject export_project: {e}")
            raise
