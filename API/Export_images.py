import os
import requests
from label_studio_sdk import Client

class ExportImages:
    def __init__(self, url: str, api_key: str, project_id: int, output_dir: str = 'Dataset'):
        self.url = url  # URL do Label Studio
        self.api_key = api_key  # Token de autenticação
        self.project_id = project_id  # ID do projeto
        self.output_dir = output_dir  # Pasta onde salvar as imagens
        self.client = Client(url=self.url, api_key=self.api_key)  # Cliente da API
        self.headers = {"Authorization": f"Token {self.api_key}"}  # Cabeçalho pra download

        print(f"[INFO] ExportImages inicializado para o projeto {self.project_id}")

    def check_connection(self):
        # Verifica se a conexão com o Label Studio ta ativa
        print('[INFO] Verificando conexão com Label Studio')
        if self.client.check_connection():
            print('[INFO] Conexão bem-sucedida')
        else:
            print(f"[ERRO] ExportImages.check_connection: Não foi possível conectar ao Label Studio")
            raise ConnectionError('Erro de conexão com Label Studio')

    def download_images(self):
        # Baixa todas as imagens do projeto 
        try:
            print(f'[INFO] Iniciando download das imagens do projeto {self.project_id}')
            project = self.client.get_project(self.project_id)
            tasks = project.get_tasks()  # Lista todas as tasks

            images_path = os.path.join(self.output_dir, 'images')
            os.makedirs(images_path, exist_ok=True)  # Cria a pasta se não existir

            for task in tasks:
                image_url = task['data'].get('image')
                if not image_url:
                    print(f"[AVISO] Task {task['id']} sem imagem, ignorada")
                    continue

                if image_url.startswith('/'):
                    image_url = f'{self.url}{image_url}'  # Corrige a URL incompleta

                try:
                    image_data = requests.get(image_url, headers=self.headers).content  # Baixa a imagem
                except Exception as e:
                    print(f"[ERRO] Erro ao baixar {image_url}: {e}")
                    continue

                image_filename = os.path.basename(image_url)  # Extrai o nome do arquivo da URL
                image_path = os.path.join(images_path, image_filename)

                print(f"[DEBUG] Salvando imagem: {image_filename}")
                with open(image_path, 'wb') as f:
                    f.write(image_data)  # Salva a imagem

                print(f'[INFO] Baixada: {image_filename} -> {image_path}')

            print('[INFO] Download finalizado')

        except Exception as e:
            print(f"[ERRO] ExportImages.download_images: {e}")
