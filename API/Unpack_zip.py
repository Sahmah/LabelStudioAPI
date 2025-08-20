import os
import zipfile

class UnpackZip:
    def __init__(self, zip_path: str, extract_to: str = 'Dataset'):
        self.zip_path = zip_path  # Caminho do arquivo .zip
        self.extract_to = extract_to  # Diretório onde os arquivos serão extraídos

    def extract(self):
        # Verifica se o arquivo ZIP existe
        if not os.path.exists(self.zip_path):
            raise FileNotFoundError(f'[UnpackZip] Arquivo ZIP não encontrado: {self.zip_path}')

        # Garante que o diretório de extração existe
        os.makedirs(self.extract_to, exist_ok=True)
        print(f"[UnpackZip] Descompactando {self.zip_path} para {self.extract_to}...")

        try:
            # Abre o arquivo zip e extrai todo o conteúdo
            with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.extract_to)

            print("[UnpackZip] Descompactação concluída")

        except Exception as e:
            print(f"[UnpackZip] Erro ao descompactar: {e}")
            raise
