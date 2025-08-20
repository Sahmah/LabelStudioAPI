import os
import shutil
import random
from pathlib import Path

class DataOrganizer:
    def __init__(self, dataset_dir, image_exists=None, split_ratios=None):
        self.dataset_dir = dataset_dir
        self.images_dir = os.path.join(dataset_dir, 'images')  # Pasta das imagens
        self.labels_dir = os.path.join(dataset_dir, 'labels')  # Pasta dos labels
        self.image_exists = image_exists if image_exists else ['.jpg', '.jpeg', '.png']  # Extensões válidas
        self.txt = '.txt'  # Extensão dos labels
        self.split_ratios = split_ratios if split_ratios else {'train': 0.8, 'val': 0.1, 'test': 0.1}  # Proporções

        print(f"[INFO] Inicializando DataOrganizer no diretório: {self.dataset_dir}")

    def start_split(self):
        try:
            print(f"[INFO] Lendo imagens em: {self.images_dir}")
            image_files = self.get_image_files()  # Pega arquivos de imagem válidos
            print(f"[INFO] Encontradas {len(image_files)} imagens")

            print("[INFO] Dividindo dataset")
            train, val, test = self.split_data(image_files)  # Divide o dataset

            print("[INFO] Criando pastas")
            self.create_folders()  # Cria as pastas necessárias

            print("[INFO] Movendo arquivos")
            self.move_data(train, 'train')
            self.move_data(val, 'val')
            self.move_data(test, 'test')

            print("[INFO] Organização concluída!")

        except Exception as e:
            print(f"[ERRO] DataOrganizer.start_split: {e}")

    def get_image_files(self):
        try:
            files = []
            for f in os.listdir(self.images_dir):
                if Path(f).suffix.lower() in self.image_exists:
                    label_filename = Path(f).stem + self.txt
                    label_path = os.path.join(self.labels_dir, label_filename)

                    if os.path.exists(label_path):
                        with open(label_path, 'r') as lbl_file:
                            content = lbl_file.read().strip()

                        if content:
                            files.append(f)
                        else:
                            os.remove(label_path)
                            os.remove(os.path.join(self.images_dir, f))
                            print(f'[AVISO] Removido label vazio e imagem associada: {f}')
                    else:
                        print(f'[AVISO] Imagem sem label: {f} — ignorada.')

            print(f"[DEBUG] Arquivos válidos: {files}")
            return files
        except Exception as e:
            print(f"[ERRO] DataOrganizer.get_image_files: {e}")
            return []

    def split_data(self, files):
        try:
            random.shuffle(files)  # Embaralha arquivos
            total = len(files)
            n_train = int(self.split_ratios['train'] * total)
            n_val = int(self.split_ratios['val'] * total)

            train_set = files[:n_train]  # do início até n_train
            val_set = files[n_train:n_train + n_val]  # do n_train até n_val
            test_set = files[n_train + n_val:]  # o restante 

            print(f"[DEBUG] Train: {len(train_set)}, Val: {len(val_set)}, Test: {len(test_set)}")
            return train_set, val_set, test_set
        except Exception as e:
            print(f"[ERRO] DataOrganizer.split_data: {e}")
            raise

    def create_folders(self):
        try:
            # Cria pastas para imagens e labels dos subsets
            for folder in ['images/train', 'images/val', 'images/test',
                           'labels/train', 'labels/val', 'labels/test']:
                os.makedirs(os.path.join(self.dataset_dir, folder), exist_ok=True)
                print(f"[DEBUG] Pasta pronta: {folder}")
        except Exception as e:
            print(f"[ERRO] DataOrganizer.create_folders: {e}")

    def move_data(self, image_list, subset):
        try:
            for image_file in image_list:
                # Move imagem
                src_img = os.path.join(self.images_dir, image_file)
                dst_img = os.path.join(self.dataset_dir, 'images', subset, image_file)
                shutil.move(src_img, dst_img)
                print(f"[DEBUG] Imagem movida: {image_file}")

                # Move label se existir
                label_file = Path(image_file).stem + self.txt  # .stem retorna o nome do arquivo sem a extensão
                src_lbl = os.path.join(self.labels_dir, label_file)
                if os.path.exists(src_lbl):
                    dst_lbl = os.path.join(self.dataset_dir, 'labels', subset, label_file)
                    shutil.move(src_lbl, dst_lbl)
                    print(f"[DEBUG] Label movido: {label_file}")
                else:
                    print(f"[AVISO] Label não encontrado: {label_file}")
        except Exception as e:
            print(f"[ERRO] DataOrganizer.move_data: {e}")
