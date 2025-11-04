"""
Data Aggregation and Storage Module
==================================

ETL pipeline for:
1. Normalizing data from multiple sources
2. Storing to PostgreSQL and S3
3. Deduplication and validation
4. Timestamp standardization (UTC)
"""

from datetime import datetime
from typing import Dict, List, Optional
import json
import warnings

import pandas as pd
import numpy as np
import boto3
from botocore.exceptions import ClientError

from config import config

warnings.filterwarnings('ignore')


class DataAggregator:
    """Aggregate and normalize data from multiple sources"""
    
    def __init__(self):
        self.required_columns = ['id', 'text', 'timestamp', 'source']
    
    def normalize_dataframe(self, df: pd.DataFrame, source_name: str) -> pd.DataFrame:
        """
        Normalize DataFrame to standard schema
        
        Standard schema:
        - id: unique identifier
        - text: main content text
        - timestamp: UTC datetime
        - source: data source name
        - author: optional author/handle
        - entities: optional list of mentioned entities
        - metrics: optional engagement metrics (likes, retweets, etc.)
        
        Args:
            df: Raw DataFrame from data source
            source_name: Name of source for tracking
        
        Returns:
            Normalized DataFrame
        """
        if df.empty:
            return pd.DataFrame(columns=self.required_columns)
        
        normalized = df.copy()
        
        # Ensure required columns exist
        if 'source' not in normalized.columns:
            normalized['source'] = source_name
        
        if 'id' not in normalized.columns:
            # Generate IDs if missing
            normalized['id'] = [f"{source_name}_{i}" for i in range(len(normalized))]
        
        if 'timestamp' not in normalized.columns:
            # Use current time if missing
            normalized['timestamp'] = datetime.utcnow()
        
        # Standardize timestamp to UTC
        normalized['timestamp'] = pd.to_datetime(normalized['timestamp'], utc=True)
        
        # Extract text content (may be in different columns)
        if 'text' not in normalized.columns:
            if 'content' in normalized.columns:
                normalized['text'] = normalized['content']
            elif 'body' in normalized.columns:
                normalized['text'] = normalized['body']
            elif 'message' in normalized.columns:
                normalized['text'] = normalized['message']
            else:
                normalized['text'] = ''
        
        # Consolidate metrics into JSON
        metric_columns = ['likes', 'retweets', 'shares', 'comments', 'reposts']
        if any(col in normalized.columns for col in metric_columns):
            normalized['metrics'] = normalized.apply(
                lambda row: {
                    col: row[col] for col in metric_columns 
                    if col in row and pd.notna(row[col])
                },
                axis=1
            )
        
        # Remove duplicates based on ID
        normalized = normalized.drop_duplicates(subset=['id'], keep='first')
        
        print(f"✓ Normalized {len(normalized)} records from {source_name}")
        
        return normalized
    
    def merge_dataframes(self, dataframes: List[pd.DataFrame]) -> pd.DataFrame:
        """
        Merge multiple DataFrames with deduplication
        
        Args:
            dataframes: List of DataFrames to merge
        
        Returns:
            Merged and deduplicated DataFrame
        """
        if not dataframes:
            return pd.DataFrame()
        
        # Filter out empty DataFrames
        dataframes = [df for df in dataframes if not df.empty]
        
        if not dataframes:
            return pd.DataFrame()
        
        # Concatenate
        merged = pd.concat(dataframes, ignore_index=True, sort=False)
        
        # Remove duplicates (by ID or text+timestamp)
        if 'id' in merged.columns:
            merged = merged.drop_duplicates(subset=['id'], keep='first')
        elif 'text' in merged.columns and 'timestamp' in merged.columns:
            merged = merged.drop_duplicates(subset=['text', 'timestamp'], keep='first')
        
        # Sort by timestamp (most recent first)
        if 'timestamp' in merged.columns:
            merged = merged.sort_values('timestamp', ascending=False)
        
        print(f"✓ Merged {len(merged)} unique records from {len(dataframes)} sources")
        
        return merged
    
    def filter_by_date_range(
        self,
        df: pd.DataFrame,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Filter DataFrame by date range
        
        Args:
            df: DataFrame with 'timestamp' column
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
        
        Returns:
            Filtered DataFrame
        """
        if 'timestamp' not in df.columns:
            print("⚠️  No timestamp column for date filtering")
            return df
        
        filtered = df.copy()
        
        if start_date:
            filtered = filtered[filtered['timestamp'] >= start_date]
        
        if end_date:
            filtered = filtered[filtered['timestamp'] <= end_date]
        
        print(f"✓ Filtered to {len(filtered)} records in date range")
        
        return filtered
    
    def validate_data_quality(self, df: pd.DataFrame) -> Dict:
        """
        Validate data quality and generate report
        
        Args:
            df: DataFrame to validate
        
        Returns:
            Dict with validation metrics
        """
        if df.empty:
            return {
                'total_records': 0,
                'valid_records': 0,
                'quality_score': 0.0,
                'issues': ['DataFrame is empty']
            }
        
        issues = []
        total = len(df)
        
        # Check required columns
        missing_cols = [col for col in self.required_columns if col not in df.columns]
        if missing_cols:
            issues.append(f"Missing required columns: {missing_cols}")
        
        # Check for null text
        if 'text' in df.columns:
            null_text = df['text'].isna().sum()
            if null_text > 0:
                issues.append(f"{null_text} records with null text")
        
        # Check text length
        if 'text' in df.columns:
            empty_text = (df['text'].str.len() < 5).sum()
            if empty_text > total * 0.1:  # More than 10% very short
                issues.append(f"{empty_text} records with very short text (<5 chars)")
        
        # Check timestamp validity
        if 'timestamp' in df.columns:
            future_dates = (df['timestamp'] > datetime.utcnow()).sum()
            if future_dates > 0:
                issues.append(f"{future_dates} records with future timestamps")
        
        # Check for duplicates
        if 'id' in df.columns:
            duplicates = df['id'].duplicated().sum()
            if duplicates > 0:
                issues.append(f"{duplicates} duplicate IDs found")
        
        # Calculate quality score
        penalty = len(issues) * 0.1
        quality_score = max(0.0, 1.0 - penalty)
        
        valid_records = total
        if 'text' in df.columns:
            valid_records = (~df['text'].isna()).sum()
        
        return {
            'total_records': total,
            'valid_records': valid_records,
            'quality_score': round(quality_score, 2),
            'issues': issues,
            'completeness': round(valid_records / total * 100, 1) if total > 0 else 0
        }


class S3Storage:
    """Store data to Amazon S3"""
    
    def __init__(self):
        self.bucket_name = config.S3_BUCKET_NAME
        self.s3_client = None
        
        if config.AWS_ACCESS_KEY_ID and config.AWS_ACCESS_KEY_ID != 'your_aws_access_key':
            try:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
                    region_name=config.AWS_REGION
                )
            except Exception as e:
                print(f"⚠️  S3 client initialization failed: {str(e)}")
    
    def upload_dataframe(
        self,
        df: pd.DataFrame,
        key: str,
        format: str = 'parquet'
    ) -> bool:
        """
        Upload DataFrame to S3
        
        Args:
            df: DataFrame to upload
            key: S3 object key (path)
            format: File format ('parquet', 'csv', 'json')
        
        Returns:
            True if successful, False otherwise
        """
        if self.s3_client is None:
            print("⚠️  S3 client not initialized")
            return False
        
        if df.empty:
            print("⚠️  Cannot upload empty DataFrame")
            return False
        
        try:
            # Convert DataFrame to bytes
            if format == 'parquet':
                buffer = df.to_parquet(index=False)
                content_type = 'application/octet-stream'
            elif format == 'csv':
                buffer = df.to_csv(index=False).encode('utf-8')
                content_type = 'text/csv'
            elif format == 'json':
                buffer = df.to_json(orient='records').encode('utf-8')
                content_type = 'application/json'
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=buffer,
                ContentType=content_type
            )
            
            print(f"✓ Uploaded {len(df)} records to s3://{self.bucket_name}/{key}")
            return True
            
        except ClientError as e:
            print(f"❌ S3 upload failed: {e}")
            return False
        except Exception as e:
            print(f"❌ Error uploading to S3: {str(e)}")
            return False
    
    def download_dataframe(
        self,
        key: str,
        format: str = 'parquet'
    ) -> pd.DataFrame:
        """
        Download DataFrame from S3
        
        Args:
            key: S3 object key
            format: File format ('parquet', 'csv', 'json')
        
        Returns:
            DataFrame
        """
        if self.s3_client is None:
            print("⚠️  S3 client not initialized")
            return pd.DataFrame()
        
        try:
            # Download from S3
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )
            
            body = response['Body'].read()
            
            # Parse based on format
            if format == 'parquet':
                df = pd.read_parquet(body)
            elif format == 'csv':
                df = pd.read_csv(body)
            elif format == 'json':
                df = pd.read_json(body, orient='records')
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            print(f"✓ Downloaded {len(df)} records from s3://{self.bucket_name}/{key}")
            return df
            
        except ClientError as e:
            print(f"❌ S3 download failed: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"❌ Error downloading from S3: {str(e)}")
            return pd.DataFrame()
    
    def list_objects(self, prefix: str = '') -> List[str]:
        """
        List objects in S3 bucket
        
        Args:
            prefix: Key prefix filter
        
        Returns:
            List of object keys
        """
        if self.s3_client is None:
            print("⚠️  S3 client not initialized")
            return []
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            objects = [obj['Key'] for obj in response.get('Contents', [])]
            print(f"✓ Found {len(objects)} objects with prefix '{prefix}'")
            return objects
            
        except ClientError as e:
            print(f"❌ S3 list failed: {e}")
            return []


def create_daily_batch(
    date: datetime,
    include_historical: bool = False,
    include_realtime: bool = True
) -> Dict:
    """
    Create daily data batch for processing
    
    Args:
        date: Date to process
        include_historical: Include historical Trump tweets
        include_realtime: Include real-time data
    
    Returns:
        Dict with batch metadata and data path
    """
    from data.ingestion import aggregate_all_sources
    
    # Fetch data
    data = aggregate_all_sources(
        include_historical=include_historical,
        include_realtime=include_realtime,
        include_government=False,
        include_family=False
    )
    
    if data.empty:
        return {
            'date': date.date().isoformat(),
            'status': 'no_data',
            'record_count': 0
        }
    
    # Aggregate
    aggregator = DataAggregator()
    normalized = aggregator.normalize_dataframe(data, 'batch')
    
    # Filter to date
    date_filtered = aggregator.filter_by_date_range(
        normalized,
        start_date=date,
        end_date=date + pd.Timedelta(days=1)
    )
    
    # Validate
    quality = aggregator.validate_data_quality(date_filtered)
    
    # Store to S3 (if configured)
    s3 = S3Storage()
    s3_key = f"daily_batches/{date.date().isoformat()}/data.parquet"
    upload_success = s3.upload_dataframe(date_filtered, s3_key)
    
    return {
        'date': date.date().isoformat(),
        'status': 'success' if upload_success else 'local_only',
        'record_count': len(date_filtered),
        'quality_score': quality['quality_score'],
        's3_path': f"s3://{config.S3_BUCKET_NAME}/{s3_key}" if upload_success else None,
        'validation': quality
    }


if __name__ == '__main__':
    # Test aggregation
    print("\n🧪 Testing Data Aggregator\n")
    
    # Create sample data
    sample_data1 = pd.DataFrame({
        'id': ['tweet1', 'tweet2', 'tweet3'],
        'text': ['Sample tweet 1', 'Sample tweet 2', 'Sample tweet 3'],
        'timestamp': pd.date_range('2024-01-01', periods=3, freq='H'),
        'source': ['Twitter', 'Twitter', 'Twitter'],
        'likes': [100, 200, 150]
    })
    
    sample_data2 = pd.DataFrame({
        'id': ['ts1', 'ts2'],
        'content': ['Truth Social post 1', 'Truth Social post 2'],
        'timestamp': pd.date_range('2024-01-01 12:00', periods=2, freq='H'),
        'source': ['Truth Social', 'Truth Social']
    })
    
    # Test normalization
    aggregator = DataAggregator()
    
    norm1 = aggregator.normalize_dataframe(sample_data1, 'Twitter')
    print(f"Normalized Twitter data: {len(norm1)} records")
    
    norm2 = aggregator.normalize_dataframe(sample_data2, 'Truth Social')
    print(f"Normalized Truth Social data: {len(norm2)} records")
    
    # Test merging
    merged = aggregator.merge_dataframes([norm1, norm2])
    print(f"\nMerged data: {len(merged)} total records")
    
    # Test validation
    quality = aggregator.validate_data_quality(merged)
    print(f"\nData Quality Report:")
    print(f"  Total: {quality['total_records']}")
    print(f"  Valid: {quality['valid_records']}")
    print(f"  Quality Score: {quality['quality_score']}")
    print(f"  Completeness: {quality['completeness']}%")
    if quality['issues']:
        print(f"  Issues: {quality['issues']}")
    
    # Test S3 (will skip if not configured)
    print("\nTesting S3 storage...")
    s3 = S3Storage()
    if s3.s3_client:
        test_key = 'test/aggregator_test.parquet'
        success = s3.upload_dataframe(merged, test_key)
        if success:
            downloaded = s3.download_dataframe(test_key)
            print(f"  Downloaded {len(downloaded)} records (matches: {len(downloaded) == len(merged)})")
    else:
        print("  S3 not configured - skipping")

