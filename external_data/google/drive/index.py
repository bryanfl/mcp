from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
import os
import io
import PyPDF2
import pandas as pd
import google.auth

current_directory = os.path.dirname(os.path.abspath(__file__))
# Define los alcances (scopes) que necesitas
SCOPES = ['https://www.googleapis.com/auth/drive']
# Especifica la ruta exacta a tu archivo JSON de Service Account
SERVICE_ACCOUNT_FILE = os.path.join(current_directory, 'service_drive.json')

# Crear las credenciales usando el archivo de la Service Account
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# Construir el cliente de la API de Drive
service = build('drive', 'v3', credentials=credentials)

def get_files():
    try:
        # Crear las credenciales usando el archivo de la Service Account
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)

        # Construir el cliente de la API de Drive
        service = build('drive', 'v3', credentials=credentials)

        # Ejecutar una solicitud de prueba: listar los primeros 10 archivos
        results = service.files().list(
            pageSize=10,
            fields="nextPageToken, files(id, name)"
        ).execute()
        items = results.get('files', [])

        if not items:
            return None
        else:
            print('Archivos:')
            print(items)

    except HttpError as error:
        print(f'Se produjo un error: {error}')

def read_file(field_id, extension):
    try:

        if (extension == 'pdf'):
            request = service.files().get_media(fileId=field_id)
            file_stream = io.BytesIO()
            downloader = MediaIoBaseDownload(file_stream, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print(f"Descarga {int(status.progress() * 100)}% completada.")

            # 2. Regresar al inicio del flujo en memoria
            file_stream.seek(0)

            # 3. Leer el PDF y extraer texto
            pdf_reader = PyPDF2.PdfReader(file_stream)
            extracted_text = ""
            
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:  # Verificar que se extrajo texto
                    extracted_text += page_text
            
            return extracted_text
        
        elif (extension == 'xlsx'):
            request = service.files().get_media(fileId=field_id)
            file_stream = io.BytesIO()
            downloader = MediaIoBaseDownload(file_stream, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print(f"Descarga {int(status.progress() * 100)}% completada.")

            # Leer el XLSX directamente desde la memoria
            df = pd.read_excel(file_stream, engine='openpyxl')

            return df.to_dict(orient='records')
        return None


    except HttpError as error:
        return f'Se produjo un error: {error}'

def create_and_upload_excel(file_path, drive_name):
    """Uploads a file to Google Drive using a service account."""

    df = pd.DataFrame(data)
    excel_file_name = f"{file_path}"
    df.to_excel(excel_file_name, index=False)
    
    # File metadata
    file_metadata = {'name': drive_name}
    # if parent_folder_id:
    file_metadata['parents'] = ["1x0Bz_zydTtIH3jv09CPkzGvvnwAawb_r"]
    print(file_metadata)
    # Media upload
    media = MediaFileUpload(file_path, resumable=True)

    # Execute the request
    file = service.files().create(body=file_metadata,
                                        media_body=media,
                                        fields='id').execute()
    print(f'File uploaded with ID: {file.get("id")}')
    return file.get('id')

# Example usage
data = [
    ["Name", "Department", "Salary"],
    ["Alice", "Engineering", 75000],
    ["Bob", "Marketing", 65000],
    ["Charlie", "Engineering", 80000]
]


if __name__ == '__main__':
    create_and_upload_excel("My_Report.xlsx", "Employee_Data.xlsx")
    # get_files()
    # print(read_file('1-0T0nxBXefPD3E6dwJ6LASgjh4ksK3q5', 'xlsx'))