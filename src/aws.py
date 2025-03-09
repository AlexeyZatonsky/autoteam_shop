import asyncio
from aiobotocore.session import get_session
from contextlib import asynccontextmanager
from typing import Optional, Dict, Union, BinaryIO
from fastapi import UploadFile
from .settings.config import settings
import io

s3_access_key = settings.S3_ACCESS_KEY
s3_secret_key = settings.S3_SECRET_KEY
s3_url = settings.S3_URL
s3_bucket_name = settings.S3_BUCKET_NAME

class S3Client:
    def __init__(
        self,
        access_key: str,
        secret_key: str,
        endpoint_url: str,
        bucket_name: str
    ):
        self.config = {
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "endpoint_url": endpoint_url,
            "region_name": "ru-msk-1"
        }
        
        self.bucket_name = bucket_name
        self.session = get_session()

    @asynccontextmanager    
    async def get_client(self):
        async with self.session.create_client("s3", **self.config) as client:
            yield client

    async def upload_file(
        self,
        file: Union[BinaryIO, io.BytesIO],
        object_name: str,
        content_type: str = "image/jpeg"
    ) -> Optional[str]:
        """Загружает файл в S3 и возвращает его URL"""
        async with self.get_client() as client:
            try:
                # Получаем содержимое файла
                if hasattr(file, 'read'):
                    body = file.read()
                    if hasattr(file, 'seek'):
                        file.seek(0)  # Возвращаем указатель в начало
                else:
                    body = file  # Если file уже является bytes
                
                # Загружаем файл в S3
                await client.put_object(
                    Bucket=self.bucket_name,
                    Key=object_name,
                    Body=body,
                    ContentType=content_type
                )

                # Возвращаем полный URL
                url = f"{self.config['endpoint_url']}/{self.bucket_name}/{object_name}"
                return url
            except Exception as e:
                print(f"Ошибка при загрузке файла: {e}")
                return None

    async def delete_file(self, object_name: str) -> bool:
        """Удаляет файл из S3"""
        async with self.get_client() as client:
            try:
                await client.delete_object(
                    Bucket=self.bucket_name,
                    Key=object_name
                )
                return True
            except Exception as e:
                print(f"Ошибка при удалении файла: {e}")
                return False

    async def get_file(self, object_name: str) -> Optional[bytes]:
        """Получает файл из S3"""
        async with self.get_client() as client:
            try:
                response = await client.get_object(
                    Bucket=self.bucket_name,
                    Key=object_name
                )
                async with response['Body'] as stream:
                    return await stream.read()
            except Exception as e:
                print(f"Ошибка при получении файла: {e}")
                return None

s3_client = S3Client(
    access_key=s3_access_key,
    secret_key=s3_secret_key,
    endpoint_url=s3_url,
    bucket_name=s3_bucket_name
)