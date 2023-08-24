import sys
import os
import logging
import boto3
import requests
import csv


logging.basicConfig(format="%(levelname)s [%(asctime)s]: %(filename)s::%(funcName)s %(message)s")
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Variáveis Globais
bucket_name = os.environ['BUCKET_NAME']
list_backup = os.environ['LIST_BACKUP']
list_processed = os.environ['LIST_PROCESSED']
list_failed = os.environ['LIST_FAILED']
list_exist = os.environ['LIST_EXIST']

# Conexão com AWS S3
try:
    s3 = boto3.client('s3')
    logger.info("Sucesso: Conectado ao S3")
except Exception as e:
    logger.error(f"Erro na conexão com o S3: {e}")
    sys.exit()
    
# Download da LISTA
try:
    s3.download_file(BUCKET_NAME, f'list/{LIST_BACKUP}', f'./{LIST_BACKUP}')
    logger.info("Sucesso: Download da LISTA")
except Exception as e:
    logger.error(f"Erro ao fazer download da lista: {e}")
    sys.exit()

    # Tratamento dos dados do arquivo de LISTA e download das imagens
try:
    # Variáveis
    URL_BASE = "https://url-base.com/"

    # Verifica a existência do arquivo de LISTA
    if os.path.exists(f'./{LIST_BACKUP}'):
        logger.info("Arquivo de lista existe!")

    # Realiza a leitura da LISTA
    with open(f'./{LIST_BACKUP}', "r") as imgs:
        img_exist = []
        not_processed = []
        processed = []
        img_file = list(csv.reader(imgs, delimiter=","))

        # Realiza a indexação dos dados
        for row in img_file:
            URI_IMG = str(row[1])
            logger.info("Sucesso: indexação dos dados")

            # Tratamento do caminho da imagem
            dir_main, file_name = os.path.split(URI_IMG)
            dir_primary, dir_secundary = os.path.split(dir_main)
            dir_secundary = os.path.join(dir_secundary)
            dir_primary = dir_primary.lstrip('/')

            # Variaveis
            IMG_PATH = f'/tmp/{file_name}'
            IMG_PATH_S3 = f'{dir_primary}/{dir_secundary}/{file_name}'

            # Verifica se o arquivo já existe no Bucket s3
            try:
                response = s3.head_object(Bucket=BUCKET_NAME, Key=IMG_PATH_S3)
            # Se o arquivo não existir:
            except Exception as e:

                # Realiza o download da imagem
                response = requests.get(str(URL_BASE) + str(URI_IMG))
                logger.info(f'Download da imagem {URI_IMG}-{response}')

                # Cria o arquivo e realiza o upload no s3
                if response.status_code == 200:
                    # Cria o arquivo
                    with open(IMG_PATH, 'wb') as f:

                        # Salva o conteúdo no arquivo criado
                        f.write(response.content)

                        # Realiza o upload da imagem no s3
                        s3.upload_file(os.path.join(IMG_PATH),BUCKET_NAME, os.path.join(IMG_PATH_S3))
                        logger.info("Sucesso: Upload da imagem S3")
                        
                        # Remove a imagem do diretório temporário
                        os.remove(IMG_PATH)
                        logger.info("Sucesso: Remoção do arquivo temporário")
                        
                    # Usado para remover linha do arquivo LIST_BACKUP
                    processed.append(row)

                    # Cria um arquivo de log com as imagens processadas
                    if LIST_PROCESSED:
                        with open(f'./log/{LIST_PROCESSED}', 'a') as f:
                            f.write(f'{URI_IMG}\n')  
                        logger.info(f"Sucesso: Item {URI_IMG} adicionado a LIST_PROCESSED.")                          

                    # Remove as linhas processadas do arquivo de LISTA 
                    img_file = [x for x in img_file if x not in processed]
                    logger.info("Sucesso: item removido da lista LIST_BACKUP")

                    with open(f'./{LIST_BACKUP}', 'w', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerows(img_file)
                    logger.info("Sucesso: arquivo LIST_BACKUP atualizado")
                    
                    # Realiza o upload do arquivo de lista atualizado para o s3
                    s3.upload_file(f'./{LIST_BACKUP}',BUCKET_NAME, f'list/{LIST_BACKUP}')
                    logger.info("Sucesso: LIST_BACKUP enviada para o S3")   
                    
                    # Realiza o upload da lista das imagens processados para o S3
                    s3.upload_file(f'./log/{LIST_PROCESSED}', BUCKET_NAME, f'list/{LIST_PROCESSED}')
                    logger.info("Sucesso: LIST_PROCESSED enviada para o S3")

                else:

                    # Usado para remover linha do arquivo LIST_BACKUP
                    not_processed.append(row)

                    # Cria um arquivo de LISTA com as imagens não processadas que tiveram erro
                    if LIST_FAILED:
                        with open(f'./log/{LIST_FAILED}', 'a') as f:
                            f.write(f'{URI_IMG}-{response}\n')  
                        logger.info(f"Sucesso: Item {URI_IMG} adicionado a LIST_FAILED.")     

                        # Remove as linhas não processadas do arquivo Lista original
                        img_file = [x for x in img_file if x not in not_processed]
                        logger.info("Sucesso: Item removido da lista LIST_BACKUP")

                        with open(f'./{LIST_BACKUP}', 'w', newline='') as f:
                            writer = csv.writer(f)
                            writer.writerows(img_file)
                        logger.info("Sucesso: arquivo LIST_BACKUP atualizado")  
                        
                        # Realiza o upload do arquivo de lista atualizado para o s3
                        s3.upload_file(f'./{LIST_BACKUP}',BUCKET_NAME, f'list/{LIST_BACKUP}')
                        logger.info("Sucesso: LIST_BACKUP enviada para o S3")
                        # Realiza o upload da lista das imagens que falharam para o s3
                        s3.upload_file(f'./log/{LIST_FAILED}', BUCKET_NAME, f'list/{LIST_FAILED}')
                        logger.info("Sucesso: LIST_FAILED enviada para o S3")   
            else:
                # Usado para remover linha do arquivo LIST_BACKUP
                img_exist.append(row)
                
                # Se o arquivo de imagem já existir no bucket s3
                logger.info(f"Sucesso: Item {URI_IMG} já existe no S3. Pulando upload.")
                with open(f'./log/{LIST_EXIST}', 'a') as log_file:
                    log_file.write(f'{URI_IMG}\n')
                logger.info(f"Sucesso: Item {URI_IMG} adicionado a LIST_EXIST.")
                
                # Remove as linhas não processadas do arquivo Lista original
                img_file = [x for x in img_file if x not in img_exist]
                logger.info("Sucesso: Item removido da lista LIST_BACKUP")
                
                with open(f'./{LIST_BACKUP}', 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerows(img_file)
                logger.info("Sucesso: arquivo LIST_BACKUP atualizado")  
                
                # Realiza o upload do arquivo de lista atualizado para o s3
                s3.upload_file(f'./{LIST_BACKUP}',BUCKET_NAME, f'list/{LIST_BACKUP}')
                logger.info("Sucesso: LIST_BACKUP enviada para o S3")   
                
                # Realiza o upload da lista das imagens que já existiam para o s3
                s3.upload_file(f'./log/{LIST_EXIST}', BUCKET_NAME, f'list/{LIST_EXIST}')
                logger.info("Sucesso: LIST_EXIST enviada para o S3")


except Exception as e:
    logger.error(f"Erro {e}")
    sys.exit()

logger.info("Sucesso: Função Finalizada")



#Step 1 - Importa e processa a leitura do arquivo que contém a lista de imagens armazenadas no bucket S3.
#Step 2 - Exporta as imagens do arquivo de lista de imagens para o bucket S3.
#Step 3 - Verifica se o arquivo de imagem já existe no bucket S3 e, caso exista, pule para a próxima imagem.
#Step 4 - Cria um arquivo com os dados das imagens que tiveram erro durante o processo de importação/exportação.
#Step 5 - Remove os dados das imagens que já foram processadas do arquivo original.
#Step 6 - Cria um arquivo com os dados das imagens que foram processadas com sucesso.

