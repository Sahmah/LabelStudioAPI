import shutil
import uuid
from pathlib import Path
import json


class DatasetConcatenator:
    def __init__(self, project_ids, output_dir, final_project_name='Dataset_concatenado', dataset_dir='.'):
        # Diretório onde os datasets estão
        self.dataset_dir = Path(dataset_dir)
        # Lista de IDs de projetos que vão ser concatenados
        self.project_ids = project_ids
        # Diretório onde o novo dataset vai ser salvo
        self.output_dir = Path(output_dir)
        # Nome base para o novo dataset
        self.final_project_name = final_project_name
        # Cria um nome único com UUID baseado nos IDs
        ids = "_".join(str(id) for id in self.project_ids)
        self.output_dataset_path = self.output_dir / f'{self.final_project_name}_{ids}_{uuid.uuid4().hex[:5]}'
        # Define os diretórios padrão de split
        self.splits = ['train', 'val', 'test']
        # Flag para saber se o diretório foi realmente criado
        self.output_dataset_path_created = False

    def create_dirs(self):
        try:
            # Cria as pastas para cada split (train, val, test) imagens e labels
            for split in self.splits:
                (self.output_dataset_path / 'images' / split).mkdir(parents=True, exist_ok=True)
                (self.output_dataset_path / 'labels' / split).mkdir(parents=True, exist_ok=True)
            self.output_dataset_path_created = True  # Marca que a pasta foi criada com sucesso
        except Exception as e:
            # Registra o erro se falhar ao criar diretórios
            print(f"[ERRO] Falha ao criar diretórios: {e}")

    def find_project_path(self, project_id):
        # Busca o caminho da pasta de um projeto com base no ID final do nome da pasta
        for folder in self.dataset_dir.iterdir():
            if folder.is_dir() and folder.name.endswith(f'_{project_id}'):
                return folder  # Retorna o caminho se encontrado

        # Caso não encontre loga um aviso
        warning = f'Pasta do projeto {project_id} não encontrada!'
        print(f'[AVISO] {warning}')
        return None

    def copy_data(self, images, labels, des_images, des_labels, project_id):
        # Copia os arquivos de imagem e label renomeando com o ID
        for img_file in images.glob('*.*'):
            new_name = f'{project_id}_{img_file.name}'
            shutil.copy2(img_file, des_images / new_name)

        for lb_file in labels.glob('*.*'):
            new_name = f'{project_id}_{lb_file.name}'
            shutil.copy2(lb_file, des_labels / new_name)

    def split_process(self, project_path, split, project_id):
        # Define os caminhos de origem e destino para cada split (train, test, val)
        images = project_path / 'images' / split
        labels = project_path / 'labels' / split
        des_images = self.output_dataset_path / 'images' / split
        des_labels = self.output_dataset_path / 'labels' / split 

        # Se existirem os diretórios de origem faz a cópia
        if images.exists() and labels.exists():
            self.copy_data(images, labels, des_images, des_labels, project_id)
    
    def merge_metadata_files(self, ids_validos):
        merged_classes = []
        class_mapping = {}
        normalized_class_map = {} # Mapeia o nome original
        class_index_counter = 0
        final_info = None  # Armazena apenas um bloco "info" (do primeiro projeto)

        for project_id, project_path in ids_validos:
            # Lê classes.txt
            classes_file = project_path / 'classes.txt'
            if classes_file.exists():
                with open(classes_file, 'r', encoding='utf-8') as f:
                    classes = [line.strip() for line in f.readlines()]

                for idx, cls in enumerate(classes):
                    normalized = cls.strip().lower()
                    if normalized not in normalized_class_map:
                        # Primeira vez que a categoria aparece
                        normalized_class_map[normalized] = cls # Salva o nome original
                        merged_classes.append(cls)
                        class_mapping[(project_id, idx)] = class_index_counter
                        class_index_counter += 1
                    else:
                        # A categoria ja existente
                        existing_cls = normalized_class_map[normalized]
                        new_idx = merged_classes.index(existing_cls)
                        class_mapping[(project_id, idx)] = new_idx

            # Lê notes.json pra extrair "info" (uma vez só)
            notes_file = project_path / 'notes.json'
            if final_info is None and notes_file.exists():
                with open(notes_file, 'r', encoding='utf-8') as f:
                    notes = json.load(f)
                    final_info = notes.get("info", {
                        "year": 2025,
                        "version": "1.0",
                        "contributor": "Label Studio"
                    })

        # Atualiza os arquivos de label com os índices novos
        for split in self.splits:
            labels_dir = self.output_dataset_path / 'labels' / split
            for label_file in labels_dir.glob('*.txt'):
                project_id_str = label_file.name.split('_')[0]
                try:
                    project_id = int(project_id_str)
                except ValueError:
                    continue
                updated_lines = []
                with open(label_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        parts = line.strip().split()
                        if not parts:
                            continue
                        old_class = int(parts[0])
                        new_class = class_mapping.get((project_id, old_class))
                        if new_class is None:
                            continue
                        parts[0] = str(new_class)
                        updated_lines.append(' '.join(parts))
                with open(label_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(updated_lines))

        # Escreve o novo classes.txt
        with open(self.output_dataset_path / 'classes.txt', 'w', encoding='utf-8') as f:
            for cls in merged_classes:
                f.write(cls + '\n')

        # Gera a estrutura correta do notes.json
        final_notes = {
            "categories": [{"id": i, "name": name} for i, name in enumerate(merged_classes)],
            "info": final_info or {
                "year": 2025,
                "version": "1.0",
                "contributor": "Label Studio"
            }
        }

        with open(self.output_dataset_path / 'notes.json', 'w', encoding='utf-8') as f:
            json.dump(final_notes, f, indent=4, ensure_ascii=False)

        print("[LOG] Metadados mesclados com sucesso.")

    def concatenate(self):
        # Listas para guardar os IDs válidos e inválidos
        ids_validos = []
        ids_invalidos = []

        # Verifica se cada ID tem uma pasta correspondente
        for id in self.project_ids:
            project_path = self.find_project_path(id)
            if project_path is None:
                ids_invalidos.append(id)
            else:
                ids_validos.append((id, project_path))

        # Se digitar IDs inválidos mostra no console
        if ids_invalidos:
            msg = f'IDs inválidos ignorados: {ids_invalidos}'
            print(f'\n[AVISO] {msg}')

        # Só continua se houver ao menos 2 projetos (IDs) válidos
        if len(ids_validos) < 2:
            msg = 'Concatenação cancelada: menos de dois projetos válidos encontrados.'
            print(f'\n[ERRO] {msg}')
            return None

        # Mostra quais IDs válidos serão concatenados
        print(f'\n[OK] Iniciando a concatenação dos projetos válidos: {[id for id, _ in ids_validos]}')

        try:
            self.create_dirs()  # Cria os diretórios de destino

            # Para cada ID válido, processa seus splits (train, val, test)
            for id, project_path in ids_validos:
                for split in self.splits:
                    self.split_process(project_path, split, id)

            # Registra o sucesso
            print(f'[OK] Concatenação finalizada com sucesso: {self.output_dataset_path}')
            self.merge_metadata_files(ids_validos)
            return self.output_dataset_path

        except Exception as e:
            # Se qualquer erro ocorrer, mostra no console
            print(f"[ERRO] Falha na concatenação: {e}")
            return None
