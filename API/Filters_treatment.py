import os
import glob
import cv2
import shutil
import numpy as np
import re
from collections import Counter, defaultdict
from PIL import Image, ImageEnhance

class DatasetFilter:
    def __init__(self, dataset_id, base_path='.'):
        # Encontra a pasta do dataset a partir do ID informado
        self.dataset_path = self.find_dataset_path(dataset_id, base_path)
        if not self.dataset_path:
            print(f"[ERRO] Nenhum dataset com ID {dataset_id} encontrado em {base_path}")
            raise ValueError(f"Nenhum dataset com ID {dataset_id} encontrado em {base_path}")
        print(f"[INFO] DatasetFilter iniciando para dataset: {self.dataset_path}")

    def find_dataset_path(self, dataset_id, base_path):
        if isinstance(dataset_id, str):
            ids_desejados = dataset_id.split('_')
        else:
            ids_desejados = [str(dataset_id)]

        # Se forem múltiplos IDs busca em Dataset_concatenado
        if len(ids_desejados) > 1:
            concat_path = os.path.join(base_path, 'Dataset_concatenado')
            if os.path.exists(concat_path):
                for nome in os.listdir(concat_path):
                    total_path = os.path.join(concat_path, nome)
                    if not os.path.isdir(total_path):
                        continue
                    ids_encontrados = re.findall(r'\d+', nome)
                    if all(id_ in ids_encontrados for id_ in ids_desejados):
                        return os.path.join(concat_path, nome)

        # Se for só um ID busca na raiz
        for nome in os.listdir(base_path):
            if not os.path.isdir(os.path.join(base_path, nome)):
                continue
            ids_encontrados = re.findall(r'\d+', nome)
            if ids_desejados[0] in ids_encontrados:
                return os.path.join(base_path, nome)

        print(f"[ERRO] Nenhum dataset com ID(s) {ids_desejados} encontrado.")
        return None

    def list_resolutions(self):
        print(f"\n[INFO] Analisando resoluções em: {self.dataset_path}")
        caminhos = glob.glob(os.path.join(self.dataset_path, 'images', '**', '*.*'), recursive=True)
        resolucoes = Counter()
        total = 0

        for img_path in caminhos:
            if img_path.lower().endswith(('.jpg', '.jpeg', '.png')):
                img = cv2.imread(img_path)
                if img is not None:
                    h, w = img.shape[:2]
                    resolucoes[(w, h)] += 1
                    total += 1
            else:
                print(f"[ERRO] Falha ao ler: {img_path}")

        if not resolucoes:
            print("[INFO] Nenhuma imagem encontrada")
        else:
            print("\n[RESOLUÇÕES ENCONTRADAS]")
            for res, count in resolucoes.items():
                print(f"{res[0]}x{res[1]}: {count} imagens")

    def resolution_organizer(self):
        print(f'\n[INFO] Organizando as imagens por resolução: {self.dataset_path}')
        caminhos = glob.glob(os.path.join(self.dataset_path, 'images', '**', '*.*'), recursive=True)
        caminhos = [p for p in caminhos if p.lower().endswith(('.jpg', '.jpeg', '.png'))]

        output_dir = os.path.join(self.dataset_path, 'resolucoes_organizadas')
        os.makedirs(output_dir, exist_ok=True)

        total = 0
        for img_path in caminhos:
            img = cv2.imread(img_path)
            if img is not None:
                h, w = img.shape[:2]
                nome_resolucao = f'{w}x{h}'

                subdir = os.path.relpath(img_path, os.path.join(self.dataset_path, 'images')).split(os.sep)[0]
                img_dest_dir = os.path.join(output_dir, nome_resolucao, 'images', subdir)
                ext = os.path.splitext(img_path)[1].lower()
                label_src_path = img_path.replace(os.sep + 'images' + os.sep, os.sep + 'labels' + os.sep).replace(ext, '.txt')
                label_dest_dir = os.path.join(output_dir, nome_resolucao, 'labels', subdir)

                os.makedirs(img_dest_dir, exist_ok=True)
                os.makedirs(label_dest_dir, exist_ok=True)

                shutil.copy2(img_path, os.path.join(img_dest_dir, os.path.basename(img_path)))
                if os.path.exists(label_src_path):
                    shutil.copy2(label_src_path, os.path.join(label_dest_dir, os.path.basename(label_src_path)))
                else:
                    print(f"[INFO] Label não encontrada para {img_path}")

                total += 1
            else:
                print(f"[ERRO] Falha ao ler: {img_path}")

        print(f'[INFO] {total} imagens organizadas por resolução em: {output_dir}')

    def apply_grayscale(self):
        print(f"\n[INFO] Aplicando filtro grayscale em: {self.dataset_path}")
        caminhos = glob.glob(os.path.join(self.dataset_path, 'images', '**', '*.*'), recursive=True)
        caminhos = [p for p in caminhos if p.lower().endswith(('.jpg', '.jpeg', '.png'))]
        output_dir = os.path.join(self.dataset_path, 'grayscale')
        os.makedirs(output_dir, exist_ok=True)

        for img_path in caminhos:
            img = cv2.imread(img_path)
            if img is not None:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                nome = os.path.relpath(img_path, os.path.join(self.dataset_path, 'images'))
                out_path = os.path.join(output_dir, nome)
                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                cv2.imwrite(out_path, gray)
            else:
                print(f"[ERRO] Falha ao processar: {img_path}")

        print(f"[INFO] Todas as imagens salvas em: {output_dir}")

    def apply_threshold(self):
        print(f"\n[INFO] Aplicando filtro threshold em: {self.dataset_path}")
        caminhos = glob.glob(os.path.join(self.dataset_path, 'images', '**', '*.*'), recursive=True)
        caminhos = [p for p in caminhos if p.lower().endswith(('.jpg', '.jpeg', '.png'))]
        output_dir = os.path.join(self.dataset_path, 'threshold')
        os.makedirs(output_dir, exist_ok=True)

        for img_path in caminhos:
            img = cv2.imread(img_path)
            if img is not None:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                _, treshold = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
                nome = os.path.relpath(img_path, os.path.join(self.dataset_path, 'images'))
                out_path = os.path.join(output_dir, nome)
                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                cv2.imwrite(out_path, treshold)
            else:
                print(f"[ERRO] Falha ao processar: {img_path}")

        print(f"[INFO] Todas as imagens salvas em: {output_dir}")

    def apply_threshold_inv(self):
        print(f"\n[INFO] Aplicando filtro threshold invertido em: {self.dataset_path}")
        caminhos = glob.glob(os.path.join(self.dataset_path, 'images', '**', '*.*'), recursive=True)
        caminhos = [p for p in caminhos if p.lower().endswith(('.jpg', '.jpeg', '.png'))]
        output_dir = os.path.join(self.dataset_path, 'threshold_invertido')
        os.makedirs(output_dir, exist_ok=True)

        for img_path in caminhos:
            img = cv2.imread(img_path)
            if img is not None:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                _, threshold = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
                nome = os.path.relpath(img_path, os.path.join(self.dataset_path, 'images'))
                out_path = os.path.join(output_dir, nome)
                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                cv2.imwrite(out_path, threshold)
            else:
                print(f"[ERRO] Falha ao processar: {img_path}")

        print(f"[INFO] Todas as imagens salvas em: {output_dir}")

    def apply_canny(self):
        print(f"\n[INFO] Aplicando filtro Canny em: {self.dataset_path}")
        caminhos = glob.glob(os.path.join(self.dataset_path, 'images', '**', '*.*'), recursive=True)
        caminhos = [p for p in caminhos if p.lower().endswith(('.jpg', '.jpeg', '.png'))]
        output_dir = os.path.join(self.dataset_path, 'canny')
        os.makedirs(output_dir, exist_ok=True)

        for img_path in caminhos:
            img = cv2.imread(img_path)
            if img is None:
                continue

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 100, 200)

            nome = os.path.relpath(img_path, os.path.join(self.dataset_path, 'images'))
            out_path = os.path.join(output_dir, nome)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            cv2.imwrite(out_path, edges)

        print(f"[INFO] Todas as imagens salvas em: {output_dir}")
    
    def draw_canny_lines(self):
        print(f"\nAplicando filtro de Canny com linhas: {self.dataset_path}")
        caminhos = glob.glob(os.path.join(self.dataset_path, 'images', '**', '*.*'), recursive=True)
        caminhos = [p for p in caminhos if p.lower().endswith(('.jpg', '.jpeg', '.png'))]
        output_dir = os.path.join(self.dataset_path, 'canny_lines')
        os.makedirs(output_dir, exist_ok=True)

        for img_path in caminhos:
            img = cv2.imread(img_path)
            if img is None:
                continue
        
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 100, 200)

            lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 150, None, 0, 0)
            if lines is not None:
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    cv2.line(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

            nome = os.path.relpath(img_path, os.path.join(self.dataset_path, 'images'))
            out_path = os.path.join(output_dir, nome)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            cv2.imwrite(out_path, img)
        print(f"[OK] Todas as imagens salvas em: {output_dir}")

    def apply_laplacian(self):
        print(f"\nAplicando filtro de laplacian em: {self.dataset_path}")
        caminhos = glob.glob(os.path.join(self.dataset_path, 'images', '**', '*.*'), recursive=True)
        caminhos = [p for p in caminhos if p.lower().endswith(('.jpg', '.jpeg', '.png'))]
        output_dir = os.path.join(self.dataset_path, 'laplacian')
        os.makedirs(output_dir, exist_ok=True)

        for img_path in caminhos:
            img = cv2.imread(img_path)
            if img is None:
                continue
        
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            laplacian = cv2.convertScaleAbs(laplacian)

            nome = os.path.relpath(img_path, os.path.join(self.dataset_path, 'images'))
            out_path = os.path.join(output_dir, nome)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            cv2.imwrite(out_path, laplacian)
        print(f"[OK] Todas as imagens salvas em: {output_dir}")

    def apply_kernel(self, kernel):
        print(f"\nAplicando filtro de kernel em: {self.dataset_path}")
        caminhos = glob.glob(os.path.join(self.dataset_path, 'images', '**', '*.*'), recursive=True)
        caminhos = [p for p in caminhos if p.lower().endswith(('.jpg', '.jpeg', '.png'))]
        output_dir = os.path.join(self.dataset_path, 'kernel')
        os.makedirs(output_dir, exist_ok=True)

        for img_path in caminhos:
            img = cv2.imread(img_path)
            if img is None:
                continue
        
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            filtered = cv2.filter2D(gray, -1, kernel)
            filtered = cv2.normalize(filtered, None, 0, 255, cv2.NORM_MINMAX)

            nome = os.path.relpath(img_path, os.path.join(self.dataset_path, 'images'))
            out_path = os.path.join(output_dir, nome)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            cv2.imwrite(out_path, filtered)
        print(f"[OK] Todas as imagens salvas em: {output_dir}")

    def apply_contrast(self):
        print(f"\nAplicando filtro de contraste em: {self.dataset_path}")
        caminhos = glob.glob(os.path.join(self.dataset_path, 'images', '**', '*.*'), recursive=True)
        caminhos = [p for p in caminhos if p.lower().endswith(('.jpg', '.jpeg', '.png'))]
        output_dir = os.path.join(self.dataset_path, 'contraste')
        os.makedirs(output_dir, exist_ok=True)

        for img_path in caminhos:
            img = cv2.imread(img_path)
            if img is None:
                continue
        
            lab= cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            l_channel, a, b = cv2.split(lab)

            clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8,8))
            cl = clahe.apply(l_channel)

            a = cv2.addWeighted(a, 1.1, np.full_like(a, 128), -0.1, 0)
            b = cv2.addWeighted(b, 1.1, np.full_like(b, 128), -0.1, 0)

            limg = cv2.merge((cl,a,b))
            enhanced_img = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

            nome = os.path.relpath(img_path, os.path.join(self.dataset_path, 'images'))
            out_path = os.path.join(output_dir, nome)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            cv2.imwrite(out_path, enhanced_img)
        print(f"[OK] Todas as imagens salvas em: {output_dir}")

    def remove_labels_id(self):
        resposta = input("Digite os IDs das classes que irão ser remover, separados por espaço (ex: 0 1 2)").strip()
        if not resposta:
            print("Nenhuma classe informada para remoção")
            return
        
        try:
            classes_to_remove = [int(x.strip()) for x in resposta.split()]
        except Exception as e:
            print("Entrada inválida. Use números separados por espaço.")
            return

        print(f"\nRemovendo labels das classes {classes_to_remove} de {self.dataset_path}")
        labels = os.path.join(self.dataset_path, 'labels')
        images = os.path.join(self.dataset_path, 'images')

        if not os.path.isdir(labels):
            print(f"Pasta 'labels' não encontrada em {self.dataset_path}")
            return
        
        arquivos_modificados = 0
        arquivos_removidos = 0

        for paths, _, files in os.walk(labels):
            for filename in files:
                if filename.endswith('.txt'):
                    label_path = os.path.join(paths, filename)

                    with open(label_path, 'r') as f:
                        index = f.readlines()
                    
                    new_index = []
                    for i in index: 
                        parts = i.strip().split()
                        if not parts:
                            continue
                        if int(parts[0]) not in classes_to_remove:
                            new_index.append(i if i.endswith('\n') else i + '\n')

                    if not new_index:
                        os.remove(label_path)
                        split_type = os.path.relpath(paths, labels).split(os.sep)[0]
                        img_name = os.path.splitext(filename)[0]
                        ext = ['.jpg', '.jpeg', '.png']
                        
                        img_path = None
                        for e in ext:
                            path = os.path.join(images, split_type, img_name + e)
                            if os.path.exists(path):
                                img_path = path
                                break

                        if img_path and os.path.exists(img_path):
                            os.remove(img_path)
                        arquivos_removidos += 1
                    else:
                        with open(label_path, 'w') as f:
                            f.writelines(new_index)
                        arquivos_modificados += 1
        print("Labels removidas com sucesso")

    def class_changes(self):
        print(f"\nAlterando os IDs da classe nas labels em: {self.dataset_path}")

        classe_atual = input("Digite o ID da classe que deseja alterar: ").strip()
        classe_nova = input("Digite o novo ID da classe que substituirá a classe: ").strip()
        
        if not classe_atual.isdigit() or not classe_nova.isdigit():
            print("IDs de classe devem ser números inteiros")
            return
        
        labels_dir = os.path.join(self.dataset_path, 'labels')
        if not os.path.isdir(labels_dir):
            print(f"Pasta de labels não encontrada: {labels_dir}")
            return
        
        arquivos_modificados = 0
        for path, _, files in os.walk(labels_dir):
            for file in files:
                if not file.endswith('.txt'):
                    continue

                file_path = os.path.join(path, file)
                with open(file_path, 'r') as f:
                    index = f.readlines()

                new_index = []
                modified = False
                for i in index: 
                    parts = i.strip().split()
                    if parts and parts[0] == classe_atual:
                        parts[0] = classe_nova
                        modified = True
                    new_index.append(' '.join(parts) + '\n')
            
                if modified:
                    with open(file_path, 'w') as f:
                        f.writelines(new_index)
                        print(f"Alterado: {file_path}")
                        arquivos_modificados += 1

        if arquivos_modificados == 0:
            print("Nenhum arquivo modificado")
        else:
            print(f"[OK] {arquivos_modificados} arquivos modificados")

    def review_generation(self):
        print(f"\nIniciando a criação dos relatórios: {self.dataset_path}")
        output_dir = os.path.join(self.dataset_path, "Relatorios")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"Relatorio_por_pasta_{os.path.basename(self.dataset_path)}.txt")

        folders = ['train', 'val', 'test']
        base_path = os.path.join(self.dataset_path, 'images')

        result = []

        for folder in folders:
            counter = defaultdict(int)
            complete_folder = os.path.join(base_path, folder)
            if not os.path.exists(complete_folder):
                continue

            for file in os.listdir(complete_folder):
                if not file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    continue
                id_dataset = file.split('_')[0]
                counter[id_dataset] += 1
            
            result.append(f"Pasta: {folder}")
            for id_dataset, qtd in sorted(counter.items()):
                result.append(f" - Dataset ID {id_dataset}: {qtd} imagens")
            result.append("")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(result))
        
        print(f"Relatório de contagem por pasta salvo em {output_path}")

    def review_generation_4k(self, resolution="3840x2160"):    
        print(f"\nIniciando a criação dos relatórios para 4K: {self.dataset_path}")
        output_dir = os.path.join(self.dataset_path, "Relatorios")
        os.makedirs(output_dir, exist_ok=True)

        base_name = os.path.basename(self.dataset_path)
        folder_resolution = os.path.join(self.dataset_path, f"resolucoes_organizadas/{resolution}/images")

        if not os.path.exists(folder_resolution):
            print(f"Pasta {folder_resolution} não existe")
            return

        def map_datasets_names(root_path, dataset_folder_name):
            def extrair_ids(nome):
                return set(re.findall(r'(\d+)', nome))
            
            ids_referencia = extrair_ids(dataset_folder_name)
            id_to_name = {}
            print(f'IDs da pasta de referência: {ids_referencia}')
            print(f'Verificando pastas em {root_path}')
            
            for folder in os.listdir(root_path):
                full_path = os.path.join(root_path, folder)
                if not os.path.isdir(full_path):
                    continue

                ids_pasta = extrair_ids(folder)
                if ids_referencia & ids_pasta:
                    parts = folder.split('_')
                    datasets_ids = [i for i in parts if i.isdigit()]
                    if datasets_ids:
                        dataset_id = datasets_ids[-1]
                        name = folder.replace(f"_{dataset_id}", "").split("Dataset_VoxSmartCargo_-_")[-1]
                        print(f"Incluindo {folder} no mapeamento. ID principal: {dataset_id} → nome: '{name}'")
                        id_to_name[dataset_id] = name
                    else:
                        print(f"Incluindo {folder} mas ID não foi extraído normalmente")
                else:
                    print(f"Ignorando {folder} (sem IDs em comum com {dataset_folder_name})")

            return id_to_name

        id_to_name = map_datasets_names(root_path = '.', dataset_folder_name=base_name)

        images_id = defaultdict(lambda: defaultdict(list))

        for split in ["train", "val", "test"]:
            split_path = os.path.join(folder_resolution, split)
            if not os.path.exists(split_path):
                print(f"Pasta {split_path} não encontrada, ignorando...")
                continue

            for file in os.listdir(split_path):
                if not file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    continue
                id_dataset = file.split('_')[0]
                images_id[id_dataset][split].append(file)

        consolidado_lines = ["Consolidado: "]
        for id_dataset in sorted(images_id.keys()):
            total = sum(len(images_id[id_dataset][split]) for split in ["train", "val", "test"])
            dataset_name = id_to_name.get(id_dataset, f"ID {id_dataset}")
            consolidado_lines.append(f" - {dataset_name}: {total} imagens")
        consolidado_lines.append("")
            
        summary_lines = consolidado_lines.copy()
        for split in ["train", "val", "test"]:
            summary_lines.append(f"Pasta: {split}")
            ids_in_split = {k: v[split] for k, v in images_id.items() if split in v}      
            for id_dataset in sorted(ids_in_split.keys()):
                count = len(images_id[id_dataset][split])
                nome_dataset = id_to_name.get(id_dataset, f"ID {id_dataset}")
                summary_lines.append(f" - {nome_dataset}: {count} imagens")
            summary_lines.append("")

        summary_path = os.path.join(output_dir, f"Relatorio_{resolution}_{base_name}.txt")
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(summary_lines))
        print(f"Relatório de contagem por pasta salvo em {summary_path}")

        detail_lines = []        
        for id_dataset in sorted(images_id.keys()):
            detail_lines.append(f"\n===Dataset ID {id_dataset}=== ")
            for split in ["train", "val", "test"]:
                imgs = images_id[id_dataset][split]
                if imgs:
                    detail_lines.append(f"\n [{split.upper()}] - {len(imgs)} imagens:")
                    for name in sorted(imgs):
                        detail_lines.append(f" {name}")
        detail_lines.append("")

        detail_path = os.path.join(output_dir, f"Relatorio_com_imagens_{resolution}_{base_name}.txt")
        with open(detail_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(detail_lines))
        
        print(f"Relatório de contagem por pasta salvo em {detail_path}")

    def run_menu(self):
        while True:
            print("\nEscolha um filtro para aplicar:")
            print("1) Listar resoluções")
            print("2) Converter para preto e branco (grayscale)")
            print("3) Converter treshold (treshold)")
            print("4) Converter treshold invertido")
            print("5) Organizar imagens por resolução")
            print("6) Destacar bordas do objeto com Canny")
            print("7) Destacar bordas do objeto com Laplaciano")
            print("8) Destacar bordas do objeto com Kernel")
            print("9) Destacar bordas do objeto com Canny e aplicar linhas")
            print("10) Aplicar contraste")
            print("11) Remover labels do diretório")
            print("12) Mudar as classes das labels do diretório")
            print("13) Gerar o relatório de contagem de imagens por pasta")
            print("14) Gerar o relatório de contagem de imagens 4K")
            print("0) Voltar")

            choice = input("Opção: ").strip()

            if choice == '1':
                self.list_resolutions()
            elif choice == '2':
                self.apply_grayscale()
            elif choice == '3':
                self.apply_threshold()
            elif choice == '4':
                self.apply_threshold_inv()
            elif choice == '5':
                self.resolution_organizer()
            elif choice == '6':
                self.apply_canny()
            elif choice == '7':
                self.apply_laplacian()
            elif choice == '8':
                kernel = np.array([[-1, -1, -1], [-1, 8, -1],[-1, -1, -1]])
                self.apply_kernel(kernel)
            elif choice == '9':
                self.draw_canny_lines()
            elif choice == '10':
                self.apply_contrast()
            elif choice == '11':
                self.remove_labels_id()
            elif choice == '12':
                self.class_changes()
            elif choice == '13':
                self.review_generation()
            elif choice == '14':
                self.review_generation_4k()
            elif choice == '0':
                break
            else:
                print("Opção inválida.")
