import os
import requests
import glob
from Export_images import ExportImages
from Export_zip import ExportZipProject
from Unpack_zip import UnpackZip
from Dataset_organization import DataOrganizer
from Dataset_Concatenator import DatasetConcatenator
from Filters_treatment import DatasetFilter

class SystemController:
    def __init__(self, api_key: str, url: str = ''):
        self.api_key = api_key
        self.url = url
        print(f"[INFO] Inicializando com URL definida")

    def list_projects(self):
        headers = {"Authorization": f"Token {self.api_key}"}
        url = f"{self.url}/api/projects/"
        all_projects = []
        while url:
            response = requests.get(f"{self.url}/api/projects/", headers=headers)

            print("[INFO] Requisição enviada para listar projetos")

            if response.status_code != 200:
                print("[ERRO] Erro ao buscar projetos")
                raise Exception('[SystemController] Erro ao buscar os projetos')

            projects = response.json()

            if not isinstance(projects, dict) or "results" not in projects:
                print("[ERRO] Estrutura inesperada ao buscar projetos")
                raise Exception("[SystemController] Estrutura inesperada. Esperado dict com chave 'results'!")

            all_projects.extend(project["results"])  # Junta os resultados
            
            url = project.get("next")
            
            print("[INFO] Projetos listados com sucesso ou nenhum ID foi digitado")
            for project in all_projects:
                print(f"ID: {project['id']} | Nome: {project['title']}")
        return all_projects

    def start_exportation(self, selected_ids, auto_concatenate=False):
        exported_ids = []

        for project_id in selected_ids:
            print(f"[INFO] Iniciando exportação do projeto {project_id}")
            try:
                # Salva o dataset extraído com o nome do projeto original
                project_info = self.get_project_info(project_id)
                project_name = project_info['title'].replace(" ", "_").replace("/", "_")
                self.output_dir = f'Dataset_{project_name}_{project_id}'

                # Inicializa exportador e downloader
                exporter = ExportZipProject(self.url, self.api_key, project_id)
                downloader = ExportImages(self.url, self.api_key, project_id, self.output_dir)

                # Exporta os dados do projeto como ZIP
                export_data = exporter.export_project()

                # Verifica se o ZIP foi salvo corretamente
                if isinstance(export_data, str) and export_data.endswith('.zip') and os.path.exists(export_data):
                    zip_file = export_data
                else:
                    print("[AVISO] Caminho ZIP inválido ou não encontrado, tentando localizar arquivo mais recente...")
                    zip_file = self.search_zip_file()

                # Descompacta o ZIP baixado
                extractor = UnpackZip(zip_path=zip_file, extract_to=self.output_dir)
                extractor.extract()

                # Verifica conexão e baixa imagens
                downloader.check_connection()
                downloader.download_images()

                # Divide dataset em treino, validação e teste
                splitter = DataOrganizer(dataset_dir=self.output_dir)
                splitter.start_split()

                print(f'[OK] Exportação do projeto {project_id} concluída')
                exported_ids.append(project_id)

            except Exception as e:
                print(f'[ERRO] Falha ao exportar o projeto {project_id}: {e}')
            
        if not exported_ids:
            print("[ERRO] Nenhum projeto foi exportado com sucesso")
            return

        # Pergunta ao usuário se deseja concatenar os projetos extraídos
        if auto_concatenate:
            try:
                # Inicia concatenador de datasets
                concatenator = DatasetConcatenator(
                    project_ids=exported_ids,
                    output_dir='Dataset_concatenado',
                    final_project_name='Dataset'
                )
                path = concatenator.concatenate()
                print(f'\n[OK] Dataset concatenado salvo em: {path}')
            except Exception as e:
                print(f"[ERRO] Erro ao concatenar datasets: {e}")
        else:
            resposta = input('\nDeseja concatenar os projetos extraídos? (s/n): ').strip().lower()
            if resposta == 's':
                self.concatenate_datasets()
                
    def concatenate_datasets(self):
        print("Digite os IDs dos projetos que deseja concatenar, aperte ENTER para digitar outro ID (digite 'q' após escolher os IDs):")
        ids_to_concat = []
        while True:
            ids_input = input('>').strip()
            if ids_input.lower() == 'q':
                break
            if ids_input.isdigit():
                ids_to_concat.append(int(ids_input))
            else:
                print("Entrada inválida. Digite apenas um número ou 'q' para sair")

        if not ids_to_concat:
            print("[ERRO] Nenhum ID válido informado")
            return
        try:
            # Cria concatenador com os IDs digitados
            concatenator = DatasetConcatenator(
                project_ids=ids_to_concat,
                output_dir='Dataset_concatenado',
                final_project_name='Dataset'
            )
            path = concatenator.concatenate()
            print(f'\n[OK] Dataset concatenado salvo em: {path}')
        except Exception as e:
            print(f"[ERRO] Erro ao concatenar: {e}")

    def get_project_info(self, project_id):
        headers = {"Authorization": f"Token {self.api_key}"}
        response = requests.get(f"{self.url}/api/projects/{project_id}", headers=headers)
        if response.status_code != 200:
            print(f"[ERRO] Falha ao obter informações do projeto {project_id}")
            raise Exception(f'[SystemController] Não foi possível obter as informações do projeto {project_id}')
        return response.json()

    def search_zip_file(self):  # Só acontece se exportação falhar em retornar o caminho certo do zip 
        # Busca o .zip mais recente no diretório atual
        zip_files = [f for f in os.listdir('.') if f.endswith('.zip')]
        if not zip_files:
            print("[ERRO] Nenhum arquivo .zip encontrado no diretório atual")
            raise FileNotFoundError('[SystemController] Nenhum arquivo .zip encontrado no diretório atual')
        latest_zip = max(zip_files, key=os.path.getmtime)
        print(f"[INFO] ZIP mais recente localizado: {latest_zip}")
        return latest_zip
    
    def run_dataset_filter_menu(self):
        try:
            print("\nDigite o ID do dataset extraído (ex: 60 ou 60_61):")
            dataset_id = input('>').strip()

            if not dataset_id.replace("_", "").isdigit():
                print("ID inválido. Digite apenas números ou números separados por underline (ex: 60 ou 60_61).")
                return

            filtro = DatasetFilter(dataset_id, base_path=os.getcwd())
            print(f"Dataset encontrado: {filtro.dataset_path}")
            filtro.run_menu()

        except Exception as e:
            print(f"[ERRO] Erro ao tentar rodar menu de filtro do dataset: {e}")
    
if __name__ == "__main__":
    controller = SystemController(
        api_key='',
        url='',
    )

    while True:
        print("\nDeseja:\n 1) Extrair projetos?\n 2) Apenas concatenar projetos já extraídos?\n 3) Aplicar filtros em dataset extraído\n 4) Sair")
        op = input("Escolha (1/2/3/4): ").strip()

        if op == '1':
            projects = controller.list_projects()
            selected_ids = []
            print("\nDigite os IDs dos projetos que deseja exportar, aperte ENTER para digitar outro ID (digite 'q' após escolher os IDs):")
            while True:
                user_input = input('>').strip()
                if user_input.lower() == 'q':
                    break
                if user_input.isdigit():
                    selected_ids.append(int(user_input))
                else:
                    print("Entrada inválida. Por favor, digite apenas número ou 'q'!")

            res = input("Deseja concatenar os projetos após a extração? (s/n): ").strip().lower()
            auto_concat = True if res == 's' else False
            controller.start_exportation(selected_ids, auto_concatenate=auto_concat)

        elif op == '2':
            controller.concatenate_datasets()

        elif op == '3':
            controller.run_dataset_filter_menu()

        elif op == '4':
            print("Encerrando...")
            break

        else:
            print("Opção inválida. Tente novamente.")
